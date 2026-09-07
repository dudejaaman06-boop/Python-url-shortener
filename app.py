from flask import Flask, request, redirect, send_file
import sqlite3
import random
import string
import os

app = Flask(__name__)

DATABASE = "/tmp/urls.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def generate_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=6))


@app.route("/", methods=["GET", "POST"])
def home():

    init_db()

    if request.method == "GET":
        return send_file("index.html")

    original_url = request.form.get("url")

    if not original_url:
        return "Please enter a URL.", 400

    conn = sqlite3.connect(DATABASE)

    while True:
        code = generate_code()

        existing = conn.execute(
            "SELECT id FROM urls WHERE short_code = ?",
            (code,)
        ).fetchone()

        if not existing:
            break

    conn.execute(
        "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
        (original_url, code)
    )

    conn.commit()
    conn.close()

    short_url = request.host_url + code

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shortly - Result</title>
        <link rel="stylesheet" href="/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">Shortly</div>

                <h1>Your Short URL</h1>

                <div class="result">
                    <a href="{short_url}" target="_blank">
                        {short_url}
                    </a>

                    <button onclick="copyURL()">
                        Copy
                    </button>
                </div>

                <br>

                <a href="/">
                    Shorten another URL
                </a>
            </div>
        </div>

        <script>
            function copyURL() {
                navigator.clipboard.writeText("{short_url}");
                alert("URL copied!");
            }
        </script>
    </body>
    </html>
    """


@app.route("/<code>")
def shorten_redirect(code):

    init_db()

    conn = sqlite3.connect(DATABASE)

    result = conn.execute(
        "SELECT original_url FROM urls WHERE short_code = ?",
        (code,)
    ).fetchone()

    if not result:
        conn.close()
        return "Short URL not found", 404

    conn.execute(
        "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?",
        (code,)
    )

    conn.commit()
    conn.close()

    return redirect(result[0])


@app.route("/style.css")
def stylesheet():
    return send_file("style.css", mimetype="text/css")
