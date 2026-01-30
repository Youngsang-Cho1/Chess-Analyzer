from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 

import os
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@db:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    with engine.connect() as connection:
        print("DB was connected successfully")
except Exception as e:
    print(f"Failed to connect to DB: {e}")