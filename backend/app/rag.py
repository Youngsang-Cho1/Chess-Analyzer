"""
RAG is currently disabled.

The opening-theory lookup was using sentence-transformers + ChromaDB, which
dragged ~700MB of PyTorch into the image for a feature that only injected one
line of context into a one-sentence move review. The cost/benefit didn't hold
up, so we keep the call sites intact but return empty results.

To re-enable later (e.g. for GM position similarity via bitboard cosine), drop
in a new implementation here — callers only need `search_opening_theory()`.
"""


class ChessRAG:
    def __init__(self):
        self.client = None
        print("RAG: disabled (stub).")

    def search_opening_theory(self, opening_name: str) -> str:
        return ""
