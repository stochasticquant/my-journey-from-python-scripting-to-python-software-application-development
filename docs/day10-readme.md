
# Day 10 – Advanced Features & Monitoring

> Goal: Add **advanced error handling, resilience, monitoring, and observability** to your application so it behaves like a true production system, not just a working demo.

---

## 1. Advanced Error Handling and Resilience

### What is Resilience in Software?

**Resilience** is the ability of a system to handle failures and **continue operating** (or at least fail gracefully).

### Traditional vs Professional Error Handling

```python
# Traditional approach (basic)
def update_product_quantity(product_id, new_quantity):
    product = repository.get_by_id(product_id)
    if product:
        product.quantity = new_quantity
        repository.update(product)
    # Silent failure if product not found
```

```python
# Professional approach (comprehensive)
from typing import Optional, Tuple

def update_product_quantity(product_id, new_quantity) -> Tuple[Optional[Product], Optional[str]]:
    try:
        if new_quantity < 0:
            return None, "Quantity cannot be negative"

        product = repository.get_by_id(product_id)
        if not product:
            return None, f"Product {product_id} not found"

        product.quantity = new_quantity
        updated_product = repository.update(product)
        logger.info(f"Updated product {product_id} quantity to {new_quantity}")
        return updated_product, None

    except DatabaseError as e:
        logger.error(f"Database error updating product {product_id}: {str(e)}")
        return None, "Database error occurred"
    except Exception as e:
        logger.error(f"Unexpected error updating product {product_id}: {str(e)}")
        return None, "Unexpected error occurred"
```

Key ideas:

- **Validate inputs** (`new_quantity >= 0`).
- **Handle missing data** (`product not found`).
- **Log** meaningful context (`product_id`, new value).
- **Differentiate** database errors vs unexpected errors.
- **Return clear results** instead of silently failing.

---

## 2. Decorators for Cross-Cutting Concerns

### What are Decorators?

Decorators are functions that **wrap** other functions to modify their behavior **without changing their source code**. They are ideal for **cross-cutting concerns** like logging, metrics, auth, transaction handling, etc.

### Basic Decorator Example

```python
import time
from functools import wraps

def log_execution_time(func):
    @wraps(func)  # Preserves function metadata
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            print(f"{func.__name__} executed in {execution_time:.4f} seconds")
    return wrapper

# Usage
@log_execution_time
def expensive_operation():
    time.sleep(1)

expensive_operation()  # Prints: "expensive_operation executed in 1.0023 seconds"
```

### How Decorators Work

- Python sees `@log_execution_time` above `expensive_operation`.
- It calls `log_execution_time(expensive_operation)`.
- That returns a new function (`wrapper`) that **replaces** `expensive_operation`.
- When you call `expensive_operation()`, you’re actually calling `wrapper()`.

This lets you **add behavior around** a function (before/after/around) without polluting the core business logic.

---

## 3. Application Monitoring and Observability

### What is Observability?

**Observability** is the ability to understand what's happening inside a system **from the outside**, using logs, metrics, and traces.

**Three Pillars of Observability:**

- **Logs** – Discrete events with timestamps (e.g., “Order 123 created”).  
- **Metrics** – Numerical measurements over time (e.g., request latency, error rates).  
- **Traces** – End-to-end request flows across services.

### Monitoring vs Observability

- **Monitoring** – You know **what** to look for (dashboards with known metrics).
- **Observability** – You can explore and explain **unknown issues** using rich telemetry.

In production, you want **both**.

---

## 4. Prometheus Metrics in Python

### What is Prometheus?

**Prometheus** is an open-source **monitoring and alerting** toolkit commonly used with Kubernetes.

### Metric Types

- **Counter** – Only ever goes **up** (e.g., total requests, total errors).
- **Gauge** – Can go **up and down** (e.g., memory usage, active sessions).
- **Histogram** – Collects a distribution of values (e.g., request durations).
- **Summary** – Similar to Histogram but with quantiles computed client-side.

You will typically use **Counters + Histograms** for HTTP services.

---

## 5. Context Managers and Resource Management

### What are Context Managers?

Context managers ensure resources are **properly acquired and released** using the `with` statement.

### Traditional vs Context Manager

```python
# Traditional resource management
file = open("data.txt", "r")
try:
    data = file.read()
    # What if an exception occurs here?
finally:
    file.close()  # You must remember to close it
```

```python
# With context manager
with open("data.txt", "r") as file:
    data = file.read()
# File automatically closed, even if an exception occurs
```

The same pattern is used for:

- Database sessions.
- Network connections.
- Locks and transactions.

---

## 6. Advanced Service with Comprehensive Error Handling

### Advanced Service Implementation

```python
from typing import Optional, Tuple, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

class AdvancedProductService:
    def __init__(self, session: Session):
        self.repository = ProductRepository(session)
        self.session = session

    def create_product(self, product_data: ProductCreate) -> Tuple[Optional[Product], Optional[str]]:
        """Create product with comprehensive error handling"""
        try:
            # Business validation
            if product_data.price <= 0:
                return None, "Price must be greater than zero"

            if product_data.quantity < 0:
                return None, "Quantity cannot be negative"

            # Convert Pydantic to SQLAlchemy model
            product = Product(**product_data.model_dump())
            created_product = self.repository.create(product)

            # Log successful creation
            logger.info(f"Created product: {created_product.id}")
            return created_product, None

        except SQLAlchemyError as e:
            # Database-specific errors
            self.session.rollback()
            logger.error(f"Database error creating product: {str(e)}")
            return None, "Database error occurred"
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error creating product: {str(e)}")
            return None, "Unexpected error occurred"
```

### Key Error Handling Patterns

- **Specific exception types** (`SQLAlchemyError`) for DB issues.
- **Transaction handling** – `rollback()` on DB errors.
- **Logging with context** (what failed, which data, which user).
- **Clear return contracts**: `(result, error_message)`.

---

## 7. Bulk Operations with Transaction Safety

```python
from typing import List, Tuple

def bulk_update_quantities(self, updates: List[Tuple[int, int]]) -> Tuple[int, List[str]]:
    """Bulk update product quantities with transaction safety"""
    errors: List[str] = []
    success_count = 0

    try:
        for product_id, new_quantity in updates:
            # Validate each update
            if new_quantity < 0:
                errors.append(f"Invalid quantity for product {product_id}")
                continue

            product = self.repository.get_by_id(product_id)
            if not product:
                errors.append(f"Product {product_id} not found")
                continue

            # Apply update
            product.quantity = new_quantity
            success_count += 1

        # Commit all changes at once
        self.session.commit()
        logger.info(f"Bulk update completed: {success_count} successful, {len(errors)} errors")

    except SQLAlchemyError as e:
        # Rollback entire transaction on any error
        self.session.rollback()
        logger.error(f"Database error in bulk update: {str(e)}")
        errors.append("Transaction failed - all changes rolled back")

    return success_count, errors
```

### Transaction Safety Principles (ACID)

- **Atomicity** – All updates succeed or **all fail**.
- **Consistency** – Database stays in a valid state.
- **Isolation** – Other operations don’t see partial updates.
- **Durability** – Committed changes are permanent.

---

## 8. Monitoring Decorator Implementation

### Execution Time Monitoring Decorator

```python
import time
import logging
from functools import wraps
from typing import Callable, Any

def monitor_execution_time(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logging.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
    return wrapper

# Usage in service
class ProductService:
    @monitor_execution_time
    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.get_all(skip, limit)
```

### Decorator Benefits

- **Non-invasive** – No changes to core business logic.
- **Reusable** – Apply to any function or method.
- **Consistent** – Standardized logging/metrics for performance.

---

## 9. Prometheus Metrics Integration

### Metrics Definition

```python
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi import Request, Response
from fastapi.routing import APIRoute
from typing import Callable
import time

# Define metrics
REQUEST_COUNT = Counter(
    "inventory_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "inventory_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)
```

### Custom Route Handler for Monitoring

```python
class MonitoringRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            # Process request
            response = await original_route_handler(request)

            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
            ).inc()

            return response

        return custom_route_handler
```

### Metrics Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(REGISTRY), media_type="text/plain")
```

Prometheus scrapes `/metrics` regularly; you can then build **Grafana dashboards**.

---

## 10. Business Logic with Domain Intelligence

Your services can implement **real business logic**, not just CRUD.

```python
def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
    """Get products with low stock (business intelligence)"""
    all_products = self.repository.get_all()
    return [p for p in all_products if p.quantity <= threshold]
```

```python
def apply_price_increase(self, category: str, percentage: float) -> Tuple[int, List[str]]:
    """Apply percentage price increase to products in category"""
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
            except Exception as e:
                errors.append(f"Failed to update product {product.id}: {str(e)}")

        self.session.commit()
        logger.info(f"Price increase applied to {updated_count} products in {category}")
        return updated_count, errors

    except SQLAlchemyError as e:
        self.session.rollback()
        logger.error(f"Database error applying price increase: {str(e)}")
        return 0, ["Transaction failed - all changes rolled back"]
```

This moves you from **pure CRUD** to **domain logic**, which is where real business value lives.

---

## 11. Structured Logging Configuration

### Structured JSON Logging

```python
import logging
from pythonjsonlogger import jsonlogger

class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = record.created
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

def setup_logging():
    handler = logging.StreamHandler()
    formatter = StructuredJsonFormatter(
        "%(timestamp)s %(level)s %(logger)s %(message)s"
    )
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
    )

logger = logging.getLogger(__name__)
```

### Usage

```python
logger.info("Product created", extra={
    "product_id": product.id,
    "action": "create",
    "category": product.category,
})
```

Structured logs are **machine-friendly** (e.g., for ELK/Graylog/Loki) and help with searching, filtering, and dashboarding.

---

## 12. Common Questions

**Q: When should I use decorators vs direct function calls?**  
**A:** Use decorators for **cross-cutting concerns** (logging, timing, auth, retries) that apply to many functions. Use direct calls for **business logic**.

---

**Q: What's the difference between logging and metrics?**  
**A:**

- **Logs** – Detailed event information (what happened, when, with which data).
- **Metrics** – Aggregated numbers (how many, how long, error rate).  

You need **both** for robust observability.

---

**Q: Why return tuples `(result, error)` instead of raising exceptions?**  
**A:** For **expected business errors** (validation failures, not-found cases), returning tuples leads to fewer try/except blocks and clearer control flow. Use exceptions for **unexpected system errors**.

---

**Q: How do I choose between Histogram and Summary metrics?**  
**A:**

- Use **Histogram** in most cases, especially with Prometheus + Grafana.
- Use **Summary** if you specifically need client-side quantiles.

---

**Q: What's the purpose of `@wraps` in decorators?**  
**A:** `@wraps` preserves the original function’s **name**, **docstring**, and other metadata. This is crucial for debugging, introspection, and documentation tools.

---

## 13. Monitoring and Observability in Practice

### Logging Best Practices

Log levels:

- `DEBUG` – Very detailed info for debugging.
- `INFO` – High-level application flow (“order created”, “user logged in”).
- `WARNING` – Something unexpected, but app continues.
- `ERROR` – Serious problems where an operation failed.
- `CRITICAL` – Very serious errors; the app might be unusable.

```python
# Good: Structured logging
logger.info("Order processed", extra={
    "order_id": order.id,
    "customer_id": order.customer_id,
    "amount": order.amount,
    "duration_seconds": duration,
})

# Avoid: Unstructured logging
logger.info(f"Order {order.id} for customer {order.customer_id} processed in {duration}s")
```

### Metrics Collection Strategy

```python
from prometheus_client import Counter, Gauge, Histogram

# Application metrics
APPLICATION_STARTUP = Counter("app_startups_total", "Total application startups")
ACTIVE_USERS = Gauge("active_users", "Number of active users")
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration")

# Business metrics
ORDERS_PROCESSED = Counter("orders_processed_total", "Total orders processed")
REVENUE_GENERATED = Counter("revenue_generated", "Total revenue generated")
```

Track both **technical metrics** and **business KPIs**.

---

## 14. Health Check Endpoints

### Comprehensive Health Check

```python
from datetime import datetime
from fastapi import FastAPI

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {},
    }

    # Database health check
    try:
        db_session = db_manager.get_session()
        db_session.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # External service checks can be added here

    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status, status_code
```

Kubernetes (and Docker) can use this endpoint for **liveness/readiness probes** and health checks.

---

## 15. Performance Optimization

### Database Query Optimization

```python
from sqlalchemy.orm import selectinload, load_only

def get_products_with_optimized_queries(self, category: str) -> List[Product]:
    """Use SQLAlchemy optimizations for better performance"""
    return (
        self.session.query(Product)
        .options(
            # Eager loading to avoid N+1 queries
            selectinload(Product.category),
            # Only load needed columns
            load_only(Product.name, Product.price, Product.quantity),
        )
        .filter(Product.category == category)
        .all()
    )
```

### Caching Strategies

```python
from functools import lru_cache

class CachedProductService(ProductService):
    @lru_cache(maxsize=100)
    def get_product(self, product_id: int) -> Optional[Product]:
        return super().get_product(product_id)

    def create_product(self, product_data: ProductCreate) -> Product:
        product = super().create_product(product_data)
        # Invalidate cache
        self.get_product.cache_clear()
        return product
```

Caching can significantly reduce database load for read-heavy endpoints.

---

## 16. Further Reading

### Essential References

- Python Decorators – <https://realpython.com/primer-on-python-decorators/>
- Prometheus Python Client – <https://github.com/prometheus/client_python>
- Structured Logging – <https://www.structlog.org/>
- Python Logging HOWTO – <https://docs.python.org/3/howto/logging.html>

### Deep Dive Topics

- Distributed Tracing (OpenTelemetry) – <https://opentelemetry.io/>
- Application Performance Monitoring (APM) – <https://en.wikipedia.org/wiki/Application_performance_management>
- Circuit Breaker Pattern – <https://martinfowler.com/bliki/CircuitBreaker.html>
- Retry Pattern – <https://learn.microsoft.com/azure/architecture/patterns/retry>

---

## 17. Practice Exercises (Day 10)

1. Implement a **retry decorator** for transient failures (e.g., database connection timeouts).
2. Add **distributed tracing** (OpenTelemetry) to your FastAPI app.
3. Create custom **business metrics** (e.g., low-stock alerts, order volume per hour).
4. Implement a **circuit breaker** around calls to external services.
5. Set up **log aggregation** with ELK, Loki, or a similar stack and visualize logs.

---

## 18. Key Takeaways

- Comprehensive **error handling and resilience** are hallmarks of professional systems.
- **Decorators** are a powerful tool for adding cross-cutting behavior cleanly.
- **Monitoring and observability** (logs, metrics, traces) are essential, not optional.
- **Structured logging** makes logs far more useful in large systems.
- **Metrics** give you quantitative insight into behavior and performance.
- **Transaction safety** ensures consistent and reliable data.
- Adding **business intelligence** to services moves you beyond CRUD into true domain-driven design.

---

## 19. Congratulations 🎉

You’ve completed the **10-day journey** from Python scripting to **professional software development**:

- Proper **project structure** and **packaging**.
- Robust **database access** and **repositories**.
- A clean **service layer** and **FastAPI** API.
- Comprehensive **testing**, **Docker**, and **Kubernetes deployment**.
- Advanced **monitoring**, **observability**, and **resilience**.

From here, you can deepen each area (DDD, advanced Kubernetes, observability, security), but you now have a solid, end-to-end mental model of what a **production-grade Python application** looks like.
