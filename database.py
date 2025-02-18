import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env file")


def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    print("Executing table creation query...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kids_profile (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            age INTEGER NOT NULL,
            height FLOAT,
            weight FLOAT,
            allergies TEXT,
            symptom_name TEXT,
            parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients(
           id SERIAL PRIMARY KEY,
           ingredient_name VARCHAR(50) NOT NULL,
           is_available BOOLEAN,
           parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE 
    )
    """)
    print("Table creation query executed.")
    conn.commit()
    conn.close()
