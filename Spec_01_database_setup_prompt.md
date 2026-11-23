I'm building Spendly — a personal expense tracker web app built with Flask + SQLite + Jinja2.

Here is my exact project structure:

Expense_Tracker_Basic/
├── .venv/                       ← local virtual environment (do not touch)
├── database/
│   ├── __init__.py              ← empty, makes database/ a package
│   └── db.py                    ← stub: comments only, no functions yet
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html                ← layout, nav links use url_for('landing'), url_for('login'), url_for('register')
│   ├── landing.html
│   ├── login.html
│   ├── privacy.html
│   ├── register.html
│   └── terms.html
├── .gitignore                   ← currently ignores expense_tracker.db, NOT spendly.db
├── app.py                       ← Flask app, no DB wired up yet
├── LICENSE
├── README.md
├── requirements.txt             ← flask==3.1.3, werkzeug==3.1.6, pytest==8.3.5, pytest-flask==1.3.0
└── Spec_01 … Spec_09 *.md       ← prompt files for each build step

Current state of the files this step touches:

database/db.py contains only these comments:
  get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
  init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
  seed_db()  — inserts sample data for development

app.py contains:
  — app = Flask(__name__)
  — Working routes: GET / (landing), GET /register, GET /login — render templates only
  — Placeholder routes returning plain strings:
      /logout, /profile, /expenses/add,
      /expenses/<int:id>/edit, /expenses/<int:id>/delete
  — app.run(debug=True, port=5001) under if __name__ == "__main__"

Write a spec document for Step 1: Replace the stub in database/db.py with a working SQLite implementation and wire it into app.py.

Save the output as:
  .claude/specs/01-database-setup.md

Create the .claude/specs/ folder if it does not exist.

Rules for the spec itself:
- Output only the Markdown spec document
- No code, no prose outside the spec sections
- Use tables for schema definitions
- Use checkbox lists for Definition of Done
- Number all sections exactly as listed below

Include these 14 sections:

1. Overview
   — What this step does and why it is the foundational step
   — Mention that registration, login/logout, profile, date filtering and
     add/edit/delete expense (Steps 2–9) all depend on it

2. Depends on
   — State that this is the first step with no prerequisites

3. Routes
   — No new routes
   — Existing routes and placeholder routes in app.py remain unchanged
     (same URLs, same endpoint names, same port 5001)

4. Database Schema
   — Table A: users
       id            INTEGER  PRIMARY KEY AUTOINCREMENT
       name          TEXT     NOT NULL
       email         TEXT     NOT NULL UNIQUE
       password_hash TEXT     NOT NULL
       created_at    TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP
   — Table B: expenses
       id            INTEGER  PRIMARY KEY AUTOINCREMENT
       user_id       INTEGER  NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE
       amount        REAL     NOT NULL, CHECK (amount > 0)
       category      TEXT     NOT NULL, CHECK (category IN the 7 fixed categories)
       date          TEXT     NOT NULL — must be stored as YYYY-MM-DD
       description   TEXT     nullable
       created_at    TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP
   — Index: idx_expenses_user_date on expenses(user_id, date)
     (supports the profile page and date filter in later steps)
   — For each column show: name, SQLite type, constraints in a table

5. Functions to Implement (database/db.py)
   — DB_PATH constant: absolute path to spendly.db in the project root,
     built from the location of db.py (not the current working directory),
     so the same file is used no matter where the app is started from
   — get_db(): opens DB_PATH, sets row_factory = sqlite3.Row,
     runs PRAGMA foreign_keys = ON, returns the connection
     (caller is responsible for closing it)
   — init_db(): creates both tables and the index with IF NOT EXISTS,
     commits, closes its connection; safe to call multiple times
   — seed_db(): if the users table already has any rows, return early;
     otherwise insert one demo user
       name: Demo User, email: demo@spendly.com,
       password: demo123 hashed with generate_password_hash
     and 8 sample expenses linked to that user:
       — covering all 7 categories (one category used twice)
       — realistic amounts and short descriptions
       — dates spread across the current month, from day 1 up to today,
         never in the future
     commit once at the end and close the connection

6. Changes to app.py
   — Import get_db, init_db, seed_db from database.db
   — Call init_db() then seed_db() inside `with app.app_context():`
     at module level, right after app is created
     (so it runs for both `python app.py` and `flask run`)
   — DB must be ready before any route is served
   — No other changes to routes or app.run

7. Files to Change
   — database/db.py
   — app.py
   — .gitignore (add spendly.db so the local database is never committed)

8. Files to Create
   — None in source code (spendly.db is generated automatically at runtime)

9. Dependencies
   — No new pip packages; requirements.txt stays unchanged
   — Use sqlite3 and os (stdlib), and werkzeug.security (already installed)

10. Categories (Fixed List)
    — Food, Transport, Bills, Health, Entertainment, Shopping, Other
    — These are the only valid values; list them as a bullet list
    — Note that they are case-sensitive and enforced by the CHECK constraint

11. Rules for Implementation
    — No ORM, no SQLAlchemy
    — Parameterized queries only (? placeholders) — never f-strings or
      string formatting in SQL
    — PRAGMA foreign_keys = ON on every connection
    — Store amount as REAL, not INTEGER
    — Hash passwords with generate_password_hash from werkzeug.security;
      never store plaintext
    — seed_db() must be idempotent (safe to call multiple times)
    — Dates must always be YYYY-MM-DD strings
    — Every function that opens a connection must close it, even on error
      (note: `with sqlite3.connect(...)` commits/rolls back but does NOT close)
    — Keep the code beginner-readable with short docstrings

12. Expected Behavior
    — What get_db(), init_db(), seed_db() must do when called correctly
    — Rows from get_db() can be accessed by column name (row["email"])
    — Running the app twice leaves exactly 1 user and 8 expenses
    — Deleting spendly.db and restarting recreates and reseeds it
    — What database-level constraints must enforce

13. Error Handling Expectations
    — Duplicate email insert → sqlite3.IntegrityError (UNIQUE constraint failed)
    — Expense with non-existent user_id → sqlite3.IntegrityError (FOREIGN KEY constraint failed)
    — Amount ≤ 0 or category outside the list → sqlite3.IntegrityError (CHECK constraint failed)
    — Invalid SQL → let sqlite3 errors propagate with clear messages; do not
      silently swallow exceptions
    — On failure inside init_db()/seed_db(), roll back and close the connection

14. Definition of Done
    — Checkbox list:
      - spendly.db is created in the project root on app startup
      - Both tables and the index exist with the correct schema and constraints
      - Demo user demo@spendly.com exists with a hashed password (not "demo123")
      - 8 sample expenses exist covering all 7 categories, dated within the current month and not in the future
      - Restarting the app does not duplicate seed data
      - App starts with `python app.py` on port 5001 without errors
      - Existing pages (/, /login, /register) still render
      - Foreign key enforcement works (invalid user_id insert is rejected)
      - CHECK constraints reject invalid amount and category
      - All queries use parameterized SQL
      - spendly.db is listed in .gitignore
