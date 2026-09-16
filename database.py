"""
database.py
SQLite persistence layer for the Recipe Management System.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recipes.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            cuisine TEXT,
            ingredients TEXT NOT NULL,      -- comma separated
            instructions TEXT NOT NULL,
            prep_time INTEGER DEFAULT 0,    -- minutes
            cook_time INTEGER DEFAULT 0,    -- minutes
            servings INTEGER DEFAULT 4,
            calories INTEGER,
            tags TEXT,                      -- comma separated
            cuisine_predicted INTEGER DEFAULT 0,  -- 1 if cuisine was AI-predicted
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_recipe(title, cuisine, ingredients, instructions, prep_time, cook_time,
                servings, calories, tags, cuisine_predicted=0):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO recipes (title, cuisine, ingredients, instructions, prep_time,
                              cook_time, servings, calories, tags, cuisine_predicted, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, cuisine, ingredients, instructions, prep_time, cook_time,
          servings, calories, tags, cuisine_predicted, datetime.utcnow().isoformat()))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_recipe(recipe_id, **fields):
    if not fields:
        return
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [recipe_id]
    conn.execute(f"UPDATE recipes SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_recipe(recipe_id):
    conn = get_connection()
    conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def get_recipe(recipe_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_recipes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM recipes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_recipes():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) as c FROM recipes").fetchone()["c"]
    conn.close()
    return n
