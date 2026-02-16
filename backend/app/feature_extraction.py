
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from models import Game, MoveAnalysis
from database import SessionLocal
from collections import Counter
import math

def get_player_features(username: str, db: Session):
    games = db.query(Game).filter(
        (Game.white_username == username) | (Game.black_username == username)
    ).all()

    if not games:
        return None

    total_acpl = []
    aggression_scores = []
    
    opening_counter = Counter()
    class_counter = Counter()
    
    tactical_opportunities = 0
    total_moves = 0
    
    endgame_moves = 0
    endgame_errors = 0

    for game in games:
        is_white = game.white_username == username
        color = "white" if is_white else "black"
        
        opening_name = game.opening.split(":")[0] if game.opening else "Unknown"
        opening_counter[opening_name] += 1

        moves = db.query(MoveAnalysis).filter(
            MoveAnalysis.game_id == game.id,
            MoveAnalysis.color == color
        ).order_by(MoveAnalysis.move_number).all()

        if not moves:
            continue

        game_acpl = []
        checks = 0
        sacrifices = 0
        
        for move in moves:
            total_moves += 1
            class_counter[move.classification] += 1
            
            if move.classification == "Blunder":
                game_acpl.append(300)
                endgame_errors += 1 if move.move_number > 30 else 0
            elif move.classification == "Mistake":
                game_acpl.append(100)
                endgame_errors += 1 if move.move_number > 30 else 0
            elif move.classification == "Inaccuracy":
                game_acpl.append(50)
            else:
                game_acpl.append(10)
            
            if move.move_number > 30:
                endgame_moves += 1

            if "+" in (move.move_san or ""):
                checks += 1
            
            if move.classification in ["Brilliant", "Great", "Best"]:
                if move.classification == "Brilliant":
                    sacrifices += 1
                
                if move.classification in ["Brilliant", "Great"]:
                    tactical_opportunities += 1

        if game_acpl:
            total_acpl.append(np.mean(game_acpl))
        
        blunders = sum(1 for m in moves if m.classification == "Blunder")
        aggression_val = (checks * 1.5 + sacrifices * 4 + blunders * 0.5) / max(1, len(moves)) * 100
        aggression_scores.append(aggression_val)

    n_games = len(games)
    unique_openings = len(opening_counter)
    opening_entropy = calculate_entropy(opening_counter)
    
    features = {
        "username": username,
        "games_analyzed": n_games,
        "avg_acpl": np.mean(total_acpl) if total_acpl else 0,
        "aggression_score": np.mean(aggression_scores) if aggression_scores else 0,
        "opening_entropy": opening_entropy,
        "opening_breadth": unique_openings / max(1, n_games),
        "tactical_rate": tactical_opportunities / max(1, total_moves),
        "endgame_error_rate": endgame_errors / max(1, endgame_moves) if endgame_moves > 0 else 0,
        "brilliant_rate": class_counter["Brilliant"] / max(1, total_moves),
        "blunder_rate": class_counter["Blunder"] / max(1, total_moves),
        "draw_rate": sum(1 for g in games if (g.white_username == username and g.white_result == "repetition") or (g.black_username == username and g.black_result == "repetition")) / n_games
    }

    return features

def calculate_entropy(counter):
    total = sum(counter.values())
    if total == 0: return 0
    entropy = 0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy

if __name__ == "__main__":
    db = SessionLocal()
    # print(get_player_features("joyeongsang", db))
