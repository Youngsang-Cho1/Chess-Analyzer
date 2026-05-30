from sqlalchemy.orm import Session
from database import SessionLocal
from models import Game, MoveAnalysis
from sqlalchemy import desc, or_
from llm_reviewer import ChessReviewer
import statistics
import math

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

        # Count actual sacrifices from MoveAnalysis
        game_ids = [g.id for g in games]
        user_color_map = {
            g.id: ("white" if g.white_username.lower() == user_lower else "black")
            for g in games
        }
        sacrifice_rows = db.query(MoveAnalysis).filter(
            MoveAnalysis.game_id.in_(game_ids),
            MoveAnalysis.is_sacrifice == 'true'
        ).all()
        sacrifice_count = sum(
            1 for m in sacrifice_rows
            if m.color == user_color_map.get(m.game_id)
        )

        # Count forcing moves (checks + captures) from move_san
        forcing_rows = db.query(MoveAnalysis).filter(
            MoveAnalysis.game_id.in_(game_ids)
        ).all()
        forcing_count = sum(
            1 for m in forcing_rows
            if m.color == user_color_map.get(m.game_id)
            and m.move_san
            and ('+' in m.move_san or 'x' in m.move_san)
        )

        # Style vector (0–100 each axis)
        total_moves = max(sum(classifications.values()), 1)

        # Consistency: sigmoid on accuracy stdev.
        # Centre at stdev=15 (typical average player), slope=0.15
        acc_stdev = statistics.stdev(accuracies) if len(accuracies) >= 2 else 20
        consistency = round(100 / (1 + math.exp(0.15 * (acc_stdev - 15))))

        # Aggression: sacrifice rate + forcing move rate, sigmoid scaled.
        # Centre: sacrifice ~3% of moves, forcing ~20% of moves is average
        sac_rate = sacrifice_count / total_moves
        forcing_rate = forcing_count / total_moves
        aggr_raw = sac_rate * 0.6 + forcing_rate * 0.4
        # sigmoid centred at 0.12 (average), scale to 0-100
        aggression = round(100 / (1 + math.exp(-15 * (aggr_raw - 0.12))))

        # Accuracy score: straight 0-100
        accuracy_score = round(avg_accuracy)

        # Tactical: ability to find hard moves (Brilliant, Great) relative to
        # non-trivial decisions. sigmoid centred at 5% of non-book moves.
        non_book = max(total_moves - classifications["Book"], 1)
        tactical_raw = (classifications["Brilliant"] * 3 + classifications["Great"]) / non_book
        # sigmoid centred at 0.04 (4% of non-book moves being Great/Brilliant is solid)
        tactical = round(100 / (1 + math.exp(-80 * (tactical_raw - 0.04))))

        style_vector = {
            "consistency": consistency,
            "aggression": aggression,
            "accuracy": accuracy_score,
            "tactical": tactical,
        }

        # ── Archetype (what kind of player) ──────────────────────────────
        if aggression >= 60:
            archetype = "Attacker"
        elif tactical >= 65:
            archetype = "Tactician"
        elif accuracy_score >= 82 and consistency >= 60:
            archetype = "Technician"
        elif accuracy_score >= 72 and consistency >= 60 and aggression < 45:
            archetype = "Grinder"
        elif aggression < 35 and consistency >= 60:
            archetype = "Defender"
        else:
            archetype = "All-Rounder"

        # ── Prefix (quality/accuracy of that style) ───────────────────────
        # Clinical: very high accuracy + consistency (cold, clean execution)
        # Sharp:    high accuracy (confident, precise decisions)
        # Scrappy:  high tactical but lower accuracy (thrives in chaos)
        # Shaky:    lower accuracy (ideas are there but execution wavers)
        if accuracy_score >= 82 and consistency >= 65:
            prefix = "Clinical"
        elif accuracy_score >= 76:
            prefix = "Sharp"
        elif tactical >= 60 and accuracy_score < 74:
            prefix = "Scrappy"
        else:
            prefix = "Shaky"

        # ── Consistency tag (shown separately in UI) ──────────────────────
        if consistency >= 68:
            consistency_tag = "Steady"
        elif consistency < 38:
            consistency_tag = "Volatile"
        else:
            consistency_tag = None

        style = f"{prefix} {archetype}"
        style_tag = consistency_tag  # passed to frontend separately

        # LLM Coach — use cached value from the most recent game if available
        ai_feedback = games[0].ai_insight_cache if games[0].ai_insight_cache else None
        if not ai_feedback:
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
                games[0].ai_insight_cache = ai_feedback
                db.commit()
            except Exception as e:
                print(f"Coach error: {e}")
                ai_feedback = "AI Coach is currently unavailable (Check API Key)"

        return {
            "username": username,
            "total_games": total_games,
            "win_rate": round(win_rate, 1),
            "record": f"{wins}W - {losses}L - {draws}D",
            "avg_accuracy": round(avg_accuracy, 1),
            "classifications": classifications,
            "style": style,
            "style_tag": style_tag,
            "style_vector": style_vector,
            "history": history,
            "ai_insight": ai_feedback
        }

    finally:
        db.close()

