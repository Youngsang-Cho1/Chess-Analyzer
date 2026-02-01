from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv() #load variables from .env file

USER = os.getenv("POSTGRES_USER") 
PASSWORD = os.getenv("POSTGRES_PASSWORD") #pw from .env file
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@db:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL) #connect to postgresql db

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #create a session
Base = declarative_base() #create a base class for models

def init_db():
    from models import Game
    Base.metadata.create_all(bind=engine)