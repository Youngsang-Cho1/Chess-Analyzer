import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Game, MoveAnalysis, Base
from batch import process_user_games
from player_stats import get_player_stats
from insights import get_player_insights
from llm_reviewer import ChessReviewer
from ml_features import FEATURE_NAMES, iter_user_moves
from train_risk import load_model, predict_proba, train as train_risk_model

import numpy as np

reviewer = ChessReviewer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    print("DB tables verified/created.")
    yield


app = FastAPI(lifespan=lifespan)

# Allow Frontend (Next.js) to access Backend.
# Override via CORS_ORIGINS env var (comma-separated) for non-local deployments.
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Chess Analyzer API"}


@app.post("/analyze/{username}")
def analyze_games(
    username: str,
    background_tasks: BackgroundTasks,
    limit: int = 5,
    opponent: str = None,
):
    background_tasks.add_task(process_user_games, username, limit=limit, opponent=opponent)
    msg = f"Analysis started for {username} ({limit} games)"
    if opponent:
        msg += f" vs {opponent}"
    return {"message": msg + ". Refresh in a few minutes."}


@app.get("/games/{username}")
def get_games(username: str, db: Session = Depends(get_db)):
    games = db.query(Game).filter(
        or_(Game.white_username == username, Game.black_username == username)
    ).all()
    return {"games": games}


@app.get("/game/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    analysis = db.query(MoveAnalysis).filter(
        MoveAnalysis.game_id == game_id
    ).order_by(MoveAnalysis.id).all()
    return {"game": game, "analysis": analysis}


@app.get('/stats/{username}')
def get_stats(username: str):
    stats = get_player_stats(username, limit=50)
    return {"stats": stats}


@app.get('/insights/{username}')
def get_insights(username: str, limit: int = 100):
    data = get_player_insights(username, limit=limit)
    if not data:
        raise HTTPException(status_code=404, detail="No analyzed games for this user")
    return {"insights": data}


@app.get('/moves/{username}/{classification}')
def get_moves(username: str, classification: str, db: Session = Depends(get_db)):
    results = db.query(MoveAnalysis, Game).join(Game, MoveAnalysis.game_id == Game.id).filter(
        or_(Game.white_username == username, Game.black_username == username),
        MoveAnalysis.classification == classification
    ).all()

    res = []
    for move, game in results:
        user_color = "white" if game.white_username == username else "black"
        if move.color == user_color:
            res.append(move)
    return {"moves": res}


@app.post("/risk/train/{username}")
def risk_train(username: str):
    """Kick off (synchronous) training of the per-user risk model."""
    path = train_risk_model(username)
    if not path:
        raise HTTPException(
            status_code=400,
            detail="Not enough data — analyze more games first.",
        )
    bundle = load_model(username)
    return {
        "ok": True,
        "model": bundle["kind"],
        "auc": round(bundle["auc"], 3),
        "samples": bundle["n_samples"],
        "positives": bundle["n_positives"],
    }


@app.get("/risk/{game_id}")
def risk_for_game(game_id: int, db: Session = Depends(get_db)):
    """Per-move risk probability for the user in this game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    moves = (
        db.query(MoveAnalysis)
        .filter(MoveAnalysis.game_id == game_id)
        .order_by(MoveAnalysis.id)
        .all()
    )
    if not moves:
        return {"trained": False, "predictions": []}

    # Decide which side is "the user" — prefer the side that has a trained model.
    candidates = [game.white_username, game.black_username]
    bundle = None
    username = None
    for u in candidates:
        if not u:
            continue
        b = load_model(u)
        if b:
            bundle = b
            username = u
            break

    if not bundle:
        return {
            "trained": False,
            "reason": "No risk model trained for either player. POST /risk/train/{username} first.",
            "predictions": [],
        }

    samples = list(iter_user_moves(game.pgn, username, moves))
    if not samples:
        return {"trained": True, "auc": bundle["auc"], "predictions": []}

    X = np.array(
        [[s["features"][n] for n in FEATURE_NAMES] for s in samples], dtype=float
    )
    probs = predict_proba(bundle, X)

    preds = [
        {
            "move_id": s["move_id"],
            "move_number": s["move_number"],
            "color": s["color"],
            "risk": float(round(p, 3)),
            "classification": s["classification"],
        }
        for s, p in zip(samples, probs)
    ]
    return {
        "trained": True,
        "username": username,
        "model": bundle["kind"],
        "auc": round(bundle["auc"], 3),
        "predictions": preds,
    }


@app.get("/review/move/{move_id}")
def review_move(move_id: int, db: Session = Depends(get_db)):
    move = db.query(MoveAnalysis).filter(MoveAnalysis.id == move_id).first()
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")

    move_data = {
        "move_san": move.move_san or move.move_uci,
        "classification": move.classification,
        "move_number": move.move_number,
        "color": move.color,
        "score": move.score,
        "mate_in": move.mate_in,
        "best_mate_in": move.best_mate_in,
        "best_move": move.best_move or "N/A",
        "opening": move.opening or "Unknown",
        "captured_piece": move.captured_piece,
    }
    review = reviewer.review_move(move_data)
    return {"review": review}
