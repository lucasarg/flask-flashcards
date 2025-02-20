import json
import random
import uuid  # Generate unique user IDs
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session tracking

# Load flashcards from JSON
def load_flashcards():
    with open("flashcards.json", "r", encoding="utf-8") as file:
        return json.load(file)

# Load user progress
def load_progress():
    try:
        with open("progress.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save user progress
def save_progress(progress):
    with open("progress.json", "w", encoding="utf-8") as file:
        json.dump(progress, file, indent=4)

@app.route("/", methods=["GET", "POST"])
def home():
    # Ensure the user has a unique ID
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())  # Generate a random ID

    user_id = session["user_id"]
    flashcards = load_flashcards()
    progress = load_progress()

    # Initialize progress for new users
    if user_id not in progress:
        progress[user_id] = {"known_words": [], "unknown_words": []}

    user_progress = progress[user_id]

    # Handle user input
    if request.method == "POST":
        word_english = request.form.get("word_english")
        action = request.form.get("action")

        if action == "known" and word_english not in user_progress["known_words"]:
            user_progress["known_words"].append(word_english)

        elif action == "unknown" and word_english not in user_progress["unknown_words"]:
            user_progress["unknown_words"].append(word_english)

        # Save updated progress
        save_progress(progress)

    # Filter out known words
    remaining_words = [
        word for word in flashcards if word["english"] not in user_progress["known_words"]
    ]

    # If all words are known, reset progress
    if not remaining_words:
        user_progress["known_words"] = []
        save_progress(progress)
        remaining_words = flashcards

    # Pick a random word
    word = random.choice(remaining_words)

    return render_template("index.html", word=word, known_count=len(user_progress["known_words"]))

if __name__ == "__main__":
    app.run(debug=True)
