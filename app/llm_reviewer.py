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
            template="""You are an expert chess coach analyzing a game.

Game Summary:
- Player: {player}
- Accuracy: {accuracy}%
- Blunders: {blunders}
- Mistakes: {mistakes}
- Opening: {opening}

Provide a concise 3-4 sentence review with insightful advice for improvement.
Focus on the most critical issues and specific recommendations.
"""
        )
    
    def review_game(self, game_data):
        # Fill template with actual data
        prompt = self.review_template.format(**game_data)
        review = self.llm.invoke(prompt)
        return review