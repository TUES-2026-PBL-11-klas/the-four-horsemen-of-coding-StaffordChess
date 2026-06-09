from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from jose import JWTError

from app.core.dependencies import get_current_user, get_lobby_service, get_game_repo
from app.schemas.lobby_dto import GameConfig, LobbyChallenge
from app.services.lobby_service import LobbyService
from app.utils.security import decode_token

router = APIRouter(prefix="/lobby", tags=["lobby"])

@router.get("/games", response_model=list[LobbyChallenge])
async def get_active_games(service: LobbyService = Depends(get_lobby_service)):
    return service.get_active_games()


@router.post("/create", response_model=LobbyChallenge)
async def create_game(
    config: GameConfig,
    current_user = Depends(get_current_user),
    service: LobbyService = Depends(get_lobby_service),
):
    return await service.add_to_lobby(current_user, config)

@router.post("/accept/{challenge_id}")
async def accept_game(
    challenge_id: str,
    current_user = Depends(get_current_user),
    service: LobbyService = Depends(get_lobby_service),
    game_repo = Depends(get_game_repo),
):
    try:
        game = await service.match_players(challenge_id, current_user, game_repo)
        return {"message": "Match started", "game_id": game.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.websocket("/ws")
async def websocket_lobby(
    websocket: WebSocket,
    token: str = "",
    service: LobbyService = Depends(get_lobby_service)):
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4001)
        return
    await service.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await service.disconnect(websocket)

@router.delete("/cancel/{challenge_id}")
async def cancel_game(
    challenge_id: str,
    current_user = Depends(get_current_user),
    service: LobbyService = Depends(get_lobby_service)):
    try:
        await service.cancel_challenge(challenge_id, current_user.id)
        return {"message": "Challenge cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))