from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
import json
import random
import uuid
import os

# Initialize Flask
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(50), nullable=False)
    translation = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey("user.user_id"), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"), nullable=False)
    known = db.Column(db.Boolean, nullable=False)

# Initialize Database
with app.app_context():
    db.create_all()




# Load flashcards into memory
with open("flashcards.json", "r", encoding="utf-8") as file:
    FLASHCARDS = json.load(file)






# 🌍 Arriving Page (First-Time Setup)
@app.route("/", methods=["GET", "POST"])
def home():
    """Página de inicio donde el usuario selecciona idioma y nivel."""
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

    user_id = session["user_id"]

    # Si el usuario no está en la base de datos, lo añadimos
    if not User.query.filter_by(user_id=user_id).first():
        db.session.add(User(user_id=user_id))
        db.session.commit()

    if request.method == "POST":
        # Guardamos idioma y nivel en la sesión
        session["target_language"] = request.form["target_language"]
        session["level"] = int(request.form["level"])
        return redirect(url_for("flashcards"))

    return render_template("home.html")


# 🃏 Flashcard Page
@app.route("/flashcards", methods=["GET", "POST"])
def flashcards():
    """Show flashcards for the user."""
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

    user_id = session["user_id"]

    if request.method == "POST":
        word_id = request.form.get("word_id")
        action = request.form.get("action")

        if word_id and action:
            known = action == "known"
            progress_entry = Progress(user_id=user_id, word_id=int(word_id), known=known)
            db.session.add(progress_entry)
            db.session.commit()

    # Retrieve words user hasn't marked as known
    known_word_ids = [p.word_id for p in Progress.query.filter_by(user_id=user_id, known=True).all()]
    remaining_words = Word.query.filter(~Word.id.in_(known_word_ids)).all()

    # 🔹 DEBUG: Print the list of remaining words
    print("Remaining words:", remaining_words)

    if not remaining_words:
        db.session.query(Progress).filter_by(user_id=user_id).delete()
        db.session.commit()
        remaining_words = Word.query.all()

    if remaining_words:
        word = random.choice(remaining_words)
        print("Selected word:", word.english, "-", word.translation)  # 🔹 DEBUG: Check selected word
    else:
        word = None
        print("⚠️ No words available!")

    print("🔹 Sending to template:", word)  # Debugging output
    return render_template("flashcards.html", word=word)




@app.route("/download")
def download_list():
    user_id = session.get("user_id")

    if not user_id:
        return "No progress found.", 404

    known_words = (
        db.session.query(Word.english, Word.translation)
        .join(Progress, Progress.word_id == Word.id)
        .filter(Progress.user_id == user_id, Progress.known == True)
        .all()
    )

    unknown_words = (
        db.session.query(Word.english, Word.translation)
        .join(Progress, Progress.word_id == Word.id)
        .filter(Progress.user_id == user_id, Progress.known == False)
        .all()
    )

    filename = f"user_{user_id}_words.txt"
    with open(filename, "w") as file:
        file.write("✅ Known Words:\n")
        for eng, trans in known_words:
            file.write(f"{eng} - {trans}\n")

        file.write("\n❌ Unknown Words:\n")
        for eng, trans in unknown_words:
            file.write(f"{eng} - {trans}\n")

    return send_file(filename, as_attachment=True)


# 📖 Main Menu
@app.route("/menu")
def menu():
    return render_template("menu.html")

# 📊 Progress Page
@app.route("/progress")
def progress():
    """Muestra el progreso del usuario con datos de SQLite."""
    user_id = session.get("user_id")

    if not user_id:
        return "No progress found.", 404

    known_count = Progress.query.filter_by(user_id=user_id, known=True).count()
    unknown_count = Progress.query.filter_by(user_id=user_id, known=False).count()

    total = max(known_count + unknown_count, 1)  # Para evitar divisiones por 0

    return render_template("progress.html", known_count=known_count, unknown_count=unknown_count, total=total)


@app.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset the user's progress in the database"""
    user_id = session.get("user_id")

    if user_id:
        db.session.query(Progress).filter_by(user_id=user_id).delete()
        db.session.commit()

    return redirect(url_for("progress"))



# 📋 Word List Page
@app.route("/words")
def words():
    """Fetch known and unknown words from the database."""
    user_id = session.get("user_id")

    if not user_id:
        return "No progress found.", 404

    known_words = (
        db.session.query(Word.english, Word.translation)
        .join(Progress, Progress.word_id == Word.id)
        .filter(Progress.user_id == user_id, Progress.known == True)
        .all()
    )

    unknown_words = (
        db.session.query(Word.english, Word.translation)
        .join(Progress, Progress.word_id == Word.id)
        .filter(Progress.user_id == user_id, Progress.known == False)
        .all()
    )

    return render_template("words.html", known_words=known_words, unknown_words=unknown_words)


# ⚙️ Settings Page (Change Language/Level)
@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Permite al usuario cambiar su idioma y nivel."""
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("home"))

    if request.method == "POST":
        # Guardamos el idioma y nivel en la sesión
        session["target_language"] = request.form["target_language"]
        session["level"] = int(request.form["level"])
        return redirect(url_for("flashcards"))

    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)
