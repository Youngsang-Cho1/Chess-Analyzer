import os
import io
import chess.pgn
import chromadb
from chromadb.utils import embedding_functions
from chesscom import ChessComClient
from chess_utils import get_board_description

CHROMA_DATA_PATH = "./data/chroma_db"

def ingest_gm_games():
    print("Initializing ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
    # Try using a different embedding function if needed, or default
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = chroma_client.get_or_create_collection(
        name="chess_games",
        embedding_function=sentence_transformer_ef
    )
    
    client = ChessComClient()
    gms = ["MagnusCarlsen", "Hikaru", "FabianoCaruana", "Nepomniachtchi", "DingLiren"] 
    # Added more GMs for variety
    
    for gm in gms:
        print(f"Fetching games for {gm}...")
        games = client.get_recent_games(gm, limit=10) # Increased limit slightly
        
        if not games:
            continue
            
        for game_data in games:
            pgn_text = game_data.get('pgn')
            if not pgn_text: continue
            
            pgn_io = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn_io)
            if not game: continue

            headers = game.headers
            opening = headers.get("ECOUrl", "").split("/")[-1].replace("-", " ") or "Unknown Opening"
            result = headers.get("Result", "*")
            white = headers.get("White", "?")
            black = headers.get("Black", "?")
            date = headers.get("Date", "????.??.??")
            
            print(f"  Ingesting: {white} vs {black} ({date}) - {opening}")

            board = game.board()
            
            ids = []
            documents = []
            metadatas = []
            
            move_count = 0
            for move in game.mainline_moves():
                # Capture the state BEFORE the move
                fen_before = board.fen()
                desc = get_board_description(board, opening)
                san_move = board.san(move) # Standard Algebraic Notation (e.g., "Nf3")
                
                # We want to store the state and what happened NEXT
                if move_count % 5 == 0: # Sampling
                    doc_id = f"{white}_{black}_{date}_{move_count}"
                    ids.append(doc_id)
                    documents.append(desc)
                    metadatas.append({
                        "fen": fen_before,
                        "opening": opening,
                        "white": white,
                        "black": black,
                        "result": result,
                        "move_number": move_count,
                        "next_move": san_move,  # CRITICAL: Store what the GM played
                        "player_turn": "White" if board.turn == chess.WHITE else "Black"
                    })
                
                board.push(move)
                move_count += 1
            
            if ids:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"    Added {len(ids)} positions.")

    print("Ingestion Complete!")

if __name__ == "__main__":
    ingest_gm_games()
