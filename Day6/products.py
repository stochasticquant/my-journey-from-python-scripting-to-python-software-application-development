# src/inventory_system/api/products.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..config.database import db_manager
from ..schemas.product import Product, ProductCreate, ProductUpdate
from ..services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def get_db():
    """Dependency to get database session"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    """Create a new product"""
    return service.create_product(product_data)


@router.get("/", response_model=List[Product])
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ProductService = Depends(get_product_service),
):
    """Get all products with pagination"""
    return service.get_products(skip, limit)


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    """Get a specific product by ID"""
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    """Update a product"""
    product = service.update_product(product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    """Delete a product"""
    if not service.delete_product(product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


@router.get("/category/{category}", response_model=List[Product])
def get_products_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ProductService = Depends(get_product_service),
):
    """Get products by category"""
    return service.get_products_by_category(category, skip, limit)


@router.get("/search/{name}", response_model=List[Product])
def search_products(
    name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ProductService = Depends(get_product_service),
):
    """Search products by name"""
    return service.search_products(name, skip, limit)
