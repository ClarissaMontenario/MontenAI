
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from dotenv import load_dotenv

load_dotenv()


password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60


def get_secret_key():
    secret = os.getenv("SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "SECRET_KEY não configurada nas variáveis de ambiente."
        )

    return secret


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "typ": "user",
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        get_secret_key(),
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        get_secret_key(),
        algorithms=[ALGORITHM]
    )

def create_guest_token():
    """Cria um token temporário para visitantes."""

    import uuid

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=2)

    payload = {
        "sub": f"guest:{uuid.uuid4()}",
        "typ": "guest",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        get_secret_key(),
        algorithm=ALGORITHM
    )