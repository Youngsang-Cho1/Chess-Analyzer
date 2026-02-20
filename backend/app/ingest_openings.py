"""
Run this script to ingest opening theory into ChromaDB.
Usage (inside Docker):
    docker-compose exec chess-analyzer python -m app.ingest_openings
"""
import json
import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DATA_PATH = "./data/chroma_db"
THEORY_FILE = os.path.join(os.path.dirname(__file__), "opening_theory.json")

def ingest_openings():
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    # Delete existing collection to avoid duplicates on re-run
    try:
        client.delete_collection("opening_theory")
        print("Deleted existing 'opening_theory' collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="opening_theory",
        embedding_function=ef
    )

    with open(THEORY_FILE, "r") as f:
        openings = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for i, entry in enumerate(openings):
        # Build the document: embed both opening name + content for better matching
        doc = f"Opening: {entry['opening']}\n\n{entry['content']}"
        documents.append(doc)
        metadatas.append({"opening": entry["opening"]})
        ids.append(f"opening_{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Ingested {len(documents)} openings into ChromaDB 'opening_theory' collection.")

if __name__ == "__main__":
    ingest_openings()
