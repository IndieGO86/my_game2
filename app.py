from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Создаем экземпляры без привязки к приложению
app = Flask(__name__)
db = SQLAlchemy()

# Конфигурация приложения
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db/mygame')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/avatars'

# Определяем модель Player
class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    race = db.Column(db.String(50), nullable=False)
    player_class = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(200), default='default.png') 
    bio = db.Column(db.Text, nullable=True)
    theme_color = db.Column(db.String(7), default='#1e1e1e')
    card_style = db.Column(db.String(50), default='default')
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    health = db.Column(db.Integer, default=100)
    energy = db.Column(db.Integer, nullable=True)
    mana = db.Column(db.Integer, nullable=True)
    gold = db.Column(db.Integer, default=0)
    inventory = db.Column(db.JSON, default=list)

    def __repr__(self):
        return f"<Player {self.name}>"

# Инициализируем db с приложением
db.init_app(app)

@app.route("/")
def index():
    player_id = session.get("player_id")
    show_auth = not player_id
    
    if player_id:
        player = Player.query.get(player_id)
        other_players = Player.query.filter(Player.id != player_id).all()
        return render_template("index.html", player=player, other_players=other_players, show_auth=show_auth)
    
    return render_template("index.html", show_auth=show_auth)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        password = request.form['password'].strip()
        race = request.form['race']
        player_class = request.form['player_class']

        # Проверка: игрок уже существует?
        existing_player = Player.query.filter_by(name=name).first()
        if existing_player:
            flash("Игрок с таким именем уже существует!", "error")
            return redirect(url_for("register"))

        # Проверка пароля
        if len(password) < 6:
            flash("Пароль должен содержать минимум 6 символов!", "error")
            return redirect(url_for("register"))
        
        
        # Хэшируем пароль
        hashed_password = generate_password_hash(password)
        
        new_player = Player(
            name=name,
            race=race,
            password_hash=hashed_password,
            player_class=player_class,
            health=100
        )
        
        if player_class == "Воин":
            new_player.energy = 100
        elif player_class == "Маг":
            new_player.mana = 100
        
        db.session.add(new_player)
        db.session.commit()
        
        session['player_id'] = new_player.id
        flash("Регистрация успешна, вы вошли в игру!", "success")
        return redirect(url_for('index'))
    
    return render_template("register.html")

@app.route("/login", methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password'].strip()
    
    player = Player.query.filter_by(name=name).first()
    
    if player and check_password_hash(player.password_hash, password):
        session['player_id'] = player.id
        flash("Успешный вход!", "success")
    else:
        flash("Неверный логин или пароль", "error")
    
    return redirect(url_for('index'))

@app.route("/logout", methods=['POST'])
def logout():
    session.pop('player_id', None)
    return redirect(url_for('index'))

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    player_id = session.get("player_id")
    if not player_id:
        return redirect(url_for("register"))
    
    player = Player.query.get(player_id)
    
    if request.method == 'POST':
        player.bio = request.form.get('bio')
        player.theme_color = request.form.get('theme_color', '#1e1e1e')
        player.card_style = request.form.get('card_style', 'default')
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename != '' and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    filename = secure_filename(f"player_{player_id}.png")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    player.avatar_url = filename
                except Exception as e:
                    print(f"Ошибка загрузки аватара: {e}")
        
        db.session.commit()
        flash('Настройки профиля сохранены!', 'success')
        return redirect(url_for('profile'))
    
    return render_template("profile.html", player=player)

if __name__ == "__main__":
    with app.app_context():
        # Создаем таблицы в базе данных
        db.create_all()
        
        # Создаем папку для аватаров
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(host="0.0.0.0", port=5000, debug=True)