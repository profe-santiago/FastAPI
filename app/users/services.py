from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserUpdate, UserResponse
from app.auth.services import AuthService


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_all(self) -> list[UserResponse]:
        return self.repo.get_all()

    def get_by_id(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    def create(self, data: UserCreate) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")
        data.password = AuthService.hash_password(data.password)
        return self.repo.create(data)

    def update(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self.repo.update(user, data)

    def deactivate(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self.repo.deactivate(user)

    def delete(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        self.repo.delete(user)
