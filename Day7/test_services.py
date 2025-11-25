# tests/unit/test_services.py
from src.inventory_system.schemas.product import ProductCreate
from src.inventory_system.services.product_service import ProductService


def test_create_product(test_session):
    service = ProductService(test_session)
    product_data = ProductCreate(
        name="Test Product",
        description="Test Description",
        price=19.99,
        quantity=100,
        category="Electronics",
    )

    product = service.create_product(product_data)

    assert product.id is not None
    assert product.name == "Test Product"
    assert product.price == 19.99
    assert product.quantity == 100


def test_get_product(test_session):
    service = ProductService(test_session)
    product_data = ProductCreate(
        name="Test Product",
        price=19.99,
        quantity=100,
        category="Electronics",
    )

    created_product = service.create_product(product_data)
    retrieved_product = service.get_product(created_product.id)

    assert retrieved_product is not None
    assert retrieved_product.id == created_product.id
    assert retrieved_product.name == "Test Product"
