
# Day 6 – FastAPI Implementation

> Goal: Build a **FastAPI** layer on top of your service and repository layers, exposing a clean, type-safe, and well-documented REST API.

---

## 1. FastAPI and Modern Python Web Development

### What is FastAPI?

**FastAPI** is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.

### Traditional vs FastAPI Approach

```python
# Traditional Flask approach (what you might know)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()  # Manual JSON parsing
    # No automatic validation
    if "name" not in data:
        return jsonify({"error": "Name required"}), 400

    product = Product(name=data["name"], price=data["price"])
    # Manual serialization
    return jsonify({"id": product.id, "name": product.name})
```

```python
# FastAPI approach (modern)
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ProductCreate(BaseModel):
    name: str
    price: float

@app.post("/products")
def create_product(product_data: ProductCreate) -> "Product":
    # Automatic JSON parsing, validation, and serialization
    product = product_service.create_product(product_data)
    return product  # Automatically serialized to JSON
```

### Key FastAPI Features

- **Automatic API documentation** (Swagger UI and ReDoc).
- **Type validation** using Pydantic.
- **Dependency injection system**.
- **Async support** out of the box.
- **Standards-based** (OpenAPI, JSON Schema).

---

## 2. API Routes and RESTful Design

### What is REST?

**REST (Representational State Transfer)** is an architectural style for designing networked applications based on resources and standard HTTP methods.

### RESTful Principles in Our Implementation

```python
# CRUD operations mapped to HTTP methods
@router.post("/products")        # CREATE
@router.get("/products")         # READ (list)
@router.get("/products/{id}")    # READ (single)
@router.put("/products/{id}")    # UPDATE (replace/modify)
@router.delete("/products/{id}") # DELETE
```

### REST Best Practices

- **Resource-oriented URLs** – `/products`, `/products/1`.
- **HTTP methods** – `POST` (create), `GET` (read), `PUT` (update), `DELETE` (delete).
- **Status codes** – `200` (OK), `201` (Created), `404` (Not Found), etc.
- **JSON responses** – Consistent data format with clear schemas.

---

## 3. FastAPI Dependency Injection System

### What is Dependency Injection in FastAPI?

FastAPI has a built-in **dependency injection** system that handles passing dependencies (like database sessions or services) to your route functions.

### Without Dependency Injection

```python
@app.get("/products")
def get_products():
    session = get_db_session()  # Manual dependency management
    try:
        service = ProductService(session)
        return service.get_products()
    finally:
        session.close()
```

### With Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    session = db_manager.get_session()
    try:
        yield session  # Yield makes this a generator dependency
    finally:
        session.close()

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    # FastAPI automatically calls get_db() and passes the result
    service = ProductService(db)
    return service.get_products()
```

### How Dependency Injection Works

1. FastAPI sees a parameter with `Depends(...)`.
2. It calls the dependency function (`get_db`).
3. It passes the result to your route function.
4. It handles cleanup after the request (via `yield` and `finally`).

---

## 4. Path Parameters, Query Parameters, and Request Body

FastAPI distinguishes **three** types of parameters:

### Path Parameters

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    # FastAPI converts and validates product_id as int
    return product_service.get_product(product_id)
```

### Query Parameters

```python
from fastapi import Query

@app.get("/products")
def get_products(
    skip: int = Query(0, ge=0),                  # Must be >= 0
    limit: int = Query(100, ge=1, le=1000),      # Between 1 and 1000
):
    return product_service.get_products(skip, limit)
```

### Request Body

```python
@app.post("/products")
def create_product(product_data: ProductCreate):
    # product_data is a validated Pydantic model
    return product_service.create_product(product_data)
```

Each parameter type (path, query, body) is handled differently, but all benefit from automatic validation and documentation.

---

## 5. APIRouter and Modular Applications

### What is `APIRouter`?

`APIRouter` lets you **modularize** your application by splitting routes into separate modules.

### Without APIRouter

```python
# All routes in one file
app = FastAPI()

@app.get("/products")
def get_products(): ...

@app.post("/products")  
def create_product(): ...

@app.get("/customers")
def get_customers(): ...
```

### With APIRouter

```python
# products.py
from fastapi import APIRouter

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
def get_products(): ...

@router.post("/")
def create_product(): ...

# customers.py  
router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/")
def get_customers(): ...

# main.py
from fastapi import FastAPI
from app.api import products, customers

app = FastAPI()
app.include_router(products.router)
app.include_router(customers.router)
```

Benefits:

- Cleaner structure for large applications.
- Logical grouping by domain (products, customers, orders, etc.).
- Better organization for testing and maintenance.

---

## 6. FastAPI Application Setup

Let’s examine the main application setup using FastAPI’s lifespan events.

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs when application starts
    db_manager.setup()
    db_manager.create_tables()
    yield  # Application runs here
    # Shutdown: runs when application stops
    # Close database connections or other resources if needed

app = FastAPI(
    title="Inventory Management System",
    description="Professional inventory management API", 
    version="1.0.0",
    lifespan=lifespan,  # Modern replacement for @app.on_event("startup")
)
```

### Lifespan Events

- **Startup** – Initialize database, create tables, warm up caches, etc.
- **Shutdown** – Clean up resources (close connections, flush logs, etc.).

---

## 7. Dependency Injection Chain

Let’s trace through our dependency chain for a typical endpoint:

```python
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    session = db_manager.get_session()
    try:
        yield session  # Provides database session
    finally:
        session.close()  # Always closes session

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)  # Creates service with database session

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),  # FastAPI injects service
):
    return service.get_product(product_id)
```

### Dependency Chain

```text
HTTP Request
  → get_product() needs service
  → get_product_service() needs db
  → get_db() creates Session
```

FastAPI resolves and wires everything together automatically.

---

## 8. Router Implementation (Products Example)

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    """Create a new product"""
    return service.create_product(product_data)

@router.get("/", response_model=List[Product])
def get_products(
    skip: int = Query(0, ge=0),                     # ge=0: greater than or equal to 0
    limit: int = Query(100, ge=1, le=1000),         # 1 <= limit <= 1000
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
```

---

## 9. Error Handling with `HTTPException`

### Converting Business Errors to HTTP Responses

```python
from fastapi import HTTPException, status

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    product = service.get_product(product_id)
    if not product:
        # Convert domain/business error to HTTP response
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product
```

### Common HTTP Status Codes

- `200 OK` – Successful GET request.
- `201 Created` – Resource successfully created (POST).
- `400 Bad Request` – Invalid input data.
- `404 Not Found` – Resource does not exist.
- `500 Internal Server Error` – Server-side error.

You can also define **custom exception handlers** for more advanced error handling.

---

## 10. Query Parameter Validation

FastAPI can validate query parameters directly via type hints and `Query`:

```python
from fastapi import Query

@router.get("/search/{name}", response_model=List[Product])
def search_products(
    name: str,
    skip: int = Query(0, ge=0),                # Must be >= 0
    limit: int = Query(100, ge=1, le=1000),    # Must be between 1 and 1000
    service: ProductService = Depends(get_product_service),
):
    """
    Query parameters with validation:
    - skip: must be greater than or equal to 0
    - limit: must be between 1 and 1000
    """
    return service.search_products(name, skip, limit)
```

Invalid values (e.g., `limit=-1`) automatically result in a **422 Unprocessable Entity** response with detailed error messages.

---

## 11. Response Model and Serialization

### Automatic Response Serialization

```python
@router.post("/", response_model=Product)
def create_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    product = service.create_product(product_data)
    # FastAPI automatically converts SQLAlchemy model to Pydantic model
    # using response_model=Product and from_attributes=True
    return product
```

### How It Works

1. Service returns a **SQLAlchemy model** instance.
2. FastAPI sees `response_model=Product`.
3. It uses Pydantic (with `from_attributes=True`) to build a `Product` DTO.
4. It serializes the DTO to **JSON** for the HTTP response.

You get:

- Type safety.
- Consistent response shapes.
- Automatic documentation for all responses.

---

## 12. Common Questions

**Q: Why use dependency injection instead of global variables?**  
**A:** Dependency injection makes dependencies **explicit** and **testable**. Global variables make it harder to control or replace dependencies in tests or different environments.

---

**Q: What's the difference between PUT and PATCH?**  
**A:**

- `PUT` – Replace the entire resource (full update).
- `PATCH` – Partially update the resource (only some fields).

In many simple APIs, we implement partial update behavior even with `PUT`, but it’s better to be explicit if you support true `PATCH` semantics.

---

**Q: Why raise `HTTPException` instead of returning error dicts?**  
**A:** `HTTPException` is FastAPI’s standard way to return errors. It:

- Sets the appropriate status code.
- Produces a consistent JSON error structure.
- Integrates with automatic documentation.

---

**Q: When should I use path parameters vs query parameters?**  

- **Path parameters** – Identify specific resources (`/products/1`).  
- **Query parameters** – Filtering, sorting, pagination (`/products?category=electronics&limit=10`).

---

**Q: What are the `tags` parameter in `APIRouter` for?**  
**A:** Tags group related endpoints in the automatic API documentation (Swagger UI). They improve navigation and readability.

---

## 13. Testing the API

FastAPI provides a built-in `TestClient` for testing endpoints.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_product():
    response = client.post(
        "/products/",
        json={
            "name": "Test Product",
            "price": 19.99,
            "quantity": 10,
            "category": "Test",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert "id" in data

def test_get_product_not_found():
    response = client.get("/products/999")
    assert response.status_code == 404
```

With the service and repository layers already abstracted, you can also mock dependencies to test just the API behavior.

---

## 14. Automatic API Documentation

One of FastAPI’s **killer features** is automatic documentation.

After running your application (e.g., `uvicorn app.main:app --reload`):

- **Swagger UI** – <http://localhost:8000/docs>
- **ReDoc** – <http://localhost:8000/redoc>

The documentation includes:

- All endpoints and HTTP methods.
- Request and response schemas.
- Query/path parameter validation.
- Try-it-out interface for manual testing.

---

## 15. Further Reading

### Essential References

- FastAPI Documentation – <https://fastapi.tiangolo.com/>
- FastAPI Tutorial – <https://fastapi.tiangolo.com/tutorial/>
- REST API Design Guide – <https://restfulapi.net/>
- HTTP Status Codes – <https://httpstatuses.com/>

### Deep Dive Topics

- FastAPI Dependencies – <https://fastapi.tiangolo.com/tutorial/dependencies/>
- Background Tasks – <https://fastapi.tiangolo.com/tutorial/background-tasks/>
- Middleware – <https://fastapi.tiangolo.com/tutorial/middleware/>
- WebSockets – <https://fastapi.tiangolo.com/advanced/websockets/>

---

## 16. Practice Exercises (Day 6)

1. **Add more API endpoints** – e.g., category-specific routes, bulk operations, advanced searches.
2. **Implement authentication** using FastAPI’s security utilities (OAuth2, JWT, API keys).
3. **Add middleware** for logging, correlation IDs, or rate limiting.
4. **Create custom exception handlers** for business exceptions (like `ProductAlreadyExistsError`).
5. **Add response headers and cookies** where appropriate (e.g., pagination metadata).

---

## 17. Key Takeaways

- FastAPI uses **type hints** for automatic validation, serialization, and documentation.
- **Dependency injection** makes dependencies explicit and easy to test.
- `APIRouter` enables **modular API design**.
- `HTTPException` is the idiomatic way to convert errors into HTTP responses.
- Automatic API documentation dramatically improves developer experience.
- Path parameters, query parameters, and request bodies each serve specific purposes in REST APIs.

---

## 18. Coming Up Next (Day 7)

Tomorrow we’ll implement **comprehensive testing** (unit, integration, and API tests) to ensure our application works correctly and is safe to refactor.
