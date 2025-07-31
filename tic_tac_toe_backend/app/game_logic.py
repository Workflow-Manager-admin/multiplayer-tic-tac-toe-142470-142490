from app.models import Game, GamePlayer, Move, User, db

# PUBLIC_INTERFACE
def check_winner(board: str):
    """Checks board state (string of length 9) for a winner. Returns winning letter or None."""
    wins = [
        (0,1,2),(3,4,5),(6,7,8), # rows
        (0,3,6),(1,4,7),(2,5,8), # cols
        (0,4,8),(2,4,6),         # diags
    ]
    for i,j,k in wins:
        if board[i] == board[j] == board[k] and board[i] in ("X","O"):
            return board[i]
    return None

# PUBLIC_INTERFACE
def check_draw(board: str):
    """Checks if the board is a draw (all filled, no winner)."""
    return " " not in board and check_winner(board) is None

# PUBLIC_INTERFACE
def make_move(game: Game, user: User, position: int):
    """Process a move: validate, update board, log Move, check for win/draw."""
    # Find player's letter
    gp = GamePlayer.query.filter_by(game_id=game.id, user_id=user.id).first()
    if gp is None:
        return {"error": "Not a player in this game"}
    letter = gp.letter
    # Validate turn
    if game.state not in ("ongoing",):
        return {"error": "Game not ongoing"}
    if (game.current_turn != letter):
        return {"error": "Not your turn"}
    # Validate position
    if not (0 <= position <= 8):
        return {"error": "Invalid board position"}
    board = list(game.board_state)
    if board[position] != " ":
        return {"error": "Cell not empty"}
    # Make move
    board[position] = letter
    game.board_state = "".join(board)

    # Record move
    move = Move(game_id=game.id, user_id=user.id, position=position, letter=letter)
    db.session.add(move)
    # Check win/draw
    winner = check_winner(game.board_state)
    if winner:
        game.state = "ended"
        game.winner = user
    elif check_draw(game.board_state):
        game.state = "ended"
        game.winner = None
    else:
        # Switch turn
        game.current_turn = "O" if letter == "X" else "X"

    db.session.commit()
    return None  # None if success

