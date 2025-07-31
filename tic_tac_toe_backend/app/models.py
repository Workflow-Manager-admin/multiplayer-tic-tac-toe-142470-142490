from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """User model storing user identification and creation date."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    games = db.relationship('Game', secondary='game_players', back_populates='players')
    moves = db.relationship('Move', back_populates='user')

    def __repr__(self):
        return f"<User(username={self.username})>"


class Game(db.Model):
    """Represents a single Tic Tac Toe game instance."""
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    state = db.Column(db.String(16), default="waiting")  # waiting, ongoing, ended
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner = db.relationship("User", foreign_keys=[winner_id])
    current_turn = db.Column(db.String(1), default="X")  # "X" or "O"
    board_state = db.Column(db.String(9), default="         ")  # 9 spaces, 0-8

    players = db.relationship('User', secondary='game_players', back_populates='games')
    moves = db.relationship('Move', back_populates='game', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, state={self.state}, current_turn={self.current_turn})>"


class GamePlayer(db.Model):
    """Associates users with games and assigns them a letter (X/O)."""
    __tablename__ = 'game_players'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    letter = db.Column(db.String(1))  # "X" or "O"

    __table_args__ = (db.UniqueConstraint('user_id', 'game_id', name='_user_game_uc'),)


class Move(db.Model):
    """Tracks moves performed in games."""
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    position = db.Column(db.Integer)  # 0-8
    letter = db.Column(db.String(1))  # "X" or "O"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    game = db.relationship('Game', back_populates='moves')
    user = db.relationship('User', back_populates='moves')

