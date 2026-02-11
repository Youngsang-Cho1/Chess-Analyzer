from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal
from models import Game
from sqlalchemy import or_
from batch import process_user_games
from player_stats import get_player_stats

app = FastAPI()

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
def analyze_games(username: str, background_tasks: BackgroundTasks):
    # Run analysis in background so UI doesn't freeze
    background_tasks.add_task(process_user_games, username, limit=5)
    return {"message": f"Analysis started for {username}. Refresh in a few minutes."}

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
    db.close()
    if not game:
        return {"error": "Game not found"}
    return {"game": game}

@app.get('/stats/{username}')
def get_stats(username: str):
    stats = get_player_stats(username, limit=50)
    return {"stats": stats}
