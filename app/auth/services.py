from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from app.config import settings
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserResponse
from app.auth.schemas import RegisterRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        return {"access_token": self._create_token(user), "token_type": "bearer"}

    def register(self, data: RegisterRequest) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        # Forzamos role="user" — el cliente no puede elegir su propio rol
        user_data = UserCreate(
            name=data.name,
            email=data.email,
            password=self.hash_password(data.password),
            role="user"
        )
        return self.repo.create(user_data)

    def _create_token(self, user) -> str:
        payload = {
            "sub": str(user.id),
            "role": user.role,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
