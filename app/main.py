from chesscom import ChessComClient
from database import init_db, SessionLocal
from crud import save_game
import json
import os
from llm_reviewer import ChessReviewer
from game_analysis import analyze_game

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
        pgn_text = client.get_latest_game_vs_player(test_user, "masuk-saja")
        
        if pgn_text:
            print("Success! Found game.")
            
            # 3. Analyze Game FIRST to extract metadata
            print("\n3. Running Stockfish Analysis...")
            analysis_data = analyze_game(pgn_text)
            
            moves = analysis_data['moves'] 
            summary = analysis_data['summary'] 
            headers = analysis_data.get('headers', {})

            # 4. Construct Full Game Data
            game_data = {
                'pgn': pgn_text,
                'url': headers.get('Link', 'fetched-by-opponent-search'), # Use Link header if available
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
                'opening': analysis_data.get('detected_opening', headers.get('Opening', 'Unknown'))
            }
            
            # 5. Save to Database (with full metadata)
            print("\n4. Saving to Database...")
            saved_game = save_game(db, game_data, summary)
            print(f"Game saved with ID: {saved_game.id}")
            
            # 6. Save Analysis Results
            print("   Saving Analysis Results...")
            from crud import save_analysis
            save_analysis(db, saved_game.id, moves)

            # 7. Print Summary
            print("\n--- Game Analysis Summary ---")
            print(f"White Accuracy: {summary['white']['accuracy']}%")
            print(f"Black Accuracy: {summary['black']['accuracy']}%")
            print("-----------------------------")

            # 8. LLM Review (Groq)
            if os.getenv("GROQ_API_KEY"):
                print("\n6. Generating AI Review (Groq)...")
                try:
                    # Determine player color
                    white_player = headers.get('White', '')
                    is_white = test_user.lower() in white_player.lower()
                    player_color = "white" if is_white else "black"
                    
                    # Prepare review data
                    stats = summary[player_color]
                    
                    # Create reviewer and generate
                    reviewer = ChessReviewer()
                    review = reviewer.review_game({
                        "player": test_user,
                        "accuracy": stats['accuracy'],
                        "blunders": stats['classification_counts'].get('Blunder', 0),
                        "mistakes": stats['classification_counts'].get('Mistake', 0),
                        "opening": moves[-1].get('opening', 'Unknown') if moves else "Unknown"
                    })
                    
                    print(f"\n 🤖 AI Coach Review for {test_user} ({player_color}):")
                    print(review)
                    
                except Exception as e:
                    print(f"Failed to generate AI review: {e}")
            else:
                 print("\n Set GROQ_API_KEY in .env to enable AI Game Review")
        else:
            print("Failed to fetch game.")
            
    except Exception as e:
        print(f"Error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
