import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "testsecret12345678656453142352463574687594365245675624637777773654321"
os.environ["MAIL_USERNAME"] = "test@example.com"
os.environ["MAIL_PASSWORD"] = "testpassword"
os.environ["MAIL_FROM"] = "test@example.com"

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.repositories.user_repository import UserRepository
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.services import auth_service as auth_service_module
from app.services import mail_service
from app.services.auth_service import AuthService
from app.services.profile_service import ProfileService
from app.repositories.chess_game_repository import ChessGameRepository
from app.repositories.rating_history_repository import RatingHistoryRepository
from main import app


test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def override_dependencies(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db

    sent_emails = []

    async def fake_send(recipient: str, token: str):
        sent_emails.append({"recipient": recipient, "token": token})

    monkeypatch.setattr(mail_service, "send_verification_email", fake_send)
    monkeypatch.setattr(auth_service_module, "send_verification_email", fake_send)

    from email_validator import validate_email as real_validate

    def fake_validate(email, check_deliverability=False):
        return real_validate(email, check_deliverability=False)

    monkeypatch.setattr(auth_service_module, "validate_email", fake_validate)

    app.state.sent_emails = sent_emails
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
def sent_emails():
    return app.state.sent_emails



@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def auth_service(db_session):
    user_repo = UserRepository(db_session)
    verification_repo = EmailVerificationRepository(db_session)
    return AuthService(user_repo, verification_repo)


@pytest_asyncio.fixture
def profile_service(db_session):
    user_repo = UserRepository(db_session)
    game_repo = ChessGameRepository(db_session)
    rating_repo = RatingHistoryRepository(db_session)
    return ProfileService(user_repo, game_repo, rating_repo)