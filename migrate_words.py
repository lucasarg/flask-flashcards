import json
from app import db, Word, app

with open("flashcards.json", "r", encoding="utf-8") as file:
    flashcards = json.load(file)

with app.app_context():
    for card in flashcards:
        new_word = Word(
            english=card["english"],
            translation=card["french"],  # Change based on selected language
            language="french",           # Set target language
            level=card["level"]
        )
        db.session.add(new_word)

    db.session.commit()
    print("Data migration complete!")