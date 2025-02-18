"""
This module handles database connections and initialization for the application.

It connects to a PostgreSQL database using `psycopg2` and creates necessary tables
for users, kids' profiles, and ingredients if they do not already exist.
"""

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
    """
        Establishes and returns a connection to the PostgreSQL database.

        Returns:
            psycopg2.connection: A connection object to interact with the database.

        Raises:
            HTTPException: If the connection to the database fails.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as exc:
        # Reraise the original exception with more context
        raise HTTPException(status_code=500, detail="Database connection failed") from exc


def init_db():
    """
        Initializes the database by creating necessary tables if they do not exist.

        The following tables are created:
        - users: Stores user credentials.
        - kids_profile: Stores child health-related data linked to a parent user.
        - ingredients: Stores ingredients and their availability linked to a user.

        This function retrieves a database connection, executes table creation queries,
        commits changes, and then closes the connection.
    """
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
