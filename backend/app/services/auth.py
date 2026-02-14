from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User, UserRole

settings = get_settings()


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    @staticmethod
    def create_access_token(user_id: UUID, role: UserRole) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "role": role.value,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: UUID) -> str:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> User:
        user_count = db.query(User).count()
        role = UserRole.admin if user_count == 0 else UserRole.standard

        user = User(
            username=username,
            email=email,
            hashed_password=AuthService.hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        user = AuthService.get_user_by_username(db, username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
