import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

# Absolute path to spendly.db in the project root, independent of the CWD.
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spendly.db"
)

# The only valid expense categories (case-sensitive, enforced by CHECK).
CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)


def get_db():
    """Open a connection to spendly.db with dict-style rows and FK enforcement.

    The caller is responsible for closing the connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the users and expenses tables and the index. Safe to call repeatedly."""
    conn = get_db()
    try:
        category_list = ", ".join(f"'{c}'" for c in CATEGORIES)
        conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount      REAL    NOT NULL CHECK (amount > 0),
                category    TEXT    NOT NULL CHECK (category IN ({category_list})),
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses (user_id, date);
            """
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_by_email(email):
    """Return the users row matching this email, or None if not found."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def create_user(name, email, password):
    """Insert a new user with a hashed password and return the new user's id.

    Raises sqlite3.IntegrityError if the email is already registered.
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_db():
    """Insert a demo user and 8 sample expenses if the users table is empty."""
    conn = get_db()
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()["id"]

        # Day-of-month offsets; each is clamped to today's day so no date is
        # in the future.
        today = date.today()
        samples = [
            (1, 1450.00, "Food", "Weekly groceries"),
            (3, 320.00, "Transport", "Metro card recharge"),
            (5, 2100.00, "Bills", "Electricity bill"),
            (8, 499.00, "Health", "Gym membership"),
            (11, 899.00, "Entertainment", "Movie tickets and snacks"),
            (14, 1875.50, "Shopping", "New running shoes"),
            (17, 260.00, "Food", "Dinner with friends"),
            (19, 150.00, "Other", "Birthday gift contribution"),
        ]
        rows = [
            (
                user_id,
                amount,
                category,
                date(today.year, today.month, min(day, today.day)).isoformat(),
                description,
            )
            for day, amount, category, description in samples
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
