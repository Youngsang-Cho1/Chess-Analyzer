import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

load_dotenv()


class ChessReviewer:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.llm = ChatGroq(model_name=model)

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
            input_variables=["move_san", "classification", "color", "formatted_score", "best_move", "opening", "captured_piece", "mate_context", "opening_theory"],
            template=("""You are a chess coach. Provide an ultra-concise, punchy 1-sentence review for a single move, exactly like Chess.com's Game Review.

Move: {move_san} ({color})
Classification: {classification}
Engine Score: {formatted_score}
Best Move: {best_move}
{mate_context}
{opening_theory}

CRITICAL RULES:
1. MAX 1 SHORT SENTENCE. NEVER use two sentences.
2. If the move is a Miss and they missed a mate, literally say: "You missed a chance to checkmate the king." or "They missed a forced mate."
3. If the move is a blunder that allows mate, literally say: "This blunder allows a forced mate."
4. Do NOT say "This move is classified as...". Just state the fact directly. 
5. Example format: "Qxd5 is a blunder since you missed a chance to checkmate the king." or "Nf3 develops a piece and controls the center." or "This permits mate in 1."
6. No markdown, no bold. Plain text.
"""))

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

        move_data["opening_theory"] = ""

        mate_in = move_data.get("mate_in")
        best_mate_in = move_data.get("best_mate_in")

        formatted_score = f"{move_data.get('score', 0) / 100} cp"
        mate_context = ""

        if mate_in is not None:
            formatted_score = f"M{abs(mate_in)}"
            mate_context = f"FORCED MATE: The board evaluates to mate in {abs(mate_in)}."

        if best_mate_in is not None and mate_in is None:
            mate_context = "MISSED MATE: The best move would have led to a forced checkmate, but this move missed it."

        move_data["formatted_score"] = formatted_score
        move_data["mate_context"] = mate_context

        # We don't need these raw fields in the prompt formatting dict:
        if "score" in move_data:
            del move_data["score"]
        if "move_number" in move_data:
            del move_data["move_number"]
        if "mate_in" in move_data:
            del move_data["mate_in"]
        if "best_mate_in" in move_data:
            del move_data["best_mate_in"]

        prompt = self.move_template.format(**move_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating move review: {e}"