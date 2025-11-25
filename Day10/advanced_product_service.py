# src/inventory_system/services/advanced_product_service.py
import logging
from typing import List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.inventory import Product
from ..repositories.product_repository import ProductRepository
from ..schemas.product import ProductCreate

logger = logging.getLogger(__name__)


class AdvancedProductService:
    """Service layer with richer error handling and domain logic."""

    def __init__(self, session: Session) -> None:
        self.repository = ProductRepository(session)
        self.session = session

    def create_product(
        self, product_data: ProductCreate
    ) -> Tuple[Optional[Product], Optional[str]]:
        """Create a product with comprehensive error handling.

        Returns:
            Tuple[Product | None, str | None]: (product, error_message)
        """
        try:
            # Validate business rules
            if product_data.price <= 0:
                return None, "Price must be greater than zero"

            if product_data.quantity < 0:
                return None, "Quantity cannot be negative"

            product = Product(**product_data.model_dump())
            created_product = self.repository.create(product)
            logger.info("Created product", extra={"product_id": created_product.id})
            return created_product, None

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(
                "Database error creating product",
                extra={"error": str(e)},
            )
            return None, "Database error occurred"
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error creating product",
                extra={"error": str(e)},
            )
            return None, "Unexpected error occurred"

    def bulk_update_quantities(
        self, updates: List[Tuple[int, int]]
    ) -> Tuple[int, List[str]]:
        """Bulk update product quantities with transaction safety.

        Args:
            updates: list of (product_id, new_quantity)

        Returns:
            Tuple[int, List[str]]: (success_count, errors)
        """
        errors: List[str] = []
        success_count = 0

        try:
            for product_id, new_quantity in updates:
                product = self.repository.get_by_id(product_id)
                if not product:
                    errors.append(f"Product {product_id} not found")
                    continue

                if new_quantity < 0:
                    errors.append(f"Invalid quantity for product {product_id}")
                    continue

                product.quantity = new_quantity
                success_count += 1

            self.session.commit()
            logger.info(
                "Bulk update completed",
                extra={
                    "success_count": success_count,
                    "error_count": len(errors),
                },
            )

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(
                "Database error in bulk update",
                extra={"error": str(e)},
            )
            errors.append("Transaction failed - all changes rolled back")

        return success_count, errors

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products whose quantity is below or equal to the given threshold."""
        all_products = self.repository.get_all()
        return [p for p in all_products if p.quantity <= threshold]

    def apply_price_increase(
        self, category: str, percentage: float
    ) -> Tuple[int, List[str]]:
        """Apply percentage price increase to products in a given category.

        Returns:
            Tuple[int, List[str]]: (updated_count, errors)
        """
        if percentage <= 0:
            return 0, ["Percentage must be positive"]

        try:
            products = self.repository.get_by_category(category)
            updated_count = 0
            errors: List[str] = []

            for product in products:
                try:
                    new_price = product.price * (1 + percentage / 100)
                    self.repository.update(product.id, {"price": new_price})
                    updated_count += 1
                except Exception as e:  # noqa: BLE001
                    errors.append(
                        f"Failed to update product {product.id}: {str(e)}",
                    )

            self.session.commit()
            logger.info(
                "Price increase applied",
                extra={
                    "category": category,
                    "percentage": percentage,
                    "updated_count": updated_count,
                    "error_count": len(errors),
                },
            )
            return updated_count, errors

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(
                "Database error applying price increase",
                extra={"error": str(e)},
            )
            return 0, ["Transaction failed - all changes rolled back"]
