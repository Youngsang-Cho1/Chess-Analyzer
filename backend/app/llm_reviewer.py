import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

load_dotenv()


class ChessReviewer:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.llm = ChatGroq(model_name=model)
        

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
            input_variables=["move_san", "classification", "move_number", "color", "score", "best_move", "opening"],
            template=("""You are an expert chess coach explaining a single move to a student.

Move Details:
- Move: {move_san} (Move {move_number}, {color})
- Classification: {classification}
- Engine Evaluation after move: {score} centipawns
- Best Move (by engine): {best_move}
- Opening: {opening}

Based on the classification '{classification}', explain:
1. Why this move received this classification.
2. If it's a mistake/blunder/miss, briefly explain what the best move achieves that this move doesn't.
3. If it's a good/great/brilliant move, explain what makes it strong.

It would be better if you can follow this format: this move is a {classification} because....

Rules:
- Keep it to 2-3 sentences MAX!!!!!!!!!
- Be specific and actionable, not generic.
- Use simple, direct, and concise language.
- State all the moves in SAN format.
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
        prompt = self.move_template.format(**move_data)
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating move review: {e}"