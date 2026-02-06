from sqlalchemy.orm import Session
from database import SessionLocal
from models import Game
from sqlalchemy import desc, or_
import json

def get_player_stats(username: str, limit: int = 20):
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
        classifications = {
            "Brilliant": 0, "Great": 0, "Best": 0, 
            "Excellent": 0, "Good": 0, "Inaccuracy": 0, 
            "Mistake": 0, "Blunder": 0, "Miss": 0
        }

        user_lower = username.lower()

        for game in games:
            is_white = game.white_username.lower() == user_lower
            
            # 1. Result Stats
            # 1. Result Stats (Stored as '1', '0', '1/2' from PGN split)
            my_result = game.white_result if is_white else game.black_result
            
            if my_result == '1':
                wins += 1
            elif my_result == '0':
                losses += 1
            else: # '1/2' or others
                draws += 1
                
            # 2. Accuracy Stats
            acc = game.white_accuracy if is_white else game.black_accuracy
            if acc:
                accuracies.append(acc)
                
            # 3. Move Classifications (JSON)
            moves = game.white_move_counts if is_white else game.black_move_counts
            if moves:
                for key, count in moves.items():
                    classifications[key] += count
                        
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        # 4. Style Analysis
        
        aggression_score = (classifications["Brilliant"] + classifications["Blunder"]) / total_games
        style = "Balanced"

        if aggression_score > 1.5 and avg_accuracy < 80:
            style = "Wild Gambler"
        elif aggression_score > 1.5 and avg_accuracy >= 90:
            style = "Tactical Fighter"
        elif avg_accuracy > 90:
            style = "GM Prospect"
        elif aggression_score < 0.7:
            style = "Solid Grinder"

        return {
            "username": username,
            "total_games": total_games,
            "win_rate": round(win_rate, 1),
            "record": f"{wins}W - {losses}L - {draws}D",
            "avg_accuracy": round(avg_accuracy, 1),
            "classifications": classifications,
            "style": style
        }
        
    finally:
        db.close()

def print_report(stats):
    if not stats:
        return

    print("\n" + "="*40)
    print(f"CHESS ANALYSIS REPORT: {stats['username']}")
    print("="*40)
    
    print(f"\n Overall Performance ({stats['total_games']} games)")
    print(f"   • Win Rate: {stats['win_rate']}% ({stats['record']})")
    print(f"   • Avg Accuracy: {stats['avg_accuracy']}%")
    print(f"   • Play Style: {stats['style']}")
    
    print("\n Move Quality Breakdown")
    counts = stats['classifications']
    total_moves = sum(counts.values())
    
    # Grouping for cleaner display
    good_moves = counts["Brilliant"] + counts["Great"] + counts["Best"] + counts["Excellent"]
    bad_moves = counts["Blunder"] + counts["Mistake"] + counts["Miss"]
    
    print(f"   • Brilliant!!  : {counts['Brilliant']} 🔥")
    print(f"   • Great        : {counts['Great']} 🌟")
    print(f"   • Good/Best    : {good_moves} moves")
    print(f"   • Blunders     : {counts['Blunder']} 💀")
    print(f"   • Mistakes     : {counts['Mistake']} ❓") 
    
    print("\n💡 Insight")
    if counts['Brilliant'] > 0:
        print(f"   Wow! You found {counts['Brilliant']} brilliant sacrifices in your last {stats['total_games']} games.")
    
    if counts['Blunder'] > stats['total_games']:
        print(f"   Attention: You are averaging {counts['Blunder']/stats['total_games']:.1f} blunders per game. Focus on hanging pieces.")
    else:
        print("   Solid play! You are keeping blunders low.")
        
    print("="*40 + "\n")

if __name__ == "__main__":
    # Test with username
    import sys
    username = "choys1211"
    if len(sys.argv) > 1:
        username = sys.argv[1]
        
    stats = get_player_stats(username)
    print_report(stats)
