import os
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Player
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/avatars'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Настройка базы данных
db_url = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/mygame")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Явная инициализация базы
db.init_app(app)
with app.app_context():
    db.create_all()
    print("Таблицы успешно созданы или уже существуют")

# --------------------------------
# Маршруты
# --------------------------------
@app.route("/")
def index():
    player_id = session.get("player_id")
    player = None
    other_players = []

    if player_id:
        player = Player.query.get(player_id)
        if player:
            other_players = Player.query.filter(Player.id != player_id).all()

    return render_template("index.html", player=player, other_players=other_players, show_auth=(player is None))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        race = request.form["race"]
        player_class = request.form["player_class"]

        # Базовые параметры
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

        session["player_id"] = new_player.id
        return redirect(url_for("index"))

    name = request.args.get("name", "")
    return render_template("register.html", name=name)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("index"))

    player = Player.query.filter_by(name=name).first()
    if not player:
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




@app.route('/profile', methods=['POST'])
def upload_avatar():
    if 'avatar' not in request.files:
        return redirect(url_for('profile'))
    
    file = request.files['avatar']
    if file.filename == '':
        return redirect(url_for('profile'))
    
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            filename = secure_filename(f"player_{session['player_id']}.png")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
            player = Player.query.get(session['player_id'])
            player.avatar_url = filename
            db.session.commit()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")  # Логируем ошибку, но не мешаем работе
    
    return redirect(url_for('profile'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # создаём таблицы в базе, если их нет
    app.run(host="0.0.0.0", port=5000, debug=True)
