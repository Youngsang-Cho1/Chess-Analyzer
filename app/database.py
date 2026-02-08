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

import time

def init_db():
    from models import Game
    
    # DB ready check
    retries = 30
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            print("Database connected and initialized successfully.", flush=True)
            return
        except Exception as e:
            retries -= 1
            print(f"Database unavailable, waiting 1s... ({retries} retries) Error: {e}", flush=True)
            time.sleep(1)
            
    print("Could not connect to database after 30s.", flush=True)
    raise Exception("Database connection failed")