from datetime import datetime, timedelta
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(settings.secret_key)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_session_token(username: str) -> str:
    payload = {"sub": username, "iat": datetime.utcnow().isoformat()}
    return serializer.dumps(payload)


def verify_session_token(token: str, max_age_seconds: int = 60 * 60 * 12) -> str | None:
    try:
        payload = serializer.loads(token, max_age=max_age_seconds)
        return payload.get("sub")
    except (BadSignature, SignatureExpired):
        return None
