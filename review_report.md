# Code Review Report — Spendly

**Scope:** `app.py`, `database/db.py`, `templates/*.html`, `static/css/*.css`, `static/js/main.js`, `requirements.txt`, `.gitignore`
**Stack:** Flask 3.1.3, Werkzeug 3.1.6, SQLite (`sqlite3`), Jinja2

## Summary

The core flow works: landing page, registration, login, logout, and the Terms, Privacy, and "See how it works" pages. The main gaps are security (hardcoded secret, no CSRF protection, no password rules, a seeded demo account) and missing tests. Most of the app is still placeholders, so several issues will matter more once the expense features land.

## Findings

### High

1. **Hardcoded Flask secret key** — `app.py:18`
   `app.secret_key = "spendly-dev-secret"` is committed to the repo. Anyone with the code can forge session cookies. Load it from an environment variable, and generate a random fallback for local development.

2. **Debug mode enabled in the run block** — `app.py:126`
   `app.run(debug=True, ...)` exposes the Werkzeug debugger, which allows arbitrary code execution if the app is reachable from a network. Keep it for local development only, and read the setting from an environment variable.

3. **No CSRF protection on POST forms** — `templates/register.html`, `templates/login.html`
   Forms post without a CSRF token, and the app doesn't use Flask-WTF or similar. A malicious page could submit a login or registration on a user's behalf. Add CSRF tokens before the expense forms (Steps 7–9) are built.

4. **Known demo account created on every fresh database** — `database/db.py` (`seed_db`)
   `demo@spendly.com` / `demo123` is inserted whenever the users table is empty. If the app is deployed without a database file, that account is public. Gate seeding behind a development flag, or remove it for production.

### Medium

5. **Password rules are not enforced on the server** — `app.py:34–62`, `templates/register.html`
   The form says "Min. 8 characters", but the route only checks that fields are non-empty and that the passwords match. Enforce the minimum length (and ideally a basic strength check) on the server, since the HTML `required` attribute is easy to bypass.

6. **No email format validation** — `app.py:42`
   The email is only stripped and lowercased. The browser's `type="email"` check can be bypassed. Validate the format on the server.

7. **No login protection on routes** — `app.py:105–122`
   `session["user_id"]` is set on login, but nothing reads it. The placeholder routes for profile and expenses don't check it, and the landing page and nav look the same whether or not the user is signed in. Add a `login_required` decorator when Step 4 begins, and show signed-in navigation.

8. **Import-time side effects** — `app.py:20–22`
   `init_db()` and `seed_db()` run at module import, so importing `app` in tests or other scripts touches `spendly.db`. Move them into an app factory or a CLI command.

9. **No automated tests** — `requirements.txt` lists `pytest` and `pytest-flask`, but the repo has no test files or test configuration.
   Add tests for registration, login, logout, and the database helpers before building more features.

### Low

10. **Unused CSS from the old hero** — `static/css/style.css` (`.hero`, `.hero-*`, `.mock-*` rules, roughly lines 126–260)
    The hero section now uses the `.lp-*` classes in `static/css/landing.css`. The old rules are probably dead code, so remove them after confirming nothing else uses them.

11. **Hardcoded "Last updated" date** — `templates/terms.html`, `templates/privacy.html`
    Both say "November 2026" as plain text. Update the date whenever the policy changes, or pull it from a single setting.

12. **Success messages use the error style** — `templates/login.html`, `templates/register.html`
    Flash messages render in the `auth-error` class regardless of category, so "Account created" looks like an error. Use the category to pick the class.

13. **Empty JavaScript file** — `static/js/main.js`
    The file only has a comment. The modal's JavaScript lives inline in `templates/landing.html`. Move it into `main.js` or `landing.js` once the code grows.

14. **Placeholder routes return plain text** — `app.py:105–122`
    This is expected for the current step, but these routes need real handlers before any user-facing work is complete.

15. **Hardcoded demo video URL** — `templates/landing.html`
    The "See how it works" modal uses a placeholder YouTube URL, as you requested. Replace it before launch.

## What looks good

- Passwords are hashed with Werkzeug (`generate_password_hash` / `check_password_hash`).
- The login error doesn't reveal whether the email or the password was wrong (`app.py:81`).
- SQL queries use parameter placeholders (`?`), so there is no SQL injection in the current code.
- The `expenses` table has a CHECK constraint on amount and category, and a foreign key with cascade delete.
- The database path is resolved relative to the project root, not the working directory.
- The modal closes on Escape, backdrop click, and the close button. It also clears the iframe `src` so the video stops.

## Suggested order of fixes

1. Items 1–4 (secret key, debug flag, CSRF, demo account), before any deployment.
2. Items 5–7 (validation and login checks), before Step 4 (profile page).
3. Item 9 (tests), alongside each new feature.
4. Items 8 and 10–13 (cleanup), when convenient.
