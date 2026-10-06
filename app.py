from flask import Flask, render_template, request, redirect, url_for, session
import random
import os
import mysql.connector

app = Flask(__name__)

# MySQL Database Connection
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "treasure_hunt"),
    port=int(os.getenv("DB_PORT", "3306"))
)
app.secret_key = "treasure-hunt-ca2"


# Home Page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if name == "":
            return render_template(
                "index.html",
                page="start",
                error="Please enter your name."
            )

        session.clear()
        session["player"] = name
        session["score"] = 0

        return redirect(url_for("location"))

    return render_template("index.html", page="start")


# Location Selection
@app.route("/location", methods=["GET", "POST"])
def location():
    if "player" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        choice = request.form.get("location")
        session["location"] = choice

        if choice == "forest":
            session["score"] += 10
            return redirect(url_for("forest"))

        elif choice == "beach":
            session["score"] += 5
            return redirect(url_for("beach"))

    return render_template(
        "index.html",
        page="location",
        player=session["player"],
        score=session["score"]
    )


# Forest
@app.route("/forest", methods=["GET", "POST"])
def forest():
    if "player" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        choice = request.form.get("path")
        session["path"] = choice

        if choice == "cave":
            session["score"] += 10
            session["message"] = "You found an ancient treasure map!"

        elif choice == "bridge":
            session["score"] += 5
            session["message"] = "You found a small golden key!"

        return redirect(url_for("challenge"))

    return render_template(
        "index.html",
        page="forest",
        player=session["player"],
        score=session["score"]
    )


# Beach
@app.route("/beach", methods=["GET", "POST"])
def beach():
    if "player" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        choice = request.form.get("path")
        session["path"] = choice

        if choice == "boat":
            session["score"] += 10
            session["message"] = "You found an old treasure boat!"

        elif choice == "palm":
            session["score"] += 5
            session["message"] = "You found a mysterious treasure clue!"

        return redirect(url_for("challenge"))

    return render_template(
        "index.html",
        page="beach",
        player=session["player"],
        score=session["score"]
    )


# Final Treasure Challenge
@app.route("/challenge", methods=["GET", "POST"])
def challenge():
    if "player" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        guess = request.form.get("guess")

        try:
            guess = int(guess)

            if guess < 1 or guess > 3:
                return render_template(
                    "index.html",
                    page="challenge",
                    player=session["player"],
                    score=session["score"],
                    message="Please enter a number between 1 and 3."
                )

        except ValueError:
            return render_template(
                "index.html",
                page="challenge",
                player=session["player"],
                score=session["score"],
                message="Please enter a valid number."
            )

        treasure_number = random.randint(1, 3)

        if guess == treasure_number:
            session["score"] += 20
            session["result"] = "Congratulations! You found the hidden treasure! 🏆"
            session["won"] = True
        else:
            session["result"] = "The treasure was hidden in another box. Better luck next time!"
            session["won"] = False

        return redirect(url_for("result"))

    return render_template(
        "index.html",
        page="challenge",
        player=session["player"],
        score=session["score"],
        message=session.get("message", "")
    )


# Result Page
@app.route("/result")
def result():
    if "player" not in session:
        return redirect(url_for("index"))

    # Save game result in MySQL
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO players
        (player_name, location, path, score, result)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            session["player"],
            session.get("location", ""),
            session.get("path", ""),
            session["score"],
            "Won" if session.get("won", False) else "Lost"
        )
    )

    db.commit()
    cursor.close()

    return render_template(
        "index.html",
        page="result",
        player=session["player"],
        score=session["score"],
        result=session.get("result", ""),
        won=session.get("won", False)
    )
# Player History
@app.route("/history")
def history():
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM players ORDER BY id DESC")
    players = cursor.fetchall()

    cursor.close()

    return render_template(
        "index.html",
        page="history",
        players=players
    )

# Restart Game
@app.route("/restart")
def restart():
    session.clear()
    return redirect(url_for("index"))


# Start Flask
if __name__ == "__main__":
    app.run(debug=True)
