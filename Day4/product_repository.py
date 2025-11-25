# src/inventory_system/repositories/product_repository.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.inventory import Product
from .base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.model = Product

    def get_by_id(self, id: int) -> Optional[Product]:
        return self.session.query(Product).filter(Product.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.session.query(Product).offset(skip).limit(limit).all()

    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update(self, id: int, product_data: dict) -> Optional[Product]:
        product = self.get_by_id(id)
        if product:
            for key, value in product_data.items():
                setattr(product, key, value)
            self.session.commit()
            self.session.refresh(product)
        return product

    def delete(self, id: int) -> bool:
        product = self.get_by_id(id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False

    def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        return (
            self.session.query(Product)
            .filter(Product.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Product]:
        return (
            self.session.query(Product)
            .filter(Product.name.ilike(f"%{name}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_quantity(self, id: int, quantity: int) -> Optional[Product]:
        product = self.get_by_id(id)
        if product:
            product.quantity = quantity
            self.session.commit()
            self.session.refresh(product)
        return product
