from chesscom import ChessComClient
from database import init_db, SessionLocal
from crud import save_game
import json

def main():
    # Initialize DB tables
    init_db()
    
    # Create DB Session
    db = SessionLocal()
    
    try:
        client = ChessComClient()
        test_user = "choys1211" 
        print(f"--- Testing Chess.com API for user: {test_user} ---\n")
        
        print("1. Fetching Profile...")
        profile = client.get_player_profile(test_user)
        if profile:
            print(f"Success! Name: {profile.get('name')} | ID: {profile.get('player_id')}")
            print(f"URL: {profile.get('url')}")
        else:
            print("Failed to fetch profile.")

        print("\n2. Fetching a game by opponent")
        pgn_text = client.get_latest_game_vs_player(test_user, "Masuk-saja")
        
        if pgn_text:
            print("Success! Found game.")
            game = {'pgn': pgn_text, 'url': 'fetched-by-opponent-search'}
            
            print(f"PGN (first 50 chars): {game.get('pgn', '')[:50]}...")
            
            # Save to DB
            print("\n3. Saving to Database...")
            saved_game = save_game(db, game)
            print(f"Game saved with ID: {saved_game.id}")
            
            # Run Analysis
            print("\n4. Running Stockfish Analysis...")
            from analyzer import analyze_game
            analysis_data = analyze_game(game.get('pgn'))
            
            moves = analysis_data['moves']
            summary = analysis_data['summary']

            print("\n--- Game Analysis Summary ---")
            print(f"White Accuracy: {summary['white']['accuracy']}%")
            print(f"Black Accuracy: {summary['black']['accuracy']}%")
            print("-----------------------------")
            
            # Save Analysis
            print("\n5. Saving Analysis Results...")
            from crud import save_analysis
            save_analysis(db, saved_game.id, moves)
        else:
            print("Failed to fetch game.")
            
    except Exception as e:
        print(f"Error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
