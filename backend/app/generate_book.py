import chess.pgn
import chess.polyglot
import json
import os

pgn_path = "eco.pgn"  # Inside Docker, we run from /app
output_path = "opening_book.json"

def generate_book():
    print(f"Loading PGN from {pgn_path}...")
    
    if not os.path.exists(pgn_path):
        print(f"Error: {pgn_path} not found.")
        return

    opening_map = {}
    
    with open(pgn_path) as pgn_file:
        count = 0
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            
            name = game.headers.get("Opening")
            if not name:
                continue

            board = game.board()
            for move in game.mainline_moves():
                board.push(move)

            # Compute Polyglot Zobrist Hash of the final position
            zobrist_hash = chess.polyglot.zobrist_hash(board)
            
            # Store in map (Hash -> Name)
            # Use string key for JSON compatibility
            opening_map[str(zobrist_hash)] = name
            
            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} openings...")

    print(f"Finished! Total openings indexed: {len(opening_map)}")
    
    with open(output_path, "w") as f:
        json.dump(opening_map, f)
    
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    generate_book()
