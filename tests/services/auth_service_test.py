from datetime import datetime, timedelta, timezone

import pytest
from email_validator import EmailNotValidError
from fastapi import HTTPException
from sqlalchemy import select

from app.models.user import User
from app.models.email_verification import EmailVerification
from app.schemas.auth_dto import UserCreate, UserLogin, VerifyEmail
from app.services import auth_service as auth_module
from app.utils.security import hash_password



VALID_USER = {
    "username": "felix",
    "email": "felix@example.com",
    "password": "Password123",
}


async def register_helper(auth_service, **overrides):
    data = UserCreate(**{**VALID_USER, **overrides})
    return await auth_service.register(data)


async def fully_verify_user(auth_service, sent_emails, **overrides):
    data = UserCreate(**{**VALID_USER, **overrides})
    await auth_service.register(data)
    token = sent_emails[-1]["token"]
    await auth_service.verify_email(VerifyEmail(email=data.email, token=token))
    return data.email


async def test_register_creates_user_with_inactive_flag(auth_service, db_session):
    await register_helper(auth_service)

    user = (await db_session.execute(
        select(User).where(User.email == "felix@example.com")
    )).scalar_one()
    assert user.username == "felix"
    assert user.is_active is False
    assert user.hashed_password != "Password123"

async def test_register_creates_verification_row(auth_service, db_session):
    await register_helper(auth_service)

    verification = (await db_session.execute(select(EmailVerification))).scalar_one()
    assert verification.is_verified is False
    assert len(verification.token) == 6


async def test_register_sends_email_with_token(auth_service, sent_emails):
    await register_helper(auth_service)

    assert len(sent_emails) == 1
    assert sent_emails[0]["recipient"] == "felix@example.com"
    assert len(sent_emails[0]["token"]) == 6


async def test_register_returns_success_message(auth_service):
    result = await register_helper(auth_service)
    assert "successful" in result["message"].lower()


async def test_register_rejects_undeliverable_email(auth_service, monkeypatch):
    def reject(email, check_deliverability=False):
        raise EmailNotValidError("Domain has no mail servers")

    monkeypatch.setattr(auth_module, "validate_email", reject)

    with pytest.raises(HTTPException) as exc_info:
        await register_helper(auth_service)
    assert exc_info.value.status_code == 400
    assert "not valid" in exc_info.value.detail.lower()


async def test_register_rejects_duplicate_email_with_409(auth_service):
    await register_helper(auth_service)

    with pytest.raises(HTTPException) as exc_info:
        await register_helper(auth_service, username="felix2")
    assert exc_info.value.status_code == 409


async def test_register_rejects_duplicate_username_with_409(auth_service):
    await register_helper(auth_service)

    with pytest.raises(HTTPException) as exc_info:
        await register_helper(auth_service, email="felix2@example.com")
    assert exc_info.value.status_code == 409


async def test_register_rolls_back_when_email_send_fails(
    auth_service, db_session, monkeypatch,
):
    async def broken_send(recipient, token):
        raise RuntimeError("SMTP server unreachable")

    monkeypatch.setattr(auth_module, "send_verification_email", broken_send)

    with pytest.raises(HTTPException) as exc_info:
        await register_helper(auth_service)
    assert exc_info.value.status_code == 400

    user = (await db_session.execute(select(User))).scalar_one_or_none()
    assert user is None, "Failed registration left a user row behind!"


async def test_register_does_not_send_email_when_user_already_exists(
    auth_service, sent_emails,
):
    await register_helper(auth_service)
    sent_emails.clear()

    with pytest.raises(HTTPException):
        await register_helper(auth_service, username="bob")

    assert len(sent_emails) == 0



async def test_resend_for_unknown_email_returns_generic_message(
    auth_service, sent_emails,
):
    result = await auth_service.resend_verification("nobody@example.com")
    assert "if this email exists" in result["message"].lower()
    assert len(sent_emails) == 0


async def test_resend_for_already_verified_user_returns_generic_message(
    auth_service, sent_emails,
):
    await fully_verify_user(auth_service, sent_emails)
    sent_emails.clear()

    result = await auth_service.resend_verification("felix@example.com")
    assert "if this email exists" in result["message"].lower()
    assert len(sent_emails) == 0


async def test_resend_for_unverified_user_sends_new_email(auth_service, sent_emails):
    await register_helper(auth_service)
    sent_emails.clear()

    result = await auth_service.resend_verification("felix@example.com")

    assert "if this email exists" in result["message"].lower()
    assert len(sent_emails) == 1
    assert sent_emails[0]["recipient"] == "felix@example.com"


async def test_resend_rotates_token_in_db(auth_service, sent_emails, db_session):
    await register_helper(auth_service)
    sent_emails.clear()

    await auth_service.resend_verification("felix@example.com")

    new_token_in_db = (await db_session.execute(select(EmailVerification))).scalar_one().token
    assert new_token_in_db == sent_emails[-1]["token"]


async def test_resend_rolls_back_on_email_failure(
    auth_service, sent_emails, db_session, monkeypatch,
):
    await register_helper(auth_service)
    original_token = (await db_session.execute(select(EmailVerification))).scalar_one().token

    async def broken_send(recipient, token):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(auth_module, "send_verification_email", broken_send)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.resend_verification("felix@example.com")
    assert exc_info.value.status_code == 400

    await db_session.rollback()
    current_token = (await db_session.execute(select(EmailVerification))).scalar_one().token
    assert current_token == original_token


async def test_verify_email_success_activates_user(
    auth_service, sent_emails, db_session,
):
    await register_helper(auth_service)
    token = sent_emails[-1]["token"]

    result = await auth_service.verify_email(VerifyEmail(
        email="felix@example.com", token=token,
    ))
    assert "verified successfully" in result["message"].lower()

    user = (await db_session.execute(select(User))).scalar_one()
    assert user.is_active is True

    verification = (await db_session.execute(select(EmailVerification))).scalar_one()
    assert verification.is_verified is True


async def test_verify_email_unknown_email_returns_400(auth_service):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_email(VerifyEmail(
            email="nobody@example.com", token="123456",
        ))
    assert exc_info.value.status_code == 400


async def test_verify_email_already_active_user_returns_400(auth_service, sent_emails):
    await fully_verify_user(auth_service, sent_emails)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_email(VerifyEmail(
            email="felix@example.com", token=sent_emails[-1]["token"],
        ))
    assert exc_info.value.status_code == 400


async def test_verify_email_wrong_token_returns_400(auth_service, sent_emails):
    await register_helper(auth_service)
    real_token = sent_emails[-1]["token"]
    wrong = "000000" if real_token != "000000" else "111111"

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_email(VerifyEmail(
            email="felix@example.com", token=wrong,
        ))
    assert exc_info.value.status_code == 400


async def test_verify_email_expired_token_returns_400(
    auth_service, sent_emails, db_session,
):
    await register_helper(auth_service)
    token = sent_emails[-1]["token"]

    verification = (await db_session.execute(select(EmailVerification))).scalar_one()
    verification.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_email(VerifyEmail(
            email="felix@example.com", token=token,
        ))
    assert exc_info.value.status_code == 400


async def test_verify_email_already_verified_row_returns_400(
    auth_service, sent_emails, db_session,
):
    await register_helper(auth_service)
    token = sent_emails[-1]["token"]

    verification = (await db_session.execute(select(EmailVerification))).scalar_one()
    verification.is_verified = True
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_email(VerifyEmail(
            email="felix@example.com", token=token,
        ))
    assert exc_info.value.status_code == 400



async def test_login_success_returns_jwt(auth_service, sent_emails):
    await fully_verify_user(auth_service, sent_emails)

    result = await auth_service.login(UserLogin(
        email="felix@example.com", password="Password123",
    ))

    assert result["token_type"] == "bearer"
    assert result["username"] == "felix"
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 20


async def test_login_unknown_email_returns_401(auth_service):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(UserLogin(
            email="nobody@example.com", password="Password123",
        ))
    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()


async def test_login_wrong_password_returns_401(auth_service, sent_emails):
    await fully_verify_user(auth_service, sent_emails)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(UserLogin(
            email="felix@example.com", password="WrongPassword123",
        ))
    assert exc_info.value.status_code == 401


async def test_login_unverified_user_returns_403(auth_service):
    await register_helper(auth_service)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(UserLogin(
            email="felix@example.com", password="Password123",
        ))
    assert exc_info.value.status_code == 403
    assert "verify" in exc_info.value.detail.lower()



async def make_user(db_session, *, username, email, is_active, days_old):
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password("doesnt-matter"),
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.flush()
    user.created_at = datetime.now(timezone.utc) - timedelta(days=days_old)
    await db_session.commit()
    return user


async def test_cleanup_returns_zero_when_nothing_to_delete(auth_service):
    deleted = await auth_service.cleanup_unverified_users()
    assert deleted == 0


async def test_cleanup_deletes_old_unverified_users(auth_service, db_session):
    await make_user(db_session, username="old", email="old@x.com",
                     is_active=False, days_old=30)

    deleted = await auth_service.cleanup_unverified_users()
    assert deleted == 1

    remaining = (await db_session.execute(select(User))).scalars().all()
    assert len(remaining) == 0


async def test_cleanup_does_not_delete_verified_users(auth_service, db_session):
    await make_user(db_session, username="verified", email="v@x.com",
                     is_active=True, days_old=30)

    deleted = await auth_service.cleanup_unverified_users()
    assert deleted == 0

    remaining = (await db_session.execute(select(User))).scalars().all()
    assert len(remaining) == 1


async def test_cleanup_does_not_delete_recent_unverified_users(auth_service, db_session):
    await make_user(db_session, username="recent", email="r@x.com",
                     is_active=False, days_old=1)

    deleted = await auth_service.cleanup_unverified_users()
    assert deleted == 0


async def test_cleanup_only_deletes_matching_users(auth_service, db_session):
    await make_user(db_session, username="old_unverified",
                     email="ou@x.com", is_active=False, days_old=30)
    await make_user(db_session, username="old_verified",
                     email="ov@x.com", is_active=True, days_old=30)
    await make_user(db_session, username="recent_unverified",
                     email="ru@x.com", is_active=False, days_old=1)
    await make_user(db_session, username="recent_verified",
                     email="rv@x.com", is_active=True, days_old=1)

    deleted = await auth_service.cleanup_unverified_users()
    assert deleted == 1

    remaining = {
        u.username for u in
        (await db_session.execute(select(User))).scalars().all()
    }
    assert remaining == {"old_verified", "recent_unverified", "recent_verified"}