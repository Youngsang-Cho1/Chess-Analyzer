from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
from models import Game, MoveAnalysis, Base
from sqlalchemy import or_
from batch import process_user_games
from player_stats import get_player_stats
from llm_reviewer import ChessReviewer

reviewer = ChessReviewer()

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(engine)
    print("DB tables verified/created.")

# Allow Frontend (Next.js) to access Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Chess Analyzer API"}


@app.post("/analyze/{username}")
def analyze_games(username: str, background_tasks: BackgroundTasks, limit: int = 5, opponent: str = None):
    background_tasks.add_task(process_user_games, username, limit=limit, opponent=opponent) # using batch.py
    msg = f"Analysis started for {username} ({limit} games)"
    if opponent:
        msg += f" vs {opponent}"
    return {"message": msg + ". Refresh in a few minutes."}

@app.get("/games/{username}")
def get_games(username: str):
    db = SessionLocal()
    # Query games where user is either White or Black
    games = db.query(Game).filter(
        or_(Game.white_username == username, Game.black_username == username)
    ).all()
    db.close()
    return {"games": games}

@app.get("/game/{game_id}")
def get_game(game_id: int):
    db = SessionLocal()
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        db.close()
        return {"error": "Game not found"}
    analysis = db.query(MoveAnalysis).filter(
        MoveAnalysis.game_id == game_id
    ).order_by(MoveAnalysis.id).all()
    db.close()
    return {"game": game, "analysis": analysis}

@app.get('/stats/{username}')
def get_stats(username: str):
    stats = get_player_stats(username, limit=50)
    return {"stats": stats}

@app.get('/moves/{username}/{classification}')
def get_moves(username: str, classification: str):
    db = SessionLocal()
    results = db.query(MoveAnalysis, Game).join(Game, MoveAnalysis.game_id == Game.id).filter(
        or_(Game.white_username == username, Game.black_username == username),
        MoveAnalysis.classification == classification
    ).all()
    db.close()

    res = []
    for move, game in results:
        user_color = "white" if game.white_username == username else "black"
        if move.color == user_color:
            res.append(move)
    return {"moves": res}


@app.get("/review/move/{move_id}")
def review_move(move_id: int):
    db = SessionLocal()
    move = db.query(MoveAnalysis).filter(MoveAnalysis.id == move_id).first()
    db.close()
    if not move:
        return {"error": "Move not found"}

    move_data = {
        "move_san": move.move_san or move.move_uci,
        "classification": move.classification,
        "move_number": move.move_number,
        "color": move.color,
        "score": move.score,
        "best_move": move.best_move or "N/A",
        "opening": move.opening or "Unknown",
        "captured_piece": move.captured_piece,
    }
    review = reviewer.review_move(move_data)
    return {"review": review}
