import chromadb
from chromadb.utils import embedding_functions
from chess_utils import get_board_description
import chess

CHROMA_DATA_PATH = "./data/chroma_db"

class ChessRAG:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self.collection = self.client.get_collection(
                name="chess_games",
                embedding_function=self.ef
            )
            print("RAG: ChromaDB connected successfully.")
        except Exception as e:
            print(f"RAG: Error connecting to ChromaDB: {e}")
            self.collection = None

    def search_similar_positions(self, fen: str, opening: str, limit: int = 3) -> str:
        if not self.collection:
            return "RAG System unavailable."

        try:
            # 1. Convert FEN to Description
            board = chess.Board(fen)
            query_text = get_board_description(board, opening)
            
            # 2. Query Vector DB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit
            )
            
            # 3. Format Results
            if not results['metadatas'] or not results['metadatas'][0]:
                return "No similar GM games found."

            context = "Here are similar situations from GM games:\n"
            found = False
            
            for i, meta in enumerate(results['metadatas'][0]):
                # Filter by distance if needed, but for now just take top results
                dist = results['distances'][0][i]
                if dist > 1.5: # Arbitrary threshold, tune later
                    continue
                
                white = meta.get('white', '?')
                black = meta.get('black', '?')
                next_move = meta.get('next_move', 'Unknown')
                result = meta.get('result', '*')
                
                context += f"- In {white} vs {black} ({result}), the GM played **{next_move}**.\n"
                found = True
            
            if not found:
                return "No highly similar GM games found."
                
            return context

        except Exception as e:
            print(f"RAG Search Error: {e}")
            return "Error retrieving similar games."
