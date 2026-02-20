import chromadb
from chromadb.utils import embedding_functions

CHROMA_DATA_PATH = "./data/chroma_db"

class ChessRAG:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            print("RAG: ChromaDB connected successfully.")
        except Exception as e:
            print(f"RAG: Error connecting to ChromaDB: {e}")
            self.client = None

    def _get_collection(self, name: str):
        """Try to get a collection; returns None if it doesn't exist."""
        if not self.client:
            return None
        try:
            return self.client.get_collection(name=name, embedding_function=self.ef)
        except Exception:
            return None

    def search_opening_theory(self, opening_name: str) -> str:
        """Retrieve theory for the given opening by name similarity."""
        collection = self._get_collection("opening_theory")
        if not collection:
            return ""

        try:
            results = collection.query(
                query_texts=[opening_name],
                n_results=1
            )
            if results and results["documents"] and results["documents"][0]:
                doc = results["documents"][0][0]
                opening = results["metadatas"][0][0].get("opening", "")
                distance = results["distances"][0][0]

                # Only use if reasonably similar (distance < 1.0 on cosine space)
                if distance < 1.0:
                    # Strip the "Opening: ..." header line and return just the theory text
                    lines = doc.split("\n\n", 1)
                    theory = lines[1] if len(lines) > 1 else doc
                    return f"[{opening} Theory]: {theory}"
            return ""
        except Exception as e:
            print(f"RAG Opening Search Error: {e}")
            return ""
