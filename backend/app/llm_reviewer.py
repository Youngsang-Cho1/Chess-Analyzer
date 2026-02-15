import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from rag import ChessRAG 

load_dotenv()


class ChessReviewer:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.llm = ChatGroq(model_name=model)
        self.rag = ChessRAG()
        

        self.review_template = PromptTemplate(
            input_variables=["player", "accuracy", "blunders", "mistakes", "opening"],
            template=("""You are an expert chess coach analyzing a game.

Game Summary:
- Player: {player}
- Accuracy: {accuracy}%
- Blunders: {blunders}
- Mistakes: {mistakes}
- Opening: {opening}

Provide a sincere and thorough review with insightful advice for improvement.
Focus on the most critical issues and specific recommendations. Keep the tone professional and constructive.
"""))

        self.season_template = PromptTemplate(
            input_variables=["username", "style", "win_rate", "avg_accuracy", "brilliant", "blunder", "total_games"],
            template=("""You are a world-class chess coach. You are analyzing the recent performance of a player, {username} (Last {total_games} games).

Player Profile:
- Play Style: {style}
- Win Rate: {win_rate}%
- Avg Accuracy: {avg_accuracy}%

Key Stats:
- Total Brilliant Moves: {brilliant}
- Total Blunders: {blunder}

Task:
1. Analyze their playing style ('{style}') based on the stats.
2. Give 2-3 specific, actionable tips to help them improve.
3. Be encouraging but honest. If they blunder too much, tell them to slow down. If they are too passive, tell them to be bold.

Format the response as a insightful and constructive review of the game. Give the player a useful advice. 
Keep the tone professional. Also, Keep your answer Max. 10 sentences; keep it concise.
"""))

        self.move_template = PromptTemplate(
            input_variables=["move_san", "classification", "move_number", "color", "score", "best_move", "opening", "rag_context"],
            template=("""You are a chess coach. Explain a move to a student.

Move: {move_san} (Move {move_number}, {color})
Class: {classification}
Engine: {score}
Best: {best_move}
Opening: {opening}

{rag_context}

Task:
1. Explain WHY the move is a {classification}.
2. IF there is GM context above, explicitly mention it: "In a similar position, GM [Name] played [Move]..."

Desired Format:
- If {classification} is Blunder/Mistake/Miss/Inaccuracy:
"{move_san} is a {classification} because [reason]. [GM Context if any]. You should have played {best_move} to [reason]."

- If {classification} is Good/Excellent/Best/Great/Brilliant/Book:
"{move_san} is a {classification} move! It [why it's good]. [GM Context if any, e.g. 'GM Magnus also plays this']"

Rules:
- Keep it under 3 lines.
- Natural text.
- Be direct.
"""))
    
    def review_game(self, game_data):
        # Fill template with actual data
        prompt = self.review_template.format(**game_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating review: {e}"

    def review_season(self, stats):
        # Extract clean data for prompt
        data = {
            "username": stats['username'],
            "style": stats['style'],
            "win_rate": stats['win_rate'],
            "avg_accuracy": stats['avg_accuracy'],
            "brilliant": stats['classifications'].get('Brilliant', 0),
            "blunder": stats['classifications'].get('Blunder', 0),
            "total_games": stats['total_games']
        }
        
        prompt = self.season_template.format(**data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating season review: {e}"

    def review_move(self, move_data):
        # RAG Logic: Fetch similar games only for significant errors or misses
        classification = move_data.get("classification", "").lower()
        rag_context = ""
        
        if classification in ["blunder", "mistake", "miss", "inaccuracy"]:
            # We need FEN to search. Assuming move_data pass 'fen' or we can't search.
            # Wait, api.py doesn't pass 'fen' currently. We need to fetch it from DB or pass it.
            # For now, let's assume 'fen' is in move_data or we skip RAG.
            if "fen" in move_data:
                rag_context = self.rag.search_similar_positions(
                    fen=move_data["fen"], 
                    opening=move_data.get("opening", "Unknown")
                )
        
        move_data["rag_context"] = rag_context

        # API endpoint in `api.py` needs to pass 'fen' to `review_move`. 
        # I need to update `api.py` too. 
        
        prompt = self.move_template.format(**move_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating move review: {e}"