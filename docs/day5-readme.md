
# Day 5 – Service Layer & Business Logic

> Goal: Introduce the **Service Layer Pattern** to encapsulate business logic, use Pydantic DTOs for data transfer, and keep a clean separation between API, services, and repositories.

---

## 1. Service Layer Pattern Explained

### What is the Service Layer?

The **Service Layer** is a pattern that defines an application's boundary and its set of available operations from the perspective of interfacing client layers. It encapsulates the application's **business logic**.

**Analogy – Restaurant:**

- **Repository Pattern** = Kitchen staff who handle ingredients (data access).
- **Service Layer** = Chef who coordinates cooking (business logic).
- **API Layer** = Waiter who takes orders and serves food (interface to clients).

### Without Service Layer

Business logic is mixed directly into the API:

```python
# API endpoint directly using repository (mixing concerns)
@app.post("/products")
def create_product(product_data: dict):
    # Data validation, business rules, and data access all mixed together
    if product_data["price"] <= 0:
        raise HTTPException(400, "Price must be positive")

    product = Product(**product_data)
    return product_repository.create(product)
```

### With Service Layer

Clean separation: API handles HTTP concerns, service handles business logic.

```python
# API only handles HTTP and I/O concerns
@app.post("/products")
def create_product(product_data: ProductCreate):
    return product_service.create_product(product_data)

# Service handles business logic
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def create_product(self, product_data: ProductCreate) -> Product:
        if product_data.price <= 0:
            raise ValueError("Price must be positive")
        # Business logic here
        product = Product(**product_data.model_dump())
        return self.repository.create(product)
```

---

## 2. Data Transfer Objects (DTOs) with Pydantic

### What are DTOs?

**DTOs (Data Transfer Objects)** are objects that carry data between processes or layers. Here, they carry data between:

- API layer ⇄ Service layer  
- Service layer ⇄ Clients

We use **Pydantic models** as DTOs.

### Pydantic Models as DTOs

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int
    category: str

class ProductCreate(ProductBase):
    # Used for creating new products
    # All fields required (inherited from base)
    pass

class ProductUpdate(BaseModel):
    # Used for updating existing products  
    # All fields optional - only update what's provided
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    category: Optional[str] = None

class Product(ProductBase):
    # Used for returning products (includes database fields)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode
```

### Why different DTOs for different operations?

- **Validation** – Different rules for create vs update.
- **Security** – Control which fields can be set by the client.
- **Clarity** – Clear intent for each operation (`ProductCreate`, `ProductUpdate`, `Product`).

---

## 3. Pydantic Model Config and ORM Mode

### What is `from_attributes=True`?

This enables Pydantic to read data from ORM objects (like SQLAlchemy models), not just dictionaries.

```python
# Without from_attributes=True, this would fail:
sqlalchemy_product = session.query(Product).first()
# product_schema = Product.model_validate(sqlalchemy_product)  # Error

# With from_attributes=True in model_config:
product_schema = Product.model_validate(sqlalchemy_product)  # Works!
```

### How it works conceptually

```python
# Equivalent to manually mapping fields:
sqlalchemy_product = session.query(Product).first()

pydantic_product = Product(
    id=sqlalchemy_product.id,
    name=sqlalchemy_product.name,
    description=sqlalchemy_product.description,
    price=sqlalchemy_product.price,
    quantity=sqlalchemy_product.quantity,
    category=sqlalchemy_product.category,
    created_at=sqlalchemy_product.created_at,
    updated_at=sqlalchemy_product.updated_at,
)
```

`from_attributes=True` tells Pydantic: “You may read attributes directly from ORM instances.”

---

## 4. Business Logic vs Data Access

### Separation of Concerns

- **Repository** – *How* to access data (e.g., `SELECT * FROM products WHERE category = ?`).
- **Service** – *What to do* with data (“Apply discount to all products in electronics category”).

### Business Logic Examples

```python
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def apply_discount(self, category: str, discount_percent: float) -> None:
        """Business logic: Apply discount to all products in a category"""
        products = self.repository.get_by_category(category)
        for product in products:
            new_price = product.price * (1 - discount_percent / 100)
            self.repository.update(product.id, {"price": new_price})

    def check_stock_level(self, product_id: int, required_quantity: int) -> bool:
        """Business logic: Check if we have enough stock"""
        product = self.repository.get_by_id(product_id)
        return product.quantity >= required_quantity if product else False
```

Business logic is now **centralized** in one place (services), not scattered across controllers or repositories.

---

## 5. Dependency Injection in Services

### Constructor Injection

```python
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository  # Dependency injected

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.repository.get_by_id(product_id)
```

### Why inject repositories?

- **Testability** – Can pass in a mock repository for unit tests.
- **Flexibility** – Can swap repository implementations (SQL, in-memory, cached, etc.).
- **Single Responsibility** – Service focuses only on business logic, not on creating its dependencies.

---

## 6. Pydantic Schema Design (In Detail)

Let’s examine the schema design philosophy:

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    # Common fields for create, update, and response
    name: str
    description: Optional[str] = None
    price: float
    quantity: int
    category: str

class ProductCreate(ProductBase):
    # For creating products - same as base but with explicit intent
    pass

class ProductUpdate(BaseModel):
    # For updating products - all fields optional
    # Note: Doesn't inherit from ProductBase because we don't want required fields
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    category: Optional[str] = None

class Product(ProductBase):
    # Response model - includes database generated fields
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # Crucial for ORM compatibility
```

### Key Design Decisions

- `ProductBase` – Common validation rules for all operations.
- `ProductCreate` – Clear intent: used only for creation.
- `ProductUpdate` – All fields optional for **partial updates** (`PATCH`-like behavior).
- `Product` – Read model including database-generated fields (like `id`, timestamps).

---

## 7. Service Layer Implementation

Now let’s break down the `ProductService`:

```python
from typing import List, Optional
from sqlalchemy.orm import Session

class ProductService:
    def __init__(self, session: Session):
        # Dependency injection: service gets what it needs
        self.repository = ProductRepository(session)

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a single product by ID"""
        return self.repository.get_by_id(product_id)

    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get products with pagination"""
        return self.repository.get_all(skip, limit)

    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product - business logic entry point"""
        # Convert Pydantic model to SQLAlchemy model
        product = Product(**product_data.model_dump())
        return self.repository.create(product)

    def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product - handles partial updates"""
        # Convert Pydantic model to dict, exclude unset values
        update_data = product_data.model_dump(exclude_unset=True)
        return self.repository.update(product_id, update_data)

    def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        return self.repository.delete(product_id)
```

### Advanced Service Methods

```python
    def get_products_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """Business method: Get products by category"""
        return self.repository.get_by_category(category, skip, limit)

    def search_products(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """Business method: Search products by name"""
        return self.repository.search_by_name(name, skip, limit)

    def update_product_quantity(self, product_id: int, quantity: int) -> Optional[Product]:
        """Business method: Update product quantity with validation"""
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        return self.repository.update_quantity(product_id, quantity)

    def check_stock_level(self, product_id: int, required_quantity: int) -> bool:
        """Business logic: Check if we have enough stock for an order"""
        product = self.get_product(product_id)
        if not product:
            return False
        return product.quantity >= required_quantity
```

---

## 8. Model Conversion Patterns

### Pydantic → SQLAlchemy

```python
# Using model_dump()
product_data = ProductCreate(
    name="Laptop",
    price=999.99,
    quantity=10,
    category="Electronics",
)

product_model = Product(**product_data.model_dump())
```

### SQLAlchemy → Pydantic

```python
# Using Pydantic's ORM mode
product_model = session.query(Product).first()
product_schema = Product.model_validate(product_model)

# product_schema is now a Pydantic Product DTO ready for the API response
```

This pattern ensures a clean separation between **domain models (SQLAlchemy)** and **API contracts (Pydantic)**.

---

## 9. Error Handling in Services

Services should raise **domain/business exceptions**, not HTTP exceptions. HTTP concerns belong in the API layer.

```python
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def create_product(self, product_data: ProductCreate) -> Product:
        # Business validation
        if product_data.price <= 0:
            raise ValueError("Product price must be positive")

        if product_data.quantity < 0:
            raise ValueError("Product quantity cannot be negative")

        # Check for duplicate names (business rule)
        existing = self.repository.search_by_name(product_data.name)
        if existing:
            raise ValueError(f"Product with name '{product_data.name}' already exists")

        product = Product(**product_data.model_dump())
        return self.repository.create(product)
```

The API layer will later catch these exceptions and map them to appropriate HTTP status codes.

---

## 10. Common Questions

**Q: Why not put validation in Pydantic models?**  
**A:**

- Pydantic handles **data validation** (structure & types).
- Services handle **business validation** (rules & constraints).

Example:

- Pydantic: “`price` must be a float.”
- Service: “`price` must be positive and less than 10,000.”

---

**Q: When should I create a new service vs adding methods to an existing one?**  
Group related business operations:

- `ProductService` – Product-related logic.
- `OrderService` – Order-related logic.
- `CustomerService` – Customer-related logic.

If a service becomes too large or conceptually mixed, split it.

---

**Q: What about transactions that span multiple services?**  
Create a **higher-level orchestration service** or use the **Unit of Work** pattern to coordinate multiple repositories using the same session/transaction.

---

**Q: Why use `model_dump(exclude_unset=True)` for updates?**  
This ensures that only fields explicitly provided in the request are updated. Others remain unchanged.

---

**Q: Should services return Pydantic or SQLAlchemy models?**  
Typically:

- Services return **domain models** (SQLAlchemy).
- API layer converts them to **Pydantic DTOs** for responses.

This keeps the service layer independent of any specific API framework.

---

## 11. Testing Service Layer

Services are easy to test because of dependency injection.

```python
from unittest.mock import Mock
import pytest

def test_create_product():
    # Setup
    mock_repo = Mock(spec=ProductRepository)
    service = ProductService(mock_repo)
    product_data = ProductCreate(
        name="Test",
        price=10.0,
        quantity=5,
        category="Test",
    )

    # Execute
    service.create_product(product_data)

    # Verify
    mock_repo.create.assert_called_once()
    created_product = mock_repo.create.call_args[0][0]
    assert created_product.name == "Test"


def test_business_validation():
    mock_repo = Mock(spec=ProductRepository)
    service = ProductService(mock_repo)
    invalid_data = ProductCreate(
        name="Test",
        price=-10.0,
        quantity=5,
        category="Test",
    )

    with pytest.raises(ValueError, match="price must be positive"):
        service.create_product(invalid_data)
```

Because we injected the repository, we can test the service logic **without** touching a real database.

---

## 12. Further Reading

### Essential References

- Pydantic Documentation – <https://docs.pydantic.dev/>
- Service Layer Pattern – <https://martinfowler.com/eaaCatalog/serviceLayer.html>
- Data Transfer Object – <https://martinfowler.com/eaaCatalog/dataTransferObject.html>
- Dependency Injection – <https://en.wikipedia.org/wiki/Dependency_injection>

### Deep Dive Topics

- Hexagonal Architecture – <https://alistair.cockburn.us/hexagonal-architecture/>
- CQRS Pattern – <https://martinfowler.com/bliki/CQRS.html>
- Validation in Python (Pydantic validators) – <https://docs.pydantic.dev/latest/usage/validators/>

---

## 13. Practice Exercises (Day 5)

1. **Create a `CustomerService`** with business logic like `send_welcome_email()` (use a mock email sender).
2. **Implement inventory management business rules** (e.g., low stock alerts, minimum stock thresholds).
3. **Add complex validation** using Pydantic validators (e.g., combined constraints on fields).
4. **Write unit tests** for all service methods using mocked repositories.
5. (Optional) Introduce a simple `UnitOfWork` abstraction coordinating multiple repositories in one transaction.

---

## 14. Key Takeaways

- The **Service Layer** encapsulates business logic separate from data access and API concerns.
- **Pydantic schemas (DTOs)** define clear boundaries between layers.
- `from_attributes=True` enables seamless ORM → Pydantic conversion.
- Services use **dependency injection** for testability and flexibility.
- **Business validation** belongs in services; **data validation** belongs in Pydantic.
- Different DTOs (`Create`, `Update`, `Read`) provide clarity, safety, and better contracts.

---

## 15. Coming Up Next (Day 6)

Tomorrow we’ll build the **FastAPI layer** that exposes these services as RESTful endpoints and learn how to wire everything together end-to-end.
