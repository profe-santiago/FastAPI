from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import AuthService
from app.auth.schemas import TokenResponse, RegisterRequest
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return AuthService(db).login(form.username, form.password)


# Endpoint público — no requiere token
# El rol siempre será "user" — nunca se puede registrar como admin desde aquí
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(data)
