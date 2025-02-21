from flask import Flask, render_template, request, session, Response,redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
import json
import random
import uuid
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
        print(f"🌍 Language: {session['target_language']} | 📖 Level: {session['level']}")

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
    # Get the user's selected language and level
    selected_language = session.get("target_language", "french")  # Default to French
    selected_level = session.get("level", 1)  # Default to level 1

    # Query only words that match the language and level
    remaining_words = Word.query.filter(
        ~Word.id.in_(known_word_ids),
        Word.language == selected_language,
        Word.level == selected_level
    ).all()

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




@app.route("/download_csv")
def download_csv():
    """Export known & unknown words as a CSV file."""
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

    data = pd.DataFrame(known_words, columns=["English", "Translation"])
    data["Status"] = "✅ Known"
    data_unknown = pd.DataFrame(unknown_words, columns=["English", "Translation"])
    data_unknown["Status"] = "❌ Unknown"
    data = pd.concat([data, data_unknown])

    csv_data = data.to_csv(index=False)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=word_list.csv"},
    )

@app.route("/download_pdf")
def download_pdf():
    """Export known & unknown words as a PDF file."""
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

    filename = f"user_{user_id}_words.pdf"
    pdf = canvas.Canvas(filename, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    y_position = 750  # Start position for text

    pdf.drawString(100, y_position, "✅ Known Words:")
    y_position -= 20

    for eng, trans in known_words:
        pdf.drawString(100, y_position, f"{eng} - {trans}")
        y_position -= 15

    y_position -= 30
    pdf.drawString(100, y_position, "❌ Unknown Words:")
    y_position -= 20

    for eng, trans in unknown_words:
        pdf.drawString(100, y_position, f"{eng} - {trans}")
        y_position -= 15

    pdf.save()

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
