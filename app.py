# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Player
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# берем URL из окружения (docker-compose) или дефолтно подключаемся к db сервису
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "postgresql://user:password@db:5432/mygame"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    player_id = session.get("player_id")
    player = None
    other_players = []
    if player_id:
        player = Player.query.get(player_id)
        if player:
            other_players = Player.query.filter(Player.id != player_id).all()
    # show_auth True — показать оверлей логина/регистрации
    return render_template("index.html", player=player, other_players=other_players, show_auth=(player is None))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        race = request.form["race"]
        player_class = request.form["player_class"]

        # базовые параметры
        health = 100
        energy = 100 if player_class in ["Воин", "Разбойник"] else None
        mana = 100 if player_class == "Маг" else None

        new_player = Player(
            name=name,
            race=race,
            player_class=player_class,
            health=health,
            energy=energy,
            mana=mana
        )
        db.session.add(new_player)
        db.session.commit()

        # логиним игрока
        session["player_id"] = new_player.id
        return redirect(url_for("index"))

    # GET: можно передать ?name= заранее (при редиректе из login)
    name = request.args.get("name", "")
    return render_template("register.html", name=name)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("index"))

    player = Player.query.filter_by(name=name).first()
    if not player:
        # если не найден — перейти на регистрацию и подставить имя
        return redirect(url_for("register", name=name))

    session["player_id"] = player.id
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    player_id = session.get("player_id")
    if not player_id:
        return redirect(url_for("register"))

    player = Player.query.get(player_id)
    return render_template("profile.html", player=player)


if __name__ == "__main__":
    # не вызываем db.create_all() — мы будем использовать миграции
    app.run(host="0.0.0.0", port=5000)
