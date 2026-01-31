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
        print(f"--- Testing Chess.com API for user: {test_user} ---")
        
        print("\n1. Fetching Profile...")
        profile = client.get_player_profile(test_user)
        if profile:
            print(f"Success! Name: {profile.get('name')} | ID: {profile.get('player_id')}")
            print(f"URL: {profile.get('url')}")
        else:
            print("Failed to fetch profile.")

        print("\n2. Fetching Most Recent Game...")
        game = client.get_most_recent_games(test_user)
        if game:
            if isinstance(game, list):
                print(f"Received {len(game)} games. Showing the last one.")
                game = game[-1]

            print("Success! Found game.")
            print(f"White: {game.get('white', {}).get('username')} ({game.get('white', {}).get('rating')})")
            print(f"Black: {game.get('black', {}).get('username')} ({game.get('black', {}).get('rating')})")
            print(f"URL: {game.get('url')}")
            print(f"PGN (first 50 chars): {game.get('pgn', '')[:50]}...")
            
            # Save to DB
            print("\n3. Saving to Database...")
            saved_game = save_game(db, game)
            print(f"Game saved with ID: {saved_game.id}")
            
            # Run Analysis
            print("\n4. Running Stockfish Analysis...")
            from analyzer import analyze_game
            analysis_results = analyze_game(game.get('pgn'))
            
            # Save Analysis
            print("\n5. Saving Analysis Results...")
            from crud import save_analysis
            save_analysis(db, saved_game.id, analysis_results)

            
        else:
            print("Failed to fetch recent game.")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
