from flask import Flask, render_template, request, redirect
from upstash_redis import Redis
from urllib.parse import urlparse
import random
import string

app = Flask(__name__, static_folder="public", static_url_path="/static")

# Connect to Upstash Redis using environment variables
redis = Redis.from_env()


def generate_code(length=6):
    """Generate a random 6-character URL code."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def is_valid_url(url):
    """Check whether the URL is valid."""
    parsed = urlparse(url)

    return (
        parsed.scheme in ["http", "https"]
        and bool(parsed.netloc)
    )


@app.route("/", methods=["GET", "POST"])
def home():

    short_url = None
    error = None

    if request.method == "POST":

        original_url = request.form.get("url", "").strip()

        # Validate URL
        if not is_valid_url(original_url):

            error = "Please enter a valid URL."

        else:

            # Generate a unique short code
            while True:

                code = generate_code()

                existing_url = redis.get(f"url:{code}")

                if existing_url is None:
                    break

            # Store URL in Redis
            redis.set(f"url:{code}", original_url)

            # Store click counter
            redis.set(f"clicks:{code}", 0)

            # Generate complete short URL
            short_url = request.host_url + code

    return render_template(
        "index.html",
        short_url=short_url,
        error=error
    )


@app.route("/<code>")
def redirect_url(code):

    # Find original URL
    original_url = redis.get(f"url:{code}")

    if original_url is None:
        return "Short URL not found", 404

    # Increase click count
    redis.incr(f"clicks:{code}")

    # Redirect user
    return redirect(original_url)


@app.route("/stats/<code>")
def statistics(code):

    original_url = redis.get(f"url:{code}")

    if original_url is None:
        return "Short URL not found", 404

    clicks = redis.get(f"clicks:{code}")

    return {
        "short_code": code,
        "original_url": original_url,
        "clicks": clicks
    }


if __name__ == "__main__":
    app.run(debug=True)
