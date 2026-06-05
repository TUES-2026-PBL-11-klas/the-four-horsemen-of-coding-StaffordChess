from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

mail = FastMail(conf)


async def send_verification_email(recipient: str, token: str) -> None:
    body = f"""
    <h2>StaffordChess - Verify your email</h2>
    <p>Your verification code is: <b>{token}</b></p>
    <p>This code expires in {settings.VERIFICATION_EXPIRE_MINUTES} minutes.</p>
    """
    message = MessageSchema(
        subject="StaffordChess - Verify your email",
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
    )
    await mail.send_message(message)