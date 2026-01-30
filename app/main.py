from chesscom import ChessComClient
import json

def main():
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
    else:
        print("Failed to fetch recent game.")

if __name__ == "__main__":
    main()
