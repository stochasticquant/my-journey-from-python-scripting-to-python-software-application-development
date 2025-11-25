
# Day 3 – Database Setup with SQL Server & SQLAlchemy

> Goal: Learn how to connect a real database (SQL Server) to your Python application using **SQLAlchemy ORM**, and run everything in a reproducible Dockerized environment.

---

## 1. Object-Relational Mapping (ORM) Explained

### What is an ORM?

An **ORM (Object-Relational Mapper)** is a technique that lets you interact with your database using Python objects instead of writing raw SQL queries.

### Traditional vs ORM Approach

```python
# Traditional approach (raw SQL - what you might know)
import pyodbc

connection = pyodbc.connect(connection_string)
cursor = connection.cursor()
cursor.execute(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    "Widget",
    19.99,
)
connection.commit()
```

```python
# ORM approach (professional)
product = Product(name="Widget", price=19.99)
db_session.add(product)
db_session.commit()
```

### Why use an ORM?

- **Productivity** – Write Python code instead of manual SQL for most operations.
- **Type Safety** – Python type checking for database operations.
- **Database Agnostic** – Same code works with different databases (SQL Server, PostgreSQL, etc.).
- **Security** – Built-in protection against SQL injection when using parameters properly.
- **Maintainability** – Changes to the database schema often require fewer code changes.

---

## 2. SQLAlchemy: The Python SQL Toolkit

### What is SQLAlchemy?

[SQLAlchemy](https://www.sqlalchemy.org/) is the most popular ORM for Python. It has two main components:

- **Core** – SQL expression language (lower-level, closer to raw SQL).
- **ORM** – Object-relational mapper (higher-level, works with Python classes).

### SQLAlchemy Architecture

```text
Your Python Code
    ↓
SQLAlchemy ORM (Object Relational Mapper)
    ↓
SQLAlchemy Core (SQL Expression Language)
    ↓
Database-specific driver (pyodbc, psycopg2, etc.)
    ↓
Database (SQL Server, PostgreSQL, MySQL, etc.)
```

You get the flexibility of SQL when you need it, plus the convenience of Python objects.

---

## 3. Declarative Base & Data Models

### What is a Declarative Base?

The declarative base is a factory function that creates a **base class** for all your data models. All your ORM models inherit from this base class.

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass

# All your models inherit from this base
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

### Why use a declarative base?

- **Registration** – Automatically registers models with SQLAlchemy.
- **Metadata** – Tracks all tables and their relationships via `Base.metadata`.
- **Inheritance** – Shared configuration for all models.
- **Table Creation** – Create all tables with:
  ```python
  Base.metadata.create_all(bind=engine)
  ```

---

## 4. SQLAlchemy Column Types and Constraints

### Mapping Python types to SQL types

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)                 # -> INT IDENTITY
    name = Column(String(100), nullable=False)             # -> VARCHAR(100) NOT NULL
    price = Column(Float, nullable=False)                  # -> FLOAT NOT NULL
    quantity = Column(Integer, default=0)                  # -> INT DEFAULT 0
    description = Column(Text)                             # -> TEXT
    created_at = Column(
        DateTime,
        server_default=func.now(),
    )  # -> DATETIME DEFAULT GETDATE()
```

### Common Constraints

- `primary_key=True` – Marks column as primary key.
- `nullable=False` – Column cannot be `NULL`.
- `unique=True` – All values must be unique.
- `index=True` – Creates database index for faster queries.
- `default=value` – Python-side default value if not provided.
- `server_default=...` – Default enforced by the **database**.

---

## 5. Database Sessions and Connection Pools

### What is a Session?

A **Session** represents a “workspace” for your database operations. It:

- Tracks objects you load or create.
- Manages transactions (commit/rollback).
- Buffers changes before sending them to the database.

#### Session Lifecycle Example

```python
# 1. Create session
session = SessionLocal()

try:
    # 2. Perform operations
    product = Product(name="Laptop", price=999.99)
    session.add(product)

    # 3. Query database
    laptops = (
        session.query(Product)
        .filter(Product.name.like("%Laptop%"))
        .all()
    )

    # 4. Commit transaction
    session.commit()
except Exception:
    # 5. Rollback on error
    session.rollback()
    raise
finally:
    # 6. Always close session
    session.close()
```

### Connection Pools

SQLAlchemy automatically manages a **pool of database connections** to improve performance. Instead of opening/closing a connection each time, it reuses existing ones.

- Faster database operations.
- Fewer connection overheads.
- Better scalability.

---

## 6. Database Configuration Class

Let’s break down a typical `DatabaseManager` class that configures SQLAlchemy with SQL Server:

```python
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings  # Your Pydantic settings


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def setup(self):
        """Initialize database connection"""
        # URL encode password for special characters
        encoded_password = urllib.parse.quote_plus(settings.db_password)

        connection_string = (
            f"mssql+pyodbc://{settings.db_user}:{encoded_password}@"
            f"{settings.db_host}:{settings.db_port}/{settings.db_name}?"
            f"driver={settings.db_driver}&TrustServerCertificate=yes"
        )

        # Create engine with connection pooling
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # Check connection health before use
            echo=True,           # Log SQL statements (disable in production)
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,    # We control commits manually
            autoflush=False,     # We control flushes manually
            bind=self.engine,    # Bind to our database engine
        )
```

### Key Components

- **Engine** – Manages the connection pool and low-level DB communication.
- **SessionLocal** – Factory for creating new sessions (`SessionLocal()`).
- `pool_pre_ping=True` – Tests connections before use (prevents stale connections).
- `autocommit=False` – You explicitly call `commit()` when ready.
- `echo=True` – Logs SQL statements (great for learning & debugging).

---

## 7. SQL Server Connection String Breakdown

```python
# Connection string format:
# mssql+pyodbc://username:password@host:port/database?driver=DriverName&options

connection_string = (
    "mssql+pyodbc://sa:MyPassword@localhost:1433/inventory"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
```

### Components

- `mssql+pyodbc` – SQLAlchemy dialect + DBAPI driver.
- `sa:MyPassword` – Username and password.
- `localhost:1433` – Database server and port.
- `inventory` – Database name.
- `driver=ODBC+Driver+18+for+SQL+Server` – ODBC driver to use.
- `TrustServerCertificate=yes` – Bypass certificate validation (**development only**).

In production, you should use proper TLS certificates instead of `TrustServerCertificate=yes`.

---

## 8. Docker Compose for Database

### Why use Docker Compose for development?

Docker Compose lets you define and run multi-container applications. For development, it’s perfect for running **SQL Server** locally in a reproducible way.

```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      SA_PASSWORD: "YourStrong!Passw0rd"
      ACCEPT_EULA: "Y"
    ports:
      - "1433:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql
    healthcheck:
      test: ["CMD-SHELL", "/opt/mssql-tools/bin/sqlcmd -Q 'SELECT 1'"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  sqlserver_data:
```

### Benefits

- **Consistency** – Same database version and configuration for all developers.
- **Isolation** – No need to install SQL Server directly on your machine.
- **Reproducible** – Easy to reset or recreate the database.
- **Production-like** – Mirrors how services run in containers in real environments.

---

## 9. Model Definition with SQLAlchemy (Product Example)

Let’s examine a `Product` model in detail:

```python
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func

class Product(Base):
    __tablename__ = "products"  # Actual table name in database

    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True: This is the primary key
    # index=True: Creates an index for faster lookups by ID

    name = Column(String(100), nullable=False, index=True)
    # String(100): VARCHAR(100) in database
    # nullable=False: NOT NULL constraint
    # index=True: Index for faster searches by name

    description = Column(Text)
    # TEXT type for long descriptions

    price = Column(Float, nullable=False)
    # FLOAT type, required

    quantity = Column(Integer, nullable=False, default=0)
    # default=0: Default value if not specified

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    # server_default=func.now(): Database sets timestamp on insert

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
    # onupdate=func.now(): Database updates timestamp on row update
```

This model defines your table structure and constraints directly in Python code.

---

## 10. Common Questions

**Q: Why not use raw SQL? Isn't it faster?**  
**A:** For highly optimized, complex queries, raw SQL can be faster and more expressive. However, ORMs provide:

- Faster development.
- Type safety.
- Security (SQL injection protection via parameterized queries).
- Database abstraction.

For most CRUD operations in applications, the performance difference is negligible.

---

**Q: What's the difference between `session.add()` and `session.commit()`?**  
**A:**

- `session.add(obj)` – Stages the object for insertion/update.
- `session.commit()` – Flushes changes to the database and commits the transaction.

You can add multiple objects, then commit once.

---

**Q: Why do we need to close sessions?**  
**A:** Sessions hold database connections. If you don’t close them:

- Connections stay in use.
- The connection pool can run out of connections.
- Your app might start failing due to exhausted resources.

Always use `try/finally` or context managers to close sessions.

---

**Q: What is connection pooling?**  
**A:** Connection pooling reuses existing DB connections instead of creating new ones for every operation. This is **much more efficient** and is handled by SQLAlchemy automatically through the `engine`.

---

**Q: Why use `server_default` instead of `default` for timestamps?**  
**A:**

- `default` – Python-side default (set before sending to DB).
- `server_default` – Database-side default (set by DB when inserting).

For timestamps, `server_default` is often better because it uses the **database server's time** (more consistent across services).

---

## 11. Further Reading

### Essential References

- SQLAlchemy Official Documentation – <https://docs.sqlalchemy.org/>
- SQLAlchemy ORM Tutorial – <https://docs.sqlalchemy.org/en/20/orm/tutorial.html>
- Connection Strings Reference – <https://www.connectionstrings.com/>
- Docker Compose Reference – <https://docs.docker.com/compose/>

### Deep Dive Topics

- SQLAlchemy Relationship Patterns – <https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html>
- Database Migration with Alembic – <https://alembic.sqlalchemy.org/>
- SQL Server Python Driver – <https://learn.microsoft.com/sql/connect/python/>

---

## 12. Practice Exercises (Day 3)

1. **Create additional models**: `Customer`, `Order`, `OrderItem` with appropriate relationships.
2. **Experiment with different column types and constraints** (e.g., `Boolean`, `Enum`, `Numeric`).
3. **Write queries** using both SQLAlchemy ORM and SQLAlchemy Core.
4. **Test connection pooling** by creating multiple sessions and running queries.
5. (Optional) Configure timestamps and soft-delete fields (`is_active`, `deleted_at`).

---

## 13. Key Takeaways

- ORMs let you work with databases using **Python objects** instead of raw SQL.
- SQLAlchemy is the most comprehensive and flexible Python ORM.
- Sessions manage **transactions**, object tracking, and interactions with the database.
- Connection pooling significantly improves database performance.
- Docker Compose provides **consistent, reproducible** database environments for development.
- Proper model design (columns, constraints, indexes) is crucial for performance and maintainability.

---

## 14. Coming Up Next (Day 4)

Tomorrow we’ll implement the **Repository Pattern** to abstract database operations and make our code more testable, modular, and clean.
