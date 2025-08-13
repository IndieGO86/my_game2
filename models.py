# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    race = db.Column(db.String(50), nullable=False)
    player_class = db.Column(db.String(50), nullable=False)

    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)

    health = db.Column(db.Integer, default=100)
    energy = db.Column(db.Integer, nullable=True)
    mana = db.Column(db.Integer, nullable=True)
    gold = db.Column(db.Integer, default=0)

    inventory = db.Column(JSON, default=list)  # Для работы JSON нужна psycopg2-binary

    def __repr__(self):
        return f"<Player {self.name}>"