from app.domain.game_result import GameResult



def test_default_is_ongoing():
    gr = GameResult()
    assert gr.result == GameResult.Result.ONGOING


def test_default_reason():
    gr = GameResult()
    assert gr.reason == "game is ongoing"


def test_default_not_game_over():
    gr = GameResult()
    assert gr.is_game_over() is False


def test_custom_construction():
    gr = GameResult(GameResult.Result.WHITE_WINS, "checkmate")
    assert gr.result == GameResult.Result.WHITE_WINS
    assert gr.reason == "checkmate"



def test_set_result_changes_state():
    gr = GameResult()
    gr.set_result(GameResult.Result.DRAW, "stalemate")
    assert gr.result == GameResult.Result.DRAW
    assert gr.reason == "stalemate"


def test_set_result_makes_game_over():
    gr = GameResult()
    gr.set_result(GameResult.Result.BLACK_WINS, "checkmate")
    assert gr.is_game_over() is True



def test_ongoing_not_over():
    gr = GameResult(GameResult.Result.ONGOING, "x")
    assert gr.is_game_over() is False


def test_white_wins_is_over():
    gr = GameResult(GameResult.Result.WHITE_WINS, "x")
    assert gr.is_game_over() is True


def test_black_wins_is_over():
    gr = GameResult(GameResult.Result.BLACK_WINS, "x")
    assert gr.is_game_over() is True


def test_draw_is_over():
    gr = GameResult(GameResult.Result.DRAW, "x")
    assert gr.is_game_over() is True


def test_white_resigns_is_over():
    gr = GameResult(GameResult.Result.WHITE_RESIGNS, "x")
    assert gr.is_game_over() is True


def test_black_resigns_is_over():
    gr = GameResult(GameResult.Result.BLACK_RESIGNS, "x")
    assert gr.is_game_over() is True



def test_result_enum_has_six_values():
    assert len(list(GameResult.Result)) == 6