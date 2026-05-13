from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.products.repositories import ProductRepository
from app.products.schemas import ProductCreate, ProductUpdate, ProductResponse


class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)

    def get_all(self) -> list[ProductResponse]:
        return self.repo.get_all()

    def get_by_id(self, product_id: int) -> ProductResponse:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return product

    def create(self, data: ProductCreate) -> ProductResponse:
        return self.repo.create(data)

    def update(self, product_id: int, data: ProductUpdate) -> ProductResponse:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        return self.repo.update(product, data)

    def delete(self, product_id: int) -> None:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        self.repo.delete(product)
