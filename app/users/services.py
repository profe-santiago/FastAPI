from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserResponse

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
        return self.repo.create(data)

    def deactivate(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self.repo.deactivate(user)