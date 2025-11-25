
# Day 4 – Repository Pattern & Data Persistence

> Goal: Introduce the **Repository Pattern** to separate business logic from data access, improve testability, and create a clean persistence layer on top of SQLAlchemy.

---

## 1. Repository Pattern Explained

### What is the Repository Pattern?

The **Repository Pattern** is a design pattern that mediates between the domain (business logic) and data mapping layers, acting like an in-memory collection of domain objects.

**Analogy:** Think of a repository like a **library catalog system**:

- You don’t need to know where books are physically stored.
- You use a standard interface to find, check out, and return books.
- The catalog system handles all the complex storage details.

### Without Repository Pattern

Business logic directly coupled to database operations:

```python
# Business logic mixed with database code
def create_product(product_data):
    session = get_db_session()
    product = Product(**product_data)
    session.add(product)
    session.commit()  # Direct database access in business logic
    return product
```

### With Repository Pattern

Database access is abstracted behind a repository:

```python
# Clean separation
def create_product(product_data):
    product = Product(**product_data)
    return product_repository.create(product)  # Business logic doesn't know about database
```

The service layer (business logic) does **not** care how data is stored—only that the repository can create, fetch, update, and delete entities.

---

## 2. Abstraction and Dependency Inversion

### What is Abstraction?

**Abstraction** means hiding complex implementation details and exposing only the essential features through a clear interface.

### What is Dependency Inversion?

The principle that:

- High-level modules should not depend on low-level modules.
- Both should depend on **abstractions**.

The Repository Pattern implements both by:

- Defining **abstract repository interfaces**.
- Implementing concrete repositories that depend on the database.

```python
# Abstraction: BaseRepository defines WHAT we can do
from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass

# Concrete implementation: ProductRepository defines HOW we do it
from sqlalchemy.orm import Session

class ProductRepository(BaseRepository["Product"]):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: int) -> Optional["Product"]:
        return (
            self.session.query(Product)
            .filter(Product.id == id)
            .first()
        )
```

High-level code depends on `BaseRepository` (abstraction), not directly on SQLAlchemy or SQL Server.

---

## 3. Generic Types and Type Variables

### What are Generic Types?

**Generic types** let you write code that can work with different types while maintaining type safety.

### Type Variables Example

```python
from typing import TypeVar, Generic, List, Optional

# T is a type variable - it can be any type
T = TypeVar("T")

class BaseRepository(Generic[T]):
    # This repository can work with any type T
    def get_by_id(self, id: int) -> Optional[T]:
        pass

# When we inherit, we specify what T is
class ProductRepository(BaseRepository["Product"]):
    # Now T is Product in this class
    def get_by_id(self, id: int) -> Optional["Product"]:
        pass
```

### Benefits of Generics

- **Type Safety** – Python (and your IDE) knows the return type is `Product`, not just `Any`.
- **Code Reuse** – One base repository works for **all** entity types.
- **IDE Support** – Better autocomplete and static analysis.

---

## 4. Abstract Base Classes (ABC)

### What are ABCs?

**Abstract Base Classes (ABCs)** define a blueprint for other classes. They cannot be instantiated directly and require subclasses to implement abstract methods.

```python
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def create(self, entity: T) -> T:
        pass  # Subclasses MUST implement this method
```

### Why use ABCs?

- **Contract Enforcement** – Ensures all repositories share the same interface.
- **Clear Intent** – Makes it obvious which methods must be implemented.
- **Better Errors** – Python raises an error if abstract methods are not implemented.

---

## 5. Dependency Injection

### What is Dependency Injection?

**Dependency Injection (DI)** is a technique where an object receives the objects it depends on, instead of creating them itself.

### Without Dependency Injection

```python
class ProductService:
    def __init__(self):
        self.repository = ProductRepository()  # Creates dependency internally

    def get_product(self, id: int):
        return self.repository.get_by_id(id)
```

### With Dependency Injection

```python
class ProductService:
    def __init__(self, repository: "ProductRepository"):  # Dependency injected
        self.repository = repository

    def get_product(self, id: int):
        return self.repository.get_by_id(id)

# Usage
repository = ProductRepository(session)
service = ProductService(repository)  # Inject the dependency
```

### Benefits

- **Testability** – Easy to inject mock repositories for unit tests.
- **Flexibility** – Swap implementations (e.g., in-memory vs SQL) without changing business logic.
- **Decoupling** – Business logic doesn’t know or care about data access details.

---

## 6. Base Repository Implementation

Let’s break down an abstract base repository:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session

# T is a type variable that can be any model type
T = TypeVar("T")

class BaseRepository(Generic[T], ABC):
    def __init__(self, session: Session):
        self.session = session  # Dependency injection of database session

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key"""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    def update(self, id: int, entity_data: dict) -> Optional[T]:
        """Update entity by ID"""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        pass
```

### Key Points

- `Generic[T]` – Repository works with any model type.
- `ABC` – This is an abstract base class; can’t be instantiated directly.
- `@abstractmethod` – Subclasses **must** implement these methods.
- `session` is injected – Repository doesn’t create its own session (better control & testability).

---

## 7. Concrete Repository Implementation (ProductRepository)

Now let’s examine a real `ProductRepository` implementation:

```python
from typing import List, Optional
from sqlalchemy.orm import Session

class ProductRepository(BaseRepository["Product"]):
    def __init__(self, session: Session):
        super().__init__(session)  # Call parent constructor
        self.model = Product       # Specific model for this repository

    def get_by_id(self, id: int) -> Optional["Product"]:
        return (
            self.session.query(Product)
            .filter(Product.id == id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List["Product"]:
        return (
            self.session.query(Product)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, product: "Product") -> "Product":
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)  # Get updated values (like auto-increment ID)
        return product

    def update(self, id: int, product_data: dict) -> Optional["Product"]:
        product = self.get_by_id(id)
        if product:
            # Update only the provided fields
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
```

This repository knows how to work with `Product` entities using SQLAlchemy, and nothing else.

---

## 8. Repository-Specific Methods

One major benefit of the Repository Pattern is adding **domain-specific queries** in a single place:

```python
from typing import List, Optional

class ProductRepository(BaseRepository["Product"]):
    # ... standard CRUD methods ...

    def get_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> List["Product"]:
        return (
            self.session.query(Product)
            .filter(Product.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_name(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> List["Product"]:
        return (
            self.session.query(Product)
            .filter(Product.name.ilike(f"%{name}%"))  # Case-insensitive search
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_quantity(self, id: int, quantity: int) -> Optional["Product"]:
        product = self.get_by_id(id)
        if product:
            product.quantity = quantity
            self.session.commit()
            self.session.refresh(product)
        return product
```

These methods express **business concepts** (search, update stock) instead of low-level SQL.

---

## 9. Session Management

### Important: Repository methods don’t manage the session lifecycle.

```python
# GOOD: Session managed externally
def business_operation():
    session = db_manager.get_session()
    try:
        repo = ProductRepository(session)
        product = repo.get_by_id(1)
        # ... do more work, maybe with multiple repositories ...
        session.commit()  # Commit at business logic (service) level
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

```python
# BAD: Repository manages session internally
class BadRepository:
    def __init__(self):
        self.session = db_manager.get_session()  # Don't do this!
```

**Why?**

- You want **one transaction** that can span multiple repository operations.
- Business logic (service layer) should decide when to commit or rollback.

---

## 10. Common Questions

**Q: Why not put all database logic directly in services?**  
**A:** Separation of concerns. Services handle **business rules**, repositories handle **data access**. This makes both easier to test, change, and reason about.

---

**Q: When should I create a new repository method vs using existing ones?**  
Create repository methods for:

- Common queries used in multiple places.
- Complex queries with multiple filters/joins.
- Queries that represent **business concepts** (e.g., `get_low_stock_products`).

---

**Q: What about transactions that span multiple repositories?**  
Use the **same session** across multiple repositories. Manage the transaction (commit/rollback) in the **service** or higher-level orchestration code.

---

**Q: Why use abstract methods instead of just documenting the interface?**  
Abstract methods provide **runtime enforcement**. Python raises errors when:

- You don’t implement required methods.
- You try to instantiate an abstract class.

---

**Q: How do I handle bulk operations or complex joins?**  
Add specialized methods in your repositories. The pattern is flexible enough for:

- Bulk inserts/updates.
- Complex joins using SQLAlchemy Core or raw SQL.
- Custom query objects.

---

## 11. Testing Benefits

The Repository Pattern makes both **unit tests** and **integration tests** easier.

### Example: Testing with a Mock Repository

```python
from unittest.mock import Mock

def test_product_service():
    mock_repo = Mock(spec=ProductRepository)
    mock_repo.get_by_id.return_value = Product(id=1, name="Test")

    service = ProductService(mock_repo)
    result = service.get_product(1)

    assert result.name == "Test"
    mock_repo.get_by_id.assert_called_once_with(1)
```

### Example: Testing with Real Database (Integration Test)

```python
def test_product_repository_integration(test_session):
    repo = ProductRepository(test_session)
    product = Product(name="Test", price=10.0)

    created = repo.create(product)
    assert created.id is not None
    assert created.name == "Test"
```

With DI and repositories, you can easily swap between mocks (unit tests) and real DB (integration tests).

---

## 12. Further Reading

### Essential References

- Repository Pattern (Martin Fowler) – <https://martinfowler.com/eaaCatalog/repository.html>
- Python ABC Documentation – <https://docs.python.org/3/library/abc.html>
- Python Typing Generics – <https://docs.python.org/3/library/typing.html#generics>
- Dependency Injection Principles – <https://en.wikipedia.org/wiki/Dependency_injection>

### Deep Dive Topics

- Domain-Driven Design (DDD) – <https://domainlanguage.com/ddd/>
- Unit of Work Pattern – <https://martinfowler.com/eaaCatalog/unitOfWork.html>
- Test-Driven Development (TDD) – <https://en.wikipedia.org/wiki/Test-driven_development>

---

## 13. Practice Exercises (Day 4)

1. **Create a `CustomerRepository`** with methods like `get_by_email()`.
2. **Implement a Unit of Work pattern** that coordinates multiple repositories with a single session/transaction.
3. **Write tests** for `ProductRepository` using both mocks and a real database session.
4. **Extend `BaseRepository`** with a method `get_by_ids(ids: List[int])` and implement it for `ProductRepository`.
5. (Optional) Create an in-memory implementation of `ProductRepository` for faster, DB-free testing.

---

## 14. Key Takeaways

- The **Repository Pattern** separates data access from business logic.
- **Abstract Base Classes** enforce contracts between components.
- **Generic types** give you type safety and reusable infrastructure.
- **Dependency Injection** makes your code testable and flexible.
- **Session management** should happen at the service/business logic layer.
- Domain-specific query methods belong in **repositories**, not scattered across code.

---

## 15. Coming Up Next (Day 5)

Tomorrow we’ll build the **Service Layer** that uses these repositories to implement business logic and orchestrate workflows across multiple entities.
