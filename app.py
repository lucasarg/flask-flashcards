import json
import random
import uuid
import time
from flask import Flask, render_template, request, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load flashcards into memory
with open("flashcards.json", "r", encoding="utf-8") as file:
    FLASHCARDS = json.load(file)

# Cache user progress in memory
progress_cache = None
last_load_time = 0
LOAD_INTERVAL = 10

def load_progress():
    """Load user progress from JSON with caching"""
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
    """Save user progress to JSON file"""
    global progress_cache
    progress_cache = progress
    with open("progress.json", "w", encoding="utf-8") as file:
        json.dump(progress, file, indent=4)

# 🌍 Arriving Page (First-Time Setup)
@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())  # Assign unique user ID

    user_id = session["user_id"]
    progress = load_progress()

    if request.method == "POST":
        progress[user_id] = {
            "known_words": [],
            "unknown_words": [],
            "target_language": request.form["target_language"],
            "level": int(request.form["level"])
        }
        save_progress(progress)
        return redirect(url_for("flashcards"))

    return render_template("home.html")

# 🃏 Flashcard Page
@app.route("/flashcards", methods=["GET", "POST"])
def flashcards():
    user_id = session.get("user_id")
    progress = load_progress()

    if user_id not in progress:
        return redirect(url_for("home"))

    user_progress = progress[user_id]
    
    if request.method == "POST":
        word_english = request.form.get("word_english")
        action = request.form.get("action")

        if action == "known" and word_english not in user_progress["known_words"]:
            user_progress["known_words"].append(word_english)

        elif action == "unknown" and word_english not in user_progress["unknown_words"]:
            user_progress["unknown_words"].append(word_english)

        save_progress(progress)

    remaining_words = [
        word for word in FLASHCARDS if word["english"] not in user_progress["known_words"]
    ]

    if not remaining_words:
        user_progress["known_words"] = []
        save_progress(progress)
        remaining_words = FLASHCARDS

    word = random.choice(remaining_words)
    target_language = user_progress["target_language"]
    translation = word[target_language]

    return render_template("flashcards.html", word=word, translation=translation)

# 📖 Main Menu
@app.route("/menu")
def menu():
    return render_template("menu.html")

# 📊 Progress Page
@app.route("/progress")
def progress():
    user_id = session.get("user_id")
    progress = load_progress()

    if not user_id or user_id not in progress:
        return "No progress found.", 404

    user_progress = progress[user_id]
    known_count = len(user_progress.get("known_words", []))
    unknown_count = len(user_progress.get("unknown_words", []))
    
    # Ensure total is at least 1 to prevent division errors
    total = max(known_count + unknown_count, 1)

    return render_template("progress.html", known_count=known_count, unknown_count=unknown_count, total=total)


# 📋 Word List Page
@app.route("/words")
def words():
    user_id = session.get("user_id")
    progress = load_progress()

    if not user_id or user_id not in progress:
        return "No progress found.", 404

    user_progress = progress[user_id]
    known_words = user_progress.get("known_words", [])
    unknown_words = user_progress.get("unknown_words", [])

    return render_template("words.html", known_words=known_words, unknown_words=unknown_words)

# ⚙️ Settings Page (Change Language/Level)
@app.route("/settings", methods=["GET", "POST"])
def settings():
    user_id = session.get("user_id")
    progress = load_progress()

    if not user_id or user_id not in progress:
        return redirect(url_for("home"))

    if request.method == "POST":
        progress[user_id]["target_language"] = request.form["target_language"]
        progress[user_id]["level"] = int(request.form["level"])
        save_progress(progress)
        return redirect(url_for("flashcards"))

    return render_template("settings.html")

if __name__ == "__main__":
    app.run(debug=True)
