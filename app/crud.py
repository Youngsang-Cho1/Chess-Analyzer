from sqlalchemy.orm import Session
from models import Game, MoveAnalysis
from sqlalchemy.dialects.postgresql import insert

def save_game(db: Session, game_data: dict):
    """
    Saves a game to the database. Skips if the game URL already exists.
    """
    # Extract relevant fields from nested JSON structure
    white_info = game_data.get('white', {})
    black_info = game_data.get('black', {})
    
    new_game = Game(
        url=game_data.get('url'),
        pgn=game_data.get('pgn'),
        fen=game_data.get('fen'),
        time_control=game_data.get('time_control'),
        end_time=game_data.get('end_time'),
        rated=str(game_data.get('rated')), # Store as string just in case
        time_class=game_data.get('time_class'),
        rules=game_data.get('rules'),
        
        white_username=white_info.get('username'),
        white_rating=white_info.get('rating'),
        white_result=white_info.get('result'),
        
        black_username=black_info.get('username'),
        black_rating=black_info.get('rating'),
        black_result=black_info.get('result'),
    )

    # Check if exists
    existing_game = db.query(Game).filter(Game.url == new_game.url).first()
    if not existing_game:
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        print(f"Game saved: {new_game.url}")
        return new_game
    else:
        print(f"Game already exists: {new_game.url}")
        return existing_game

def save_analysis(db: Session, game_id: int, analysis_results: list):
    """
    Saves analysis results to the database.
    """
    # First, delete existing analysis for this game to avoid duplicates if re-analyzing
    db.query(MoveAnalysis).filter(MoveAnalysis.game_id == game_id).delete()
    
    for result in analysis_results:
        analysis = MoveAnalysis(
            game_id=game_id,
            move_number=result['move_number'],
            move_uci=result['move_uci'],
            score=result['score'],
            classification=result['classification'],
            best_move=result['best_move'],
            opening=result['opening']
        )
        db.add(analysis)
    
    db.commit()
    print(f"Saved {len(analysis_results)} analysis moves for Game ID {game_id}")
