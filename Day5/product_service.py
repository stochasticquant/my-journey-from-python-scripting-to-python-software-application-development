# src/inventory_system/services/product_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.inventory import Product
from ..repositories.product_repository import ProductRepository
from ..schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: Session) -> None:
        self.repository = ProductRepository(session)

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.repository.get_by_id(product_id)

    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.get_all(skip, limit)

    def create_product(self, product_data: ProductCreate) -> Product:
        product = Product(**product_data.model_dump())
        return self.repository.create(product)

    def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        update_data = product_data.model_dump(exclude_unset=True)
        return self.repository.update(product_id, update_data)

    def delete_product(self, product_id: int) -> bool:
        return self.repository.delete(product_id)

    def get_products_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.get_by_category(category, skip, limit)

    def search_products(self, name: str, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.search_by_name(name, skip, limit)

    def update_product_quantity(self, product_id: int, quantity: int) -> Optional[Product]:
        return self.repository.update_quantity(product_id, quantity)

    def check_stock_level(self, product_id: int, required_quantity: int) -> bool:
        product = self.get_product(product_id)
        if not product:
            return False
        return product.quantity >= required_quantity
