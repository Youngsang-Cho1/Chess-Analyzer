from game_analysis import analyze_game
from chesscom import ChessComClient
from database import SessionLocal
from models import Game, AnalysisJob
from crud import save_game, save_analysis
import time as time_module

def process_user_games(username: str, new_games: int = 10, opponent: str = None, job_id: int = None):
    client = ChessComClient()
    db = SessionLocal()

    def update_job(status, processed=0, error=None):
        if job_id is None:
            return
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = status
            job.processed = processed
            if error:
                job.error = error
            db.commit()

    if opponent:
        print(f"Fetching games for {username} vs {opponent} (Target: {new_games} new games)...")
        games = client.get_games_vs_opponent(username, opponent)
    else:
        print(f"Fetching data for user: {username} (Target: {new_games} new games)...")
        games = client.get_recent_games(username)

    skipped = 0
    processed = 0

    try:
        for idx, game in enumerate(games):
            if processed >= new_games:
                print(f"Reached target of {new_games} new games.")
                break

            pgn = game.get('pgn')
            url = game.get('url')

            if db.query(Game).filter(Game.url == url).first():
                print(f"Game already exists: {url}")
                skipped += 1
                continue

            print(f"Analyzing new game {processed+1}/{new_games} (Source idx: {idx})...")

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
                'time_class': game.get('time_class', ''),
                'end_time': game.get('end_time', 0),
                'rated': headers.get('Event', '').lower() != 'casual',
                'rules': 'chess',
                'opening': analysis.get('detected_opening', headers.get('Opening', 'Unknown'))
            }

            saved_game = save_game(db, game_data, summary)
            if saved_game:
                save_analysis(db, saved_game.id, moves)
            processed += 1
            update_job("running", processed)

        # Invalidate ai_insight_cache so next /stats call regenerates it
        if processed > 0:
            latest = db.query(Game).filter(
                (Game.white_username.ilike(username)) | (Game.black_username.ilike(username))
            ).order_by(Game.id.desc()).first()
            if latest:
                latest.ai_insight_cache = None
                db.commit()

        update_job("done", processed)

    except Exception as e:
        print(f"Error processing games: {e}")
        update_job("failed", processed, error=str(e))
    finally:
        db.close()

    if processed == 0 and skipped == 0:
        print(f"No games found for {username}" + (f" vs {opponent}" if opponent else ""))
    print(f"Batch Complete: Processed {processed} new games, skipped {skipped} existing games.")

if __name__ == "__main__":
    process_user_games("choys1211", new_games=5)