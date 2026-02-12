from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey, Float, JSON
from database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    pgn = Column(Text)
    fen = Column(String)
    time_control = Column(String)
    end_time = Column(BigInteger) # Unix timestamp
    rated = Column(String)
    time_class = Column(String)
    rules = Column(String)
    opening = Column(String) # Opening used in this game
    
    # White info
    white_username = Column(String)
    white_rating = Column(Integer)
    white_result = Column(String)
    white_accuracy = Column(Float)
    white_move_counts = Column(JSON) # e.g. {"Blunder": 2, "Best": 15, "Brilliant": 1}

    # Black info
    black_username = Column(String)
    black_rating = Column(Integer)
    black_result = Column(String)
    black_accuracy = Column(Float)
    black_move_counts = Column(JSON)

class MoveAnalysis(Base):
    __tablename__ = "move_analysis"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    move_number = Column(Integer)
    move_uci = Column(String)
    move_san = Column(String)
    score = Column(Integer) # Store as centipawns (can be null for mate)
    classification = Column(String)
    color = Column(String) # "white" or "black"
    best_move = Column(String)
    opening = Column(String)
