import pytest
from fastapi import HTTPException

from app.services.game_session_service import GameSessionService, _square_to_coordinates



def test_square_to_coordinates_e2():
    assert _square_to_coordinates("e2") == (6, 4)


def test_square_to_coordinates_corners():
    assert _square_to_coordinates("a8") == (0, 0)
    assert _square_to_coordinates("a1") == (7, 0)
    assert _square_to_coordinates("h8") == (0, 7)
    assert _square_to_coordinates("h1") == (7, 7)


def test_square_to_coordinates_invalid_length():
    with pytest.raises(ValueError):
        _square_to_coordinates("e22")


def test_square_to_coordinates_invalid_file():
    with pytest.raises(ValueError):
        _square_to_coordinates("z2")


def test_square_to_coordinates_invalid_rank():
    with pytest.raises(ValueError):
        _square_to_coordinates("e9")



async def make_session(db_session, game_repo, player1, player2):
    game = await game_repo.create(player1.id, player2.id, "5+0")
    await db_session.commit()
    return GameSessionService(game.id, player1.id, player2.id, game_repo)



async def test_initial_state(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    state = session.get_state()
    assert state["turn"] == "white"
    assert state["is_game_over"] is False
    assert "fen" in state


async def test_clock_not_started_until_both_join(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    assert session.clock.is_running is False
    assert session.is_started is False



async def test_legal_move_switches_turn(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    state = await session.handle_incoming_move(player1.id, "e2", "e4")
    assert state["turn"] == "black"


async def test_illegal_move_rejected(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    with pytest.raises(HTTPException) as exc:
        await session.handle_incoming_move(player1.id, "e2", "e5")
    assert exc.value.status_code == 400


async def test_move_out_of_turn_rejected(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    with pytest.raises(HTTPException) as exc:
        await session.handle_incoming_move(player2.id, "e7", "e5")
    assert exc.value.status_code == 400
    assert "turn" in exc.value.detail.lower()


async def test_non_player_rejected(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    with pytest.raises(HTTPException) as exc:
        await session.handle_incoming_move(9999, "e2", "e4")
    assert exc.value.status_code == 403



async def test_fools_mate_ends_game(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    await session.handle_incoming_move(player1.id, "f2", "f3")
    await session.handle_incoming_move(player2.id, "e7", "e5")
    await session.handle_incoming_move(player1.id, "g2", "g4")
    state = await session.handle_incoming_move(player2.id, "d8", "h4")
    assert state["is_game_over"] is True


async def test_fools_mate_records_winner_in_db(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    await session.handle_incoming_move(player1.id, "f2", "f3")
    await session.handle_incoming_move(player2.id, "e7", "e5")
    await session.handle_incoming_move(player1.id, "g2", "g4")
    await session.handle_incoming_move(player2.id, "d8", "h4")

    game = await game_repo.get_by_id(session.game_id)
    assert game.status == "finished"
    assert game.winner_id == player2.id
    assert game.result == "black_wins"


async def test_move_after_game_over_rejected(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    await session.handle_incoming_move(player1.id, "f2", "f3")
    await session.handle_incoming_move(player2.id, "e7", "e5")
    await session.handle_incoming_move(player1.id, "g2", "g4")
    await session.handle_incoming_move(player2.id, "d8", "h4")

    with pytest.raises(HTTPException) as exc:
        await session.handle_incoming_move(player1.id, "e1", "e2")
    assert exc.value.status_code == 400



async def test_resign_ends_game(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    state = await session.resign(player1.id)
    assert state["is_game_over"] is True



async def test_pgn_records_moves(db_session, game_repo, players):
    player1, player2 = players
    session = await make_session(db_session, game_repo, player1, player2)
    await session.handle_incoming_move(player1.id, "e2", "e4")
    await session.handle_incoming_move(player2.id, "e7", "e5")
    pgn = session._build_pgn()
    assert pgn == "e2e4 e7e5"