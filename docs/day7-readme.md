
# Day 7 – Testing Implementation

> Goal: Design and implement a **testing strategy** for your application using pytest, following the Testing Pyramid, and combining unit, integration, and API tests.

---

## 1. Testing Pyramid and Testing Strategy

### What is the Testing Pyramid?

The **Testing Pyramid** is a strategy that suggests having many low-level **unit tests**, fewer **integration tests**, and even fewer **end-to-end (E2E)** tests.

```text
       /\
      /  \      E2E Tests (Few)
     /----\
    /      \    Integration Tests (Some)  
   /--------\
  /          \  Unit Tests (Many)
 /------------\
```

### Testing Pyramid in Practice

- **Unit Tests** – Test individual components in isolation (~70%).
- **Integration Tests** – Test interactions between components (~20%).
- **E2E Tests** – Test the entire system from a user perspective (~10%).

### Why This Distribution?

- **Speed** – Unit tests are very fast; E2E tests are slow.
- **Debugging** – Unit tests pinpoint failures more precisely.
- **Cost** – Unit tests are cheaper to write and maintain than E2E tests.

---

## 2. Unit Testing vs Integration Testing

### Unit Testing

- Tests individual **units of code** in isolation.
- Uses **mocks** to remove external dependencies.
- **Fast** to execute.
- Focuses on **business logic**.

```python
# Unit test example
def test_calculate_discount():
    calculator = PriceCalculator()
    result = calculator.calculate_discount(100, 10)  # No external dependencies
    assert result == 90
```

### Integration Testing

- Tests **interactions** between components.
- Uses **real dependencies** (database, APIs, etc.).
- Slower than unit tests.
- Focuses on integration correctness.

```python
# Integration test example  
def test_create_product_in_db(test_session):
    repo = ProductRepository(test_session)  # Real database session
    product = Product(name="Test", price=10.0)
    created = repo.create(product)  # Tests database interaction
    assert created.id is not None
```

Both are important: unit tests protect logic; integration tests validate how pieces work together.

---

## 3. Test Doubles: Mocks, Stubs, and Fakes

**Test Doubles** are objects that replace real dependencies in tests.

### Mocks

- Objects that **record interactions**.
- Used to verify **how** something is used.
- Example: “Did `get_by_id` get called with argument `1`?”

```python
from unittest.mock import Mock

mock_repo = Mock(spec=ProductRepository)
mock_repo.get_by_id.return_value = None

service = ProductService(mock_repo)
service.get_product(1)

mock_repo.get_by_id.assert_called_once_with(1)  # Verification
```

### Stubs

- Objects that provide **predefined responses**.
- Used to verify **what** is returned.

```python
stub_repo = Mock(spec=ProductRepository)
stub_repo.get_by_id.return_value = Product(id=1, name="Test")

service = ProductService(stub_repo)
result = service.get_product(1)

assert result.name == "Test"
```

### Fakes

- Working implementations with **simplified behavior**.
- Example: in-memory repository instead of real database.

```python
class FakeProductRepository:
    def __init__(self):
        self.products = {}

    def get_by_id(self, id):
        return self.products.get(id)
```

Fakes are great for fast tests that still exercise realistic flows.

---

## 4. pytest Framework Features

### Why pytest?

- Simple and expressive syntax.
- Powerful **fixtures**.
- Rich **plugin ecosystem**.
- Detailed failure reports.

### Fixtures

Fixtures provide reusable setup/teardown logic.

```python
import pytest

@pytest.fixture
def sample_product():
    return Product(name="Test", price=10.0)

def test_something(sample_product):  # Injected automatically
    assert sample_product.name == "Test"
```

### Parameterized Tests

Write one test, run it with multiple inputs.

```python
import pytest

@pytest.mark.parametrize("price,discount,expected", [
    (100, 10, 90),
    (50, 20, 40),
    (200, 0, 200),
])
def test_discount_calculation(price, discount, expected):
    result = calculate_discount(price, discount)
    assert result == expected
```

---

## 5. Test Configuration with `conftest.py`

### What is `conftest.py`?

A special file that pytest **automatically discovers**. It contains shared fixtures and configuration.

- Fixtures in `conftest.py` are available to all tests in that directory and subdirectories.
- Perfect for shared setup (database, HTTP client, etc.).

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    client = TestClient(app)
    yield client
    # Optional teardown
```

This avoids repeating setup logic in every test file.

---

## 6. Test Database Setup

Let’s examine a test database configuration using SQLAlchemy:

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.main import app

TEST_DATABASE_URL = (
    "mssql+pyodbc://sa:YourStrong!Passw0rd@localhost:1433/inventory_test"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)  # Create all tables
    return engine

@pytest.fixture(scope="function")
def test_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()  # Rollback instead of commit
        session.close()
```

### Why a Separate Test Database?

- **Isolation** – Tests don't interfere with development or production data.
- **Control** – Easy to reset database state.
- **Safety** – No accidental modifications of real data.

### Session Management in Tests

- `rollback()` – Undoes all changes after each test.
- `scope="function"` – Fresh session for every test function.

---

## 7. Dependency Override for Testing

FastAPI allows you to override dependencies in tests.

```python
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db  # or your own dependency

@pytest.fixture(scope="function")
def client(test_session):
    # Override the database dependency
    def override_get_db():
        try:
            yield test_session
        finally:
            pass  # Session managed by fixture

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()  # Clean up after tests
```

### How It Works

- FastAPI’s dependency system is temporarily replaced for tests.
- Tests use the **test session** instead of the real database session.
- Overrides are cleared after tests to avoid cross-test pollution.

---

## 8. Unit Testing Services

Example of a unit/integration-style test for a service method:

```python
def test_create_product(test_session):
    # Arrange
    service = ProductService(test_session)
    product_data = ProductCreate(
        name="Test Product",
        description="Test Description", 
        price=19.99,
        quantity=100,
        category="Electronics",
    )

    # Act
    product = service.create_product(product_data)

    # Assert
    assert product.id is not None
    assert product.name == "Test Product"
    assert product.price == 19.99
    assert product.quantity == 100
```

This follows the **Arrange–Act–Assert** pattern:

- **Arrange** – Set up test data and dependencies.
- **Act** – Execute the code under test.
- **Assert** – Verify the outcome.

---

## 9. Mock Testing Services

Testing services with mocked repositories (pure unit tests):

```python
from unittest.mock import Mock

def test_get_product_with_mock():
    # Arrange
    mock_repo = Mock(spec=ProductRepository)
    mock_repo.get_by_id.return_value = Product(id=1, name="Test Product")
    service = ProductService(mock_repo)  # Inject mock

    # Act
    result = service.get_product(1)

    # Assert
    assert result.name == "Test Product"
    mock_repo.get_by_id.assert_called_once_with(1)
```

### When to Use Mocks

- To test **business logic** without hitting the database.
- To simulate **error conditions** and rare edge cases.
- To keep tests **fast and focused**.

---

## 10. Integration Testing API Endpoints

Testing the full stack: API → Service → Repository → Database.

```python
def test_create_product_api(client):
    # Arrange
    product_data = {
        "name": "API Test Product",
        "description": "API Test Description",
        "price": 29.99,
        "quantity": 50,
        "category": "Books",
    }

    # Act
    response = client.post("/products/", json=product_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
    assert "id" in data  # Verify database-generated ID
```

This verifies:

- HTTP routing.
- JSON serialization/deserialization.
- Pydantic validation.
- Service and repository behavior.
- Database persistence.

### Testing Error Conditions

```python
def test_get_nonexistent_product(client):
    response = client.get("/products/999")  # Non-existent ID
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_create_product_invalid_data(client):
    invalid_data = {"name": "Test"}  # Missing required fields

    response = client.post("/products/", json=invalid_data)

    assert response.status_code == 422  # Pydantic validation error
```

---

## 11. Test Organization Best Practices

### File Structure

```text
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests
│   ├── test_services.py
│   ├── test_repositories.py
│   └── test_models.py
├── integration/          # Integration tests  
│   ├── test_api.py
│   └── test_database.py
└── e2e/                  # End-to-end tests
    └── test_workflows.py
```

### Naming Conventions

- Test files: `test_*.py` or `*_test.py`.
- Test functions: `test_*`.
- Test classes: `Test*`.

Clear structure makes it easier to navigate and maintain tests.

---

## 12. Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_services.py

# Run tests with verbose output
pytest -v

# Run tests and show coverage
pytest --cov=src

# Run only integration tests
pytest tests/integration/

# Run tests matching name pattern
pytest -k "test_create"
```

### Useful pytest Options

- `-x` – Stop on first failure.
- `--lf` – Run only last failed tests.
- `-s` – Show `print` output (for debugging).
- `--cov-report=html` – Generate HTML coverage report.

---

## 13. Test Coverage

### What Is Test Coverage?

A measurement of how much of your code is executed by tests.

### Generating Coverage Reports

```bash
# Install coverage plugin (via uv dev dependencies)
uv add --group dev pytest-cov

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html
```

### Interpreting Coverage

- Aim for **80–90% coverage** on critical code.
- Focus on **business logic**, not trivial boilerplate.
- Remember: high coverage ≠ good tests, but low coverage = risk.

---

## 14. Common Questions

**Q: Why use a separate test database?**  
**A:** To keep test data isolated, avoid polluting your main database, and safely reset state between tests.

---

**Q: When should I use unit tests vs integration tests?**  
**A:**

- Use **unit tests** for business logic and pure functions.
- Use **integration tests** for database access, API endpoints, and cross-component flows.

Start by covering core business logic with unit tests.

---

**Q: What's the difference between `yield` and `return` in fixtures?**  
**A:** `yield` allows you to write **teardown code** after the test finishes. With `return`, there is no after-test cleanup.

---

**Q: Why rollback instead of deleting data manually?**  
**A:** `rollback()` is faster, safer, and guarantees complete cleanup, even when tests fail halfway.

---

**Q: How do I test async code?**  
**A:** Use `pytest-asyncio` and declare tests with `async def`, then `await` async functions.

---

## 15. Further Reading

### Essential References

- pytest Documentation – <https://docs.pytest.org/>
- “Python Testing with pytest” (Book) – <https://pytest.org/book>
- Test-Driven Development – <https://en.wikipedia.org/wiki/Test-driven_development>
- Mock Object – <https://en.wikipedia.org/wiki/Mock_object>

### Deep Dive Topics

- Property-based Testing (Hypothesis) – <https://hypothesis.readthedocs.io/>
- Factory Boy for Test Data – <https://factoryboy.readthedocs.io/>
- SQLAlchemy Testing Patterns – <https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction>
- API Testing Strategies – <https://www.ministryoftesting.com/learning-path/api-testing>

---

## 16. Practice Exercises (Day 7)

1. Write unit tests for all **service methods**.
2. Add integration tests for key database and API flows, including **error conditions**.
3. Implement test data factories for complex entities (e.g., orders with multiple items).
4. Add property-based tests for validation/business rules where appropriate.
5. Set up **continuous integration** (e.g., GitHub Actions) to run tests on every push/PR.

---

## 17. Key Takeaways

- Follow the **Testing Pyramid**: many unit tests, some integration tests, few E2E tests.
- Use **mocks** and **fakes** to keep unit tests fast and focused.
- `conftest.py` is your hub for shared pytest fixtures.
- FastAPI **dependency overrides** make it easy to test APIs without real infrastructure.
- The **Arrange–Act–Assert** pattern keeps tests clear and maintainable.
- Coverage is a useful metric, but **test quality and relevance** matter more.

---

## 18. Coming Up Next (Day 8)

Tomorrow we’ll **containerize** the application for production deployment with Docker, including best practices for image structure, environment configuration, and running migrations.
