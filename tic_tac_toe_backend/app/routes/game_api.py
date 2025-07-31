from flask import request, session
from flask.views import MethodView
from flask_smorest import Blueprint as SmorestBlueprint, abort
from app.models import db, User, Game, GamePlayer
from app.models import Move
from app.game_logic import make_move
from sqlalchemy.exc import IntegrityError

blp = SmorestBlueprint("TicTacToe", "tictactoe", url_prefix="/api", description="Tic Tac Toe API routes")

SESSION_USER_KEY = "user_id"

def get_current_user():
    uid = session.get(SESSION_USER_KEY)
    if uid:
        return User.query.get(uid)
    return None

# PUBLIC_INTERFACE
@blp.route('/users', methods=["POST"])
class RegisterUser(MethodView):
    """Registers a new user given a username, returns user_id and username."""
    def post(self):
        data = request.get_json()
        username = data.get("username")
        if not username:
            abort(400, message="Username required")
        user = User(username=username)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="Username already exists")
        session[SESSION_USER_KEY] = user.id
        return {"user_id": user.id, "username": user.username}

# PUBLIC_INTERFACE
@blp.route('/session', methods=["GET"])
class GetSession(MethodView):
    """Get current user session (if logged in)."""
    def get(self):
        user = get_current_user()
        if user:
            return {"user_id": user.id, "username": user.username}
        return {"user_id": None, "username": None}

# PUBLIC_INTERFACE
@blp.route('/games', methods=["POST"])
class CreateGame(MethodView):
    """Create a new game. First player is X. Returns game_id."""
    def post(self):
        user = get_current_user()
        if not user:
            abort(401, message="User not authenticated")
        game = Game(state="waiting", board_state=" " * 9, current_turn="X")
        db.session.add(game)
        db.session.commit()
        # Add creator as player (always X)
        gp = GamePlayer(user_id=user.id, game_id=game.id, letter="X")
        db.session.add(gp)
        db.session.commit()
        return {"game_id": game.id}

# PUBLIC_INTERFACE
@blp.route('/games/<int:game_id>/join', methods=["POST"])
class JoinGame(MethodView):
    """Join a game as the second player. Becomes letter O. Starts game if possible."""
    def post(self, game_id):
        user = get_current_user()
        if not user:
            abort(401, message="User not authenticated")
        game = Game.query.get(game_id)
        if not game:
            abort(404, message="Game not found")
        players = GamePlayer.query.filter_by(game_id=game_id).count()
        if players >= 2:
            abort(400, message="Game already has two players")
        current_players = [gp.user_id for gp in GamePlayer.query.filter_by(game_id=game_id)]
        if user.id in current_players:
            abort(400, message="Already in game")
        gp = GamePlayer(user_id=user.id, game_id=game_id, letter="O")
        db.session.add(gp)
        # If now full, set to ongoing
        if players == 1:
            game.state = "ongoing"
        db.session.commit()
        return {"game_id": game.id, "state": game.state}

# PUBLIC_INTERFACE
@blp.route('/games/<int:game_id>/move', methods=["POST"])
class MakeMove(MethodView):
    """Make a move as the current player. Request: position (0-8). Returns updated game state."""
    def post(self, game_id):
        user = get_current_user()
        if not user:
            abort(401, message="User not authenticated")
        game = Game.query.get(game_id)
        if not game:
            abort(404, message="Game not found")
        data = request.get_json()
        position = data.get("position")
        if position is None:
            abort(400, message="Position required")
        error = make_move(game, user, position)
        if error:
            abort(400, message=error["error"])
        return {"message": "move accepted", "state": serialize_game(game, user)}

# PUBLIC_INTERFACE
@blp.route('/games/<int:game_id>', methods=["GET"])
class GameState(MethodView):
    """Returns details and state of a game."""
    def get(self, game_id):
        user = get_current_user()
        game = Game.query.get(game_id)
        if not game:
            abort(404, message="Game not found")
        return {"state": serialize_game(game, user)}

# Utility functions
def serialize_game(game: Game, user: User):
    # Board is always string of len 9
    player_letters = {}
    for gp in GamePlayer.query.filter_by(game_id=game.id):
        player_letters[gp.letter] = gp.user.username
    winner = game.winner.username if game.winner else None
    moves = [
        {"position": m.position, "letter": m.letter, "user": User.query.get(m.user_id).username}
        for m in Move.query.filter_by(game_id=game.id).order_by(Move.created_at)
    ]
    return {
        "game_id": game.id,
        "state": game.state,
        "current_turn": game.current_turn,
        "board": list(game.board_state),
        "players": player_letters,
        "your_letter": None if not user else (
            GamePlayer.query.filter_by(game_id=game.id, user_id=user.id).first().letter
            if GamePlayer.query.filter_by(game_id=game.id, user_id=user.id).first()
            else None
        ),
        "winner": winner,
        "moves": moves
    }

