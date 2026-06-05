from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.user import User
from app.models.chess_game import ChessGame
from app.models.rating_history import RatingHistory
from app.repositories.user_repository import UserRepository
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.rating_history_repository import RatingHistoryRepository
from app.services.profile_service import ProfileService



async def make_user(db_session, username: str, email: str, **overrides) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password="fake_password",
        is_active=True,
        **overrides
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def make_game(db_session, white_id: int, black_id: int, **overrides) -> ChessGame:
    game = ChessGame(
        white_player_id=white_id,
        black_player_id=black_id,
        time_control="10+0",
        **overrides
    )
    db_session.add(game)
    await db_session.flush()
    return game


async def make_rating_snapshot(db_session, user_id: int, rating: int, days_ago: int = 0) -> RatingHistory:
    snapshot = RatingHistory(
        user_id=user_id,
        rating=rating,
    )
    db_session.add(snapshot)
    await db_session.flush()
    
    if days_ago > 0:
        snapshot.date = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
    return snapshot


@pytest.mark.asyncio
async def test_fetch_profile_data_success(profile_service, db_session):
    user = await make_user(
        db_session, "carlsen", "carlsen@example.com", 
        current_rating=2850, games_played=100, wins=80, losses=10, draws=10
    )
    await db_session.commit()

    profile = await profile_service.fetch_profile_data(user.id)

    assert profile.username == "carlsen"
    assert profile.current_rating == 2850
    assert profile.games_played == 100
    assert profile.wins == 80
    assert profile.losses == 10
    assert profile.draws == 10


@pytest.mark.asyncio
async def test_fetch_profile_data_user_not_found_raises_404(profile_service):
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.fetch_profile_data(9999)
    
    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail



@pytest.mark.asyncio
async def test_fetch_game_history_success_and_mapping(profile_service, db_session):
    user1 = await make_user(db_session, "player1", "p1@x.com")
    user2 = await make_user(db_session, "player2", "p2@x.com")
    
    await make_game(
        db_session, white_id=user1.id, black_id=user2.id, 
        winner_id=user1.id, status="finished", result="1-0"
    )
    
    await make_game(
        db_session, white_id=user2.id, black_id=user1.id, 
        winner_id=user2.id, status="finished", result="1-0"
    )
    
    await db_session.commit()

    history = await profile_service.fetch_game_history(user1.id)

    assert len(history) == 2
    
    black_game = next(g for g in history if g.played_as == "black")
    assert black_game.opponent_username == "player2"
    assert black_game.outcome == "loss"
    assert black_game.status == "finished"

    white_game = next(g for g in history if g.played_as == "white")
    assert white_game.opponent_username == "player2"
    assert white_game.outcome == "win"


@pytest.mark.asyncio
async def test_fetch_game_history_calculates_draws_and_ongoing(profile_service, db_session):
    user1 = await make_user(db_session, "hero", "hero@x.com")
    user2 = await make_user(db_session, "villain", "villain@x.com")
    
    await make_game(
        db_session, white_id=user1.id, black_id=user2.id, 
        winner_id=None, status="finished", result="1/2-1/2"
    )
    
    await make_game(
        db_session, white_id=user2.id, black_id=user1.id, 
        winner_id=None, status="ongoing", result=None
    )
    
    await db_session.commit()

    history = await profile_service.fetch_game_history(user1.id)
    
    draw_game = next(g for g in history if g.status == "finished")
    assert draw_game.outcome == "draw"
    
    ongoing_game = next(g for g in history if g.status == "ongoing")
    assert ongoing_game.outcome == "ongoing"


@pytest.mark.asyncio
async def test_fetch_game_history_user_not_found_raises_404(profile_service):
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.fetch_game_history(9999)
    
    assert exc_info.value.status_code == 404



@pytest.mark.asyncio
async def test_generate_rating_chart_points_returns_ordered_data(profile_service, db_session):
    user = await make_user(db_session, "graph_user", "graph@x.com")
    
    await make_rating_snapshot(db_session, user.id, rating=1550, days_ago=2)
    await make_rating_snapshot(db_session, user.id, rating=1600, days_ago=0) # Днес
    await make_rating_snapshot(db_session, user.id, rating=1500, days_ago=5) # Преди 5 дни
    
    await db_session.commit()

    points = await profile_service.generate_rating_chart_points(user.id)

    assert len(points) == 3
    assert points[0].rating == 1500
    assert points[1].rating == 1550
    assert points[2].rating == 1600
    
    assert "T" in points[0].date


@pytest.mark.asyncio
async def test_generate_rating_chart_points_user_not_found_raises_404(profile_service):
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.generate_rating_chart_points(9999)
    
    assert exc_info.value.status_code == 404