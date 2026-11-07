"""
database.py
SQLite persistence layer for the Sage & Stamp AI Recipe Management System.
Features:
- Cultural & dietary safety validation: Strictly checks and prevents beef, steak,
  pork, and offensive ingredients.
- CRUD methods for recipes.
- User authentication, profiles, saved favorites, and cooking history.
"""
import sqlite3
import os

import re
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "recipes.db")

# Vercel Serverless environment fallback: copy pre-seeded SQLite DB to /tmp if read-only
if os.environ.get("VERCEL") or (os.name != "nt" and not os.access(os.path.dirname(DB_PATH) or ".", os.W_OK)):
    import shutil
    TMP_DIR = "/tmp"
    TMP_DB = os.path.join(TMP_DIR, "recipes.db")
    if os.path.exists(DB_PATH) and not os.path.exists(TMP_DB):
        try:
            os.makedirs(TMP_DIR, exist_ok=True)
            shutil.copy2(DB_PATH, TMP_DB)
        except Exception:
            pass
    if os.path.exists(TMP_DB):
        DB_PATH = TMP_DB

# Prohibited items check (India dietary & cultural compliance)
PROHIBITED_TERMS = [
    r"\bbeef\b",
    r"\bsteak\b",
    r"\bcow\b",
    r"\bveal\b",
    r"\bpork\b",
    r"\bbacon\b",
    r"\bham\b",
    r"\blard\b",
    r"\bpancetta\b",
    r"\bprosciutto\b"
]


def check_dietary_compliance(title: str, ingredients: str):
    """
    Validates that a dish does not contain beef, steak, pork, or culturally harmful ingredients.
    Returns (is_compliant, reason_string).
    """
    text_to_check = f"{title} {ingredients}".lower()
    for pattern in PROHIBITED_TERMS:
        if re.search(pattern, text_to_check):
            term = pattern.replace(r"\b", "")
            return False, f"Notice: Recipes containing '{term}' are not permitted in Sage & Stamp (India-Compliant Edition)."
    return True, ""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    except Exception:
        pass
    conn = get_connection()
    # Recipes table
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
    # Users table for profile, signup, login, palate modeling
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            palate TEXT DEFAULT 'North Indian & Mediterranean',
            diet_pref TEXT DEFAULT 'Vegetarian',
            spicy_affinity INTEGER DEFAULT 49,
            healthy_affinity INTEGER DEFAULT 100,
            quick_affinity INTEGER DEFAULT 100,
            saved_recipes TEXT DEFAULT '',   -- comma separated recipe ids
            cooked_count INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    conn.commit()
    # If database is fresh or empty in /tmp serverless environment, seed recipes
    cur = conn.execute("SELECT COUNT(*) as c FROM recipes")
    count = cur.fetchone()["c"]
    conn.close()
    seed_default_user()
    if count == 0:
        try:
            import seed_data
            seed_data.seed_all()
        except Exception:
            pass


def seed_default_user():
    """Seeds the initial user 'Anshul' if not present so dashboard renders with complete modeled palate."""
    conn = get_connection()
    existing = conn.execute("SELECT * FROM users WHERE email = ?", ("anshul@example.com",)).fetchone()
    if not existing:
        pwd_hash = generate_password_hash("password123")
        conn.execute("""
            INSERT INTO users (name, email, password_hash, palate, diet_pref, spicy_affinity,
                               healthy_affinity, quick_affinity, saved_recipes, cooked_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Anshul Bhilare", "anshul@example.com", pwd_hash, "North Indian & Mediterranean", "Vegetarian",
              49, 100, 100, "", 1, datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()


# ------------------------------------------------------------------
# User Authentication & Profile Methods
# ------------------------------------------------------------------
def create_user(name, email, password, palate="North Indian & Mediterranean", diet_pref="Vegetarian"):
    email_clean = email.strip().lower()
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email_clean,)).fetchone()
    if existing:
        conn.close()
        raise ValueError(f"An account with email '{email_clean}' already exists. Please log in.")

    pwd_hash = generate_password_hash(password)
    cur = conn.execute("""
        INSERT INTO users (name, email, password_hash, palate, diet_pref, spicy_affinity,
                           healthy_affinity, quick_affinity, saved_recipes, cooked_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name.strip(), email_clean, pwd_hash, palate.strip(), diet_pref.strip(), 50, 100, 100, "", 0, datetime.utcnow().isoformat()))
    conn.commit()
    new_user_id = cur.lastrowid
    conn.close()
    return new_user_id


def verify_user(email, password):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    if not row:
        return None
    user = dict(row)
    if check_password_hash(user["password_hash"], password):
        return user
    return None


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_profile(user_id, **fields):
    if not fields:
        return
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def toggle_save_recipe(user_id, recipe_id):
    user = get_user_by_id(user_id)
    if not user:
        return False, 0
    saved = [r.strip() for r in user["saved_recipes"].split(",") if r.strip()]
    r_str = str(recipe_id)
    if r_str in saved:
        saved.remove(r_str)
        is_saved = False
    else:
        saved.append(r_str)
        is_saved = True

    new_saved_str = ",".join(saved)
    update_user_profile(user_id, saved_recipes=new_saved_str)
    return is_saved, len(saved)


def increment_cooked(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return 1
    new_count = user["cooked_count"] + 1
    update_user_profile(user_id, cooked_count=new_count)
    return new_count


# ------------------------------------------------------------------
# Recipe CRUD Methods
# ------------------------------------------------------------------
def add_recipe(title, cuisine, ingredients, instructions, prep_time, cook_time,
               servings, calories, tags, cuisine_predicted=0):
    is_valid, msg = check_dietary_compliance(title, ingredients)
    if not is_valid:
        raise ValueError(msg)

    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO recipes (title, cuisine, ingredients, instructions, prep_time,
                              cook_time, servings, calories, tags, cuisine_predicted, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title.strip(), (cuisine or "Other").strip(), ingredients.strip(), instructions.strip(),
          prep_time, cook_time, servings, calories, tags.strip() if tags else "",
          cuisine_predicted, datetime.utcnow().isoformat()))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_recipe(recipe_id, **fields):
    if not fields:
        return

    title = fields.get("title", "")
    ingredients = fields.get("ingredients", "")
    if title or ingredients:
        curr = get_recipe(recipe_id)
        check_t = title or (curr["title"] if curr else "")
        check_i = ingredients or (curr["ingredients"] if curr else "")
        is_valid, msg = check_dietary_compliance(check_t, check_i)
        if not is_valid:
            raise ValueError(msg)

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
    rows = conn.execute("SELECT * FROM recipes ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recipes_by_cuisine(cuisine):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM recipes WHERE LOWER(cuisine) = LOWER(?) ORDER BY id DESC", (cuisine,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_recipes():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) as c FROM recipes").fetchone()["c"]
    conn.close()
    return n
