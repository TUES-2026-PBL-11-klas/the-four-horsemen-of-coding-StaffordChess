from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.chess_game_repository import ChessGameRepository
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

    session = session_manager.get_or_create(
        game_id, game.white_player_id, game.black_player_id, game_repo,
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
                user_id, data["from"], data["to"],
            )
            await connection_manager.broadcast(game_id, state)
        elif msg_type == "resign":
            state = await session.resign(user_id)
            await connection_manager.broadcast(game_id, state)
        else:
            await websocket.send_json({"error": f"Unknown message type: {msg_type}"})
    except HTTPException as e:
        await websocket.send_json({"error": e.detail})

    if session.engine.game_result.is_game_over():
        session_manager.remove(game_id)