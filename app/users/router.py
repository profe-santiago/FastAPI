from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.services import UserService
from app.users.schemas import UserCreate, UserUpdate, UserResponse
from app.auth.dependencies import verify_token, require_role
from app.auth.schemas import TokenPayload

router = APIRouter(prefix="/users", tags=["Users"])


# Solo admin puede ver todos los usuarios
@router.get("/", response_model=list[UserResponse], dependencies=[Depends(require_role("admin"))])
def get_all(db: Session = Depends(get_db)):
    return UserService(db).get_all()


# El usuario puede ver su propia info — admin puede ver cualquiera
@router.get("/{user_id}", response_model=UserResponse)
def get_by_id(user_id: int, db: Session = Depends(get_db), current_user: TokenPayload = Depends(verify_token)):
    if current_user.role != "admin" and current_user.sub != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para ver este usuario")
    return UserService(db).get_by_id(user_id)


# Solo admin puede crear usuarios
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))])
def create(data: UserCreate, db: Session = Depends(get_db)):
    return UserService(db).create(data)


# Solo admin puede editar usuarios
@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
def update(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    return UserService(db).update(user_id, data)


# Solo admin puede desactivar usuarios
@router.post("/{user_id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
def deactivate(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).deactivate(user_id)


# Solo admin puede eliminar usuarios
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).delete(user_id)
