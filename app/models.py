from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey
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
    
    # White info
    white_username = Column(String)
    white_rating = Column(Integer)
    white_result = Column(String)

    # Black info
    black_username = Column(String)
    black_rating = Column(Integer)
    black_result = Column(String)

class MoveAnalysis(Base):
    __tablename__ = "move_analysis"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    move_number = Column(Integer)
    move_uci = Column(String)
    score = Column(Integer) # Store as centipawns (can be null for mate)
    classification = Column(String) # Best, Good, Mistake, Blunder, etc.
    best_move = Column(String)

