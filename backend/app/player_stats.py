from sqlalchemy.orm import Session
from database import SessionLocal
from models import Game
from sqlalchemy import desc, or_
import json
from llm_reviewer import ChessReviewer

def get_player_stats(username: str, limit: int = 50):
    db: Session = SessionLocal()
    
    try:
        games = db.query(Game).filter(
            or_(
                Game.white_username.ilike(username),
                Game.black_username.ilike(username)
            )
        ).order_by(desc(Game.id)).limit(limit).all()
        
        if not games:
            print(f"No games found for {username}")
            return None

        total_games = len(games)
        wins = 0
        losses = 0
        draws = 0
        
        accuracies = []
        history = [] # For storing individual game details
        
        classifications = {
            "Brilliant": 0, "Great": 0, "Book": 0, "Best": 0,
            "Excellent": 0, "Good": 0, "Inaccuracy": 0, 
            "Mistake": 0, "Blunder": 0, "Miss": 0
        }

        user_lower = username.lower()

        for game in games:
            is_white = game.white_username.lower() == user_lower
            
            my_result = game.white_result if is_white else game.black_result
            result_label = "Draw"
            
            if my_result == '1':
                wins += 1
                result_label = "Win"
            elif my_result == '0':
                losses += 1
                result_label = "Loss"
            else: 
                draws += 1
                
            acc = game.white_accuracy if is_white else game.black_accuracy
            if acc is not None:
                accuracies.append(acc)
                
            moves = game.white_move_counts if is_white else game.black_move_counts
            if moves:
                for key, count in moves.items():
                    classifications[key] += count

            history.append({
                "id": game.id,
                "is_white": is_white,
                "opponent": game.black_username if is_white else game.white_username,
                "result": result_label,
                "accuracy": acc if acc else 0.0,
                "opening": game.opening if game.opening else "Unknown"
            })
                        
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        aggression_score = (classifications["Brilliant"] * 2 + classifications["Blunder"]) / total_games
        style = "Balanced"

        if aggression_score > 1.5 and avg_accuracy < 80:
            style = "Wild Gambler"
        elif aggression_score > 1.5 and avg_accuracy >= 90:
            style = "Tactical Fighter"
        elif avg_accuracy > 90:
            style = "GM Prospect"
        elif aggression_score < 0.7:
            style = "Solid Grinder"

        # LLM Coach Integration
        ai_feedback = "AI Coach is currently unavailable (Check API Key)"
        try:
            reviewer = ChessReviewer()
            ai_feedback = reviewer.review_season({
                "username": username,
                "style": style,
                "win_rate": round(win_rate, 1),
                "avg_accuracy": round(avg_accuracy, 1),
                "classifications": classifications,
                "total_games": total_games
            })
        except Exception as e:
            print(f"Coach error: {e}")

        return {
            "username": username,
            "total_games": total_games,
            "win_rate": round(win_rate, 1),
            "record": f"{wins}W - {losses}L - {draws}D",
            "avg_accuracy": round(avg_accuracy, 1),
            "classifications": classifications,
            "style": style,
            "history": history,
            "ai_insight": ai_feedback
        }

    finally:
        db.close()

