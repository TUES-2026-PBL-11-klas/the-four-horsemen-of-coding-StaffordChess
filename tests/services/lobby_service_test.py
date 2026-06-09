import pytest
from app.services.lobby_service import LobbyService
from app.schemas.lobby_dto import GameConfig
from app.repositories.chess_game_repository import ChessGameRepository
from app.models.user import User


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, data: dict):
        self.messages.append(data)


async def make_user(db_session, username: str, email: str, rating: int = 1500) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password="fake",
        is_active=True,
        current_rating=rating
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def lobby_service():
    return LobbyService()


@pytest.fixture
def game_repo(db_session):
    return ChessGameRepository(db_session)



@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect(lobby_service):
    ws = DummyWebSocket()
    user_id = 1
    await lobby_service.connect(ws, user_id)
    
    assert ws.accepted is True
    assert ws in lobby_service.active_connections
    
    await lobby_service.disconnect(ws)
    assert ws not in lobby_service.active_connections



@pytest.mark.asyncio
async def test_add_to_lobby_creates_game_and_broadcasts(lobby_service, db_session):
    user = await make_user(db_session, "host_player", "host@x.com", 1600)
    config = GameConfig(time_control="10+0", color_preference="white")

    ws = DummyWebSocket()
    await lobby_service.connect(ws, user.id)

    challenge = await lobby_service.add_to_lobby(user, config)

    assert challenge.id in lobby_service.waiting_games
    assert challenge.host_username == "host_player"
    assert challenge.time_control == "10+0"
    assert len(lobby_service.get_active_games()) == 1

    assert len(ws.messages) == 1
    broadcast_msg = ws.messages[0]
    assert broadcast_msg["type"] == "NEW_CHALLENGE"
    assert broadcast_msg["challenge"]["id"] == challenge.id



@pytest.mark.asyncio
async def test_cancel_challenge_success(lobby_service, db_session):
    user = await make_user(db_session, "host", "h@x.com")
    config = GameConfig(time_control="3+2", color_preference="random")
    challenge = await lobby_service.add_to_lobby(user, config)
    
    ws = DummyWebSocket()
    await lobby_service.connect(ws, user.id)

    await lobby_service.cancel_challenge(challenge.id, user.id)

    assert len(lobby_service.get_active_games()) == 0
    assert ws.messages[0]["type"] == "REMOVE_CHALLENGE"
    assert ws.messages[0]["challenge_id"] == challenge.id


@pytest.mark.asyncio
async def test_cancel_challenge_wrong_user_raises_error(lobby_service, db_session):
    host = await make_user(db_session, "host", "h@x.com")
    hacker = await make_user(db_session, "hacker", "hack@x.com")
    challenge = await lobby_service.add_to_lobby(host, GameConfig(time_control="5+0", color_preference="white"))

    with pytest.raises(PermissionError) as exc_info:
        await lobby_service.cancel_challenge(challenge.id, hacker.id)
    
    assert "own challenges" in str(exc_info.value)
    assert len(lobby_service.get_active_games()) == 1



@pytest.mark.asyncio
async def test_match_players_success_and_db_creation(lobby_service, game_repo, db_session):
    host = await make_user(db_session, "white_player", "white@x.com")
    opponent = await make_user(db_session, "black_player", "black@x.com")
    
    config = GameConfig(time_control="10+0", color_preference="white")
    challenge = await lobby_service.add_to_lobby(host, config)

    ws = DummyWebSocket()
    await lobby_service.connect(ws, host.id)

    game = await lobby_service.match_players(challenge.id, opponent, game_repo)

    assert len(lobby_service.get_active_games()) == 0

    assert game.white_player_id == host.id
    assert game.black_player_id == opponent.id
    assert game.time_control == "10+0"
    assert game.status == "ongoing"

    assert any(msg["type"] == "MATCH_STARTED" and msg["game_id"] == game.id for msg in ws.messages)


@pytest.mark.asyncio
async def test_match_players_cannot_accept_own_challenge(lobby_service, game_repo, db_session):
    host = await make_user(db_session, "host", "h@x.com")
    challenge = await lobby_service.add_to_lobby(host, GameConfig(time_control="10+0", color_preference="white"))

    with pytest.raises(ValueError) as exc_info:
        await lobby_service.match_players(challenge.id, host, game_repo)
    
    assert "own challenge" in str(exc_info.value)


@pytest.mark.asyncio
async def test_match_players_random_color_assignment(lobby_service, game_repo, db_session):
    host = await make_user(db_session, "host", "h@x.com")
    opponent = await make_user(db_session, "opponent", "o@x.com")
    
    for _ in range(10):
        challenge = await lobby_service.add_to_lobby(host, GameConfig(time_control="5+0", color_preference="random"))
        game = await lobby_service.match_players(challenge.id, opponent, game_repo)
        
        assert set([game.white_player_id, game.black_player_id]) == {host.id, opponent.id}