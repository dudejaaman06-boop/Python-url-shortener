from flask import Flask, render_template, request, redirect
import sqlite3
import random
import string
from urllib.parse import urlparse

app = Flask(__name__, static_folder="static", static_url_path="/static")
DATABASE = "/tmp/urls.db"

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_db()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0
        )
    """)
    connection.commit()
    connection.close()

def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

def valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)

@app.route("/", methods=["GET", "POST"])
def home():
    init_db()
    short_url = None
    error = None

    if request.method == "POST":
        original_url = request.form.get("url", "").strip()

        if not valid_url(original_url):
            error = "Please enter a valid URL."
        else:
            connection = get_db()
            existing = connection.execute(
                "SELECT short_code FROM urls WHERE original_url = ?",
                (original_url,)
            ).fetchone()

            if existing:
                code = existing["short_code"]
            else:
                while True:
                    code = generate_code()
                    existing_code = connection.execute(
                        "SELECT id FROM urls WHERE short_code = ?",
                        (code,)
                    ).fetchone()
                    if existing_code is None:
                        break

                connection.execute(
                    "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                    (original_url, code)
                )
                connection.commit()

            connection.close()
            short_url = request.host_url + code

    return render_template("index.html", short_url=short_url, error=error)

@app.route("/<code>")
def redirect_url(code):
    init_db()
    connection = get_db()

    url_data = connection.execute(
        "SELECT original_url FROM urls WHERE short_code = ?",
        (code,)
    ).fetchone()

    if url_data is None:
        connection.close()
        return "Short URL not found", 404

    connection.execute(
        "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?",
        (code,)
    )
    connection.commit()
    connection.close()

    return redirect(url_data["original_url"])

@app.route("/stats/<code>")
def stats(code):
    init_db()
    connection = get_db()

    data = connection.execute(
        "SELECT original_url, short_code, clicks FROM urls WHERE short_code = ?",
        (code,)
    ).fetchone()

    connection.close()

    if data is None:
        return "Short URL not found", 404

    return {
        "short_code": data["short_code"],
        "original_url": data["original_url"],
        "clicks": data["clicks"]
    }

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
