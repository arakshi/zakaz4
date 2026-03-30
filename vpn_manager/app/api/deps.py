from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_session_token
from app.models.entities import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    username = verify_session_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    return user
