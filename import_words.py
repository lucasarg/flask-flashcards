from app import db, Word, app

with app.app_context():
    words = [
        # A1 Level
        {"english": "apple", "translation": "pomme", "language": "french", "level": 1},
        {"english": "house", "translation": "maison", "language": "french", "level": 1},
        {"english": "car", "translation": "voiture", "language": "french", "level": 1},
        {"english": "happy", "translation": "heureux", "language": "french", "level": 1},

        {"english": "apple", "translation": "manzana", "language": "spanish", "level": 1},
        {"english": "house", "translation": "casa", "language": "spanish", "level": 1},
        {"english": "car", "translation": "coche", "language": "spanish", "level": 1},
        {"english": "happy", "translation": "feliz", "language": "spanish", "level": 1},

        {"english": "apple", "translation": "Apfel", "language": "german", "level": 1},
        {"english": "house", "translation": "Haus", "language": "german", "level": 1},
        {"english": "car", "translation": "Auto", "language": "german", "level": 1},
        {"english": "happy", "translation": "glücklich", "language": "german", "level": 1},

        {"english": "apple", "translation": "mela", "language": "italian", "level": 1},
        {"english": "house", "translation": "casa", "language": "italian", "level": 1},
        {"english": "car", "translation": "macchina", "language": "italian", "level": 1},
        {"english": "happy", "translation": "felice", "language": "italian", "level": 1},

        {"english": "apple", "translation": "maçã", "language": "portuguese", "level": 1},
        {"english": "house", "translation": "casa", "language": "portuguese", "level": 1},
        {"english": "car", "translation": "carro", "language": "portuguese", "level": 1},
        {"english": "happy", "translation": "feliz", "language": "portuguese", "level": 1},

        # A2 Level
        {"english": "train", "translation": "train", "language": "french", "level": 2},
        {"english": "delicious", "translation": "délicieux", "language": "french", "level": 2},

        {"english": "train", "translation": "tren", "language": "spanish", "level": 2},
        {"english": "delicious", "translation": "delicioso", "language": "spanish", "level": 2},

        {"english": "train", "translation": "Zug", "language": "german", "level": 2},
        {"english": "delicious", "translation": "köstlich", "language": "german", "level": 2},

        {"english": "train", "translation": "treno", "language": "italian", "level": 2},
        {"english": "delicious", "translation": "delizioso", "language": "italian", "level": 2},

        {"english": "train", "translation": "trem", "language": "portuguese", "level": 2},
        {"english": "delicious", "translation": "delicioso", "language": "portuguese", "level": 2},

        # B1 Level
        {"english": "experience", "translation": "expérience", "language": "french", "level": 3},
        {"english": "amazing", "translation": "incroyable", "language": "french", "level": 3},

        {"english": "experience", "translation": "experiencia", "language": "spanish", "level": 3},
        {"english": "amazing", "translation": "increíble", "language": "spanish", "level": 3},

        {"english": "experience", "translation": "Erfahrung", "language": "german", "level": 3},
        {"english": "amazing", "translation": "erstaunlich", "language": "german", "level": 3},

        {"english": "experience", "translation": "esperienza", "language": "italian", "level": 3},
        {"english": "amazing", "translation": "sorprendente", "language": "italian", "level": 3},

        {"english": "experience", "translation": "experiência", "language": "portuguese", "level": 3},
        {"english": "amazing", "translation": "surpreendente", "language": "portuguese", "level": 3},
    ]

    for word in words:
        new_word = Word(
            english=word["english"],
            translation=word["translation"],
            language=word["language"],
            level=word["level"]
        )
        db.session.add(new_word)

    db.session.commit()
    print("✅ Expanded word list imported successfully!")
