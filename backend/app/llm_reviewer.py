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
            input_variables=["move_san", "classification", "move_number", "color", "score", "best_move", "opening", "rag_context", "captured_piece"],
            template=("""You are a chess coach. Explain a move to a student.

Move: {move_san} (Move {move_number}, {color})
Class: {classification}
Captured Piece: {captured_piece} (If None, no capture)
Engine Score: {score} (Centipawns. Positive = White advantage)
Best Move Suggested: {best_move}
Opening: {opening}

Relevant GM Games (Context):
{rag_context}

Task:
1. Explain WHY the move is a {classification}.
   - If {classification} is **Brilliant**: It's likely a sacrifice. Explain what was given up and what compensation was gained (attack, mate threat, positional dominance).
   - If {classification} is **Blunder/Mistake**: Explain why the played move is bad compared to the Best Move ({best_move}).
   - If Captured Piece is present, mention it explicitly (e.g., "captured a {captured_piece}").

2. **CRITICAL RULE about GM Context**:
   - IF `{rag_context}` is provided and meaningful, you MAY say: "In a similar position, GM [Name] played..."
   - IF `{rag_context}` is EMPTY or irrelevant, **DO NOT MENTION GM GAMES AT ALL.** Do not invent or hallucinate GM moves.
   - Focus on the engine's reason instead.

Desired Format:
- Keep it under 3 lines.
- Be direct and educational.
- "Great move! You sacrificed a Rook to expose the King..." (if Brilliant)
- "That was a mistake. You lost a Knight for nothing. {best_move} would have saved it." (if Blunder)
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
        
        # Only use RAG for blunders/mistakes where advice is needed
        if classification in ["blunder", "mistake", "miss"]:
            if "fen" in move_data and move_data["fen"]:
                rag_context = self.rag.search_similar_positions(
                    fen=move_data["fen"], 
                    opening=move_data.get("opening", "Unknown")
                )
        
        move_data["rag_context"] = rag_context
        # Ensure captured_piece is string
        if not move_data.get("captured_piece"):
            move_data["captured_piece"] = "None"
        
        prompt = self.move_template.format(**move_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating move review: {e}"