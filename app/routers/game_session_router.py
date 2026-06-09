from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.user_repository import UserRepository
from app.core.connection_manager import ConnectionManager
from app.core.game_session_manager import GameSessionManager
from app.utils.security import decode_token

router = APIRouter(prefix="/game", tags=["game"])

connection_manager = ConnectionManager()
session_manager = GameSessionManager()


def _authenticate(token: str) -> int:
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise ValueError("Invalid token")


def _parse_time_control(tc: str | None) -> tuple[int, int]:
    if not tc:
        return 300, 0
    try:
        minutes_str, increment_str = tc.split("+", 1)
        return int(minutes_str) * 60, int(increment_str)
    except (ValueError, AttributeError):
        return 300, 0


@router.get("/{game_id}")
async def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    game_repo = ChessGameRepository(db)
    user_repo = UserRepository(db)

    game = await game_repo.get_by_id(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    if current_user.id not in (game.white_player_id, game.black_player_id):
        raise HTTPException(status_code=403, detail="Not a participant in this game")

    white = await user_repo.get_by_id(game.white_player_id)
    black = await user_repo.get_by_id(game.black_player_id)

    def _player(user_id: int, user) -> dict:
        return {
            "id": user_id,
            "username": user.username if user else "Deleted user",
            "rating": user.current_rating if user else None,
        }

    return {
        "id": game.id,
        "white_player": _player(game.white_player_id, white),
        "black_player": _player(game.black_player_id, black),
        "time_control": game.time_control,
        "status": game.status,
        "result": game.result,
        "winner_id": game.winner_id,
        "moves_pgn": game.moves_pgn,
        "started_at": game.started_at.isoformat() if game.started_at else None,
    }


@router.websocket("/{game_id}")
async def game_websocket(
    websocket: WebSocket, 
    game_id: int, 
    token: str = "",
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = _authenticate(token)
    except ValueError:
        await websocket.close(code=4001)
        return

    game_repo = ChessGameRepository(db)
    game = await game_repo.get_by_id(game_id)
    if game is None:
        await websocket.close(code=4004)
        return

    if user_id not in (game.white_player_id, game.black_player_id):
        await websocket.close(code=4003)
        return

    initial_seconds, increment_seconds = _parse_time_control(game.time_control)
    session = await session_manager.get_or_create(
        game_id, game.white_player_id, game.black_player_id, game_repo,
        initial_seconds=initial_seconds,
        increment_seconds=increment_seconds,
    )

    await connection_manager.connect(game_id, websocket)

    if not session.is_started:
        active_connections = len(connection_manager.connections.get(game_id, []))
        if active_connections >= 2:
            session.is_started = True
            session.clock.start()

    await websocket.send_json(session.get_state())

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_message(session, game_id, user_id, data, websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(game_id, websocket)


async def _handle_message(session, game_id: int, user_id: int, data: dict, websocket: WebSocket) -> None:
    msg_type = data.get("type")

    try:
        if msg_type == "move":
            state = await session.handle_incoming_move(
                user_id, data["from"], data["to"], data.get("promotion"),
            )
            await connection_manager.broadcast(game_id, state)
        elif msg_type == "resign":
            state = await session.resign(user_id)
            await connection_manager.broadcast(game_id, state)
        elif msg_type == "sync":
            state = await session.check_time()
            await connection_manager.broadcast(game_id, state)
        else:
            await websocket.send_json({"error": f"Unknown message type: {msg_type}"})
    except HTTPException as e:
        await websocket.send_json({"error": e.detail})

    if session.engine.game_result.is_game_over():
        session_manager.remove(game_id)