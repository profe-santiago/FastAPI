from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.services import UserService
from app.users.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse])
def get_all(db: Session = Depends(get_db)):
    return UserService(db).get_all()

@router.get("/{user_id}", response_model=UserResponse)
def get_by_id(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).get_by_id(user_id)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(data: UserCreate, db: Session = Depends(get_db)):
    return UserService(db).create(data)

@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).deactivate(user_id)