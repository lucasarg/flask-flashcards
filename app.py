import json
import random
import uuid
import time
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load flashcards into memory at startup
with open("flashcards.json", "r", encoding="utf-8") as file:
    FLASHCARDS = json.load(file)

# Cache user progress in memory to reduce file reads
progress_cache = None
last_load_time = 0
LOAD_INTERVAL = 10  # Refresh progress data every 10 seconds

def load_progress():
    global progress_cache, last_load_time
    if time.time() - last_load_time > LOAD_INTERVAL or progress_cache is None:
        try:
            with open("progress.json", "r", encoding="utf-8") as file:
                progress_cache = json.load(file)
                last_load_time = time.time()
        except FileNotFoundError:
            progress_cache = {}
    return progress_cache

def save_progress(progress):
    global progress_cache
    progress_cache = progress  # Update cache
    with open("progress.json", "w", encoding="utf-8") as file:
        json.dump(progress, file, indent=4)

@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())  # Assign unique user ID

    user_id = session["user_id"]
    progress = load_progress()

    if user_id not in progress:
        progress[user_id] = {"known_words": [], "unknown_words": []}

    user_progress = progress[user_id]

    if request.method == "POST":
        word_english = request.form.get("word_english")
        action = request.form.get("action")

        if action == "known" and word_english not in user_progress["known_words"]:
            user_progress["known_words"].append(word_english)

        elif action == "unknown" and word_english not in user_progress["unknown_words"]:
            user_progress["unknown_words"].append(word_english)

        # Only update session if progress changes
        session.modified = True
        save_progress(progress)

    remaining_words = [
        word for word in FLASHCARDS if word["english"] not in user_progress["known_words"]
    ]

    if not remaining_words:
        user_progress["known_words"] = []
        save_progress(progress)
        remaining_words = FLASHCARDS

    word = random.choice(remaining_words)

    return render_template("index.html", word=word, known_count=len(user_progress["known_words"]))

@app.route("/reset", methods=["POST"])
def reset_progress():
    user_id = session.get("user_id")

    if user_id:
        progress = load_progress()
        if user_id in progress:
            progress[user_id] = {"known_words": [], "unknown_words": []}
            save_progress(progress)

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
