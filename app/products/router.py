from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.products.services import ProductService
from app.products.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.auth.dependencies import verify_token, require_role

router = APIRouter(prefix="/products", tags=["Products"])


# Cualquier usuario autenticado puede ver el catálogo
@router.get("/", response_model=list[ProductResponse], dependencies=[Depends(verify_token)])
def get_all(db: Session = Depends(get_db)):
    return ProductService(db).get_all()


# Cualquier usuario autenticado puede ver un producto
@router.get("/{product_id}", response_model=ProductResponse, dependencies=[Depends(verify_token)])
def get_by_id(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).get_by_id(product_id)


# Solo admin puede crear productos
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role("admin"))])
def create(data: ProductCreate, db: Session = Depends(get_db)):
    return ProductService(db).create(data)


# Solo admin puede editar productos
@router.put("/{product_id}", response_model=ProductResponse,
            dependencies=[Depends(require_role("admin"))])
def update(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    return ProductService(db).update(product_id, data)


# Solo admin puede eliminar productos
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role("admin"))])
def delete(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).delete(product_id)
