from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import entities  # noqa: F401
from app.models.entities import User
from app.core.config import settings


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == settings.admin_username).first()
        if not exists:
            db.add(User(username=settings.admin_username, password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("DB initialized")
