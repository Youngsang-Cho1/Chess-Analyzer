from game_analysis import analyze_game
from chesscom import ChessComClient
from database import SessionLocal
from models import Game
from crud import save_game, save_analysis
import time

def process_user_games(username: str, limit: int = 10, opponent: str = None):
    client = ChessComClient()
    db = SessionLocal()
    
    if opponent:
        print(f"Fetching games for {username} vs {opponent} (Target: {limit} games)...")
        games = client.get_games_vs_opponent(username, opponent, limit)
    else:
        print(f"Fetching data for user: {username} (Target: {limit} new games)...")
        games = client.get_recent_games(username, limit) 
    
    if not games:
        print(f"No games found for {username}" + (f" vs {opponent}" if opponent else ""))
        db.close()
        return

    skipped = 0
    processed = 0
    
    try:
        for idx, game in enumerate(games):
            if processed >= limit:
                print(f"Reached target of {limit} new games.")
                break

            pgn = game.get('pgn')
            url = game.get('url')

            if db.query(Game).filter(Game.url == url).first():
                print(f"Game already exists: {url}")
                skipped += 1
                continue

            print(f"Analyzing new game {processed+1}/{limit} (Source idx: {idx})...")

            analysis = analyze_game(pgn)

            headers = analysis['headers']
            moves = analysis['moves']
            summary = analysis['summary']

            game_data = {
                'pgn': pgn,
                'url': url,
                'white': {
                    'username': headers.get('White', 'Unknown'),
                    'rating': int(headers.get('WhiteElo', 0)),
                    'result': headers.get('Result', '').split('-')[0] if '-' in headers.get('Result', '') else ''
                },
                'black': {
                    'username': headers.get('Black', 'Unknown'),
                    'rating': int(headers.get('BlackElo', 0)),
                    'result': headers.get('Result', '').split('-')[1] if '-' in headers.get('Result', '') else ''
                },
                'time_control': headers.get('TimeControl', ''),
                'end_time': 0, # Timestamp hard to parse from headers reliably without datetime lib
                'rated': headers.get('Event', '').lower() != 'casual',
                'rules': 'chess',
                'opening': analysis.get('detected_opening', headers.get('Opening', 'Unknown'))
            }

            saved_game = save_game(db, game_data, summary)
            if saved_game:
                save_analysis(db, saved_game.id, moves)
            processed += 1 

    except Exception as e:
        print(f"Error processing games: {e}")
    finally:
        db.close()

    print(f"Batch Complete: Processed {processed} new games, skipped {skipped} existing games.")

if __name__ == "__main__":
    process_user_games("choys1211", limit=5)