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
            input_variables=["move_san", "classification", "move_number", "color", "score", "best_move", "opening", "captured_piece", "opening_theory"],
            template=("""You are a chess coach. Explain a single move to a student.

Move Played: {move_san} (Move {move_number}, {color})
Classification: {classification}
Captured Piece: {captured_piece}
Engine Score After Move: {score} cp (Positive = White advantage)
Engine's Best Move: {best_move}
Opening: {opening}

{opening_theory}

Task:
Explain WHY this move is classified as "{classification}".

Guidelines by classification:
- **Brilliant**: Briefly explain the sacrifice and the compensation (attack, position).
- **Blunder/Mistake/Miss**: Explain the critical error and why {best_move} was better.
- **Good/Best/Excellent**: Briefly note why it's good (space, development, tactics).

CRITICAL RULES FOR RESPONSE:
1. MAX 2 SHORT SENTENCES. 
2. Be extremely punchy and direct. No conversational filler like "This move is classified as...". Just say exactly what happened.
3. Example Good: "It's a blunder since you hung your Knight on f3. Playing Qe2 would have defended it while controlling the center."
4. If opening theory is provided, weave it naturally into ONE of the sentences, but DO NOT make it longer.
5. NO markdown, NO bold, NO lists. Plain text only.
"""))

    def review_game(self, game_data):
        prompt = self.review_template.format(**game_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating review: {e}"

    def review_season(self, stats):
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
        # Ensure captured_piece is a string
        if not move_data.get("captured_piece"):
            move_data["captured_piece"] = "None (not a capture)"

        # Fetch opening theory from RAG
        opening_name = move_data.get("opening", "")
        opening_theory = ""
        if opening_name and opening_name not in ("Unknown", "Opening Move", "No Opening"):
            theory = self.rag.search_opening_theory(opening_name)
            if theory:
                opening_theory = f"Opening Theory Context:\n{theory}"

        move_data["opening_theory"] = opening_theory

        prompt = self.move_template.format(**move_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating move review: {e}"