
# Day 2 – Project Scaffolding & Dependency Management

> Goal: Move from “a folder of scripts” to a **structured, installable Python application** with modern dependency management using `pyproject.toml` and `uv`.

---

## 1. Modern Python Packaging: From `setup.py` to `pyproject.toml`

### What is `pyproject.toml`?

`pyproject.toml` is a single, standardized configuration file that replaces multiple older files:

- `setup.py`
- `requirements.txt`
- `setup.cfg`
- `MANIFEST.in`

with **one** declarative configuration that modern tools understand.

### Traditional vs Modern Approach

```python
# OLD: setup.py (imperative, can execute arbitrary code)
from setuptools import setup

setup(
    name="my-project",
    version="0.1.0",
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0"
    ]
)
```

```toml
# NEW: pyproject.toml (declarative, standardized)
[project]
name = "my-project"
version = "0.1.0"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]
```

### Why `pyproject.toml`?

- **Standardized** – Follows PEP 621, supported by all modern Python tooling.
- **Declarative** – No arbitrary code execution during installation.
- **Tool-agnostic** – Works with `pip`, `uv`, Poetry, Hatch, and others.
- **Comprehensive** – Handles dependencies, metadata, and tool configuration in one place.

---

## 2. Dependency Management Philosophy

### What are dependencies?

Dependencies are external packages your project needs to function (e.g., `requests`, `pandas`, `fastapi`).

### Scripting vs Professional Development

```text
# Scripting approach
# requirements.txt
requests
pandas
numpy
# Installed with: pip install -r requirements.txt
```

```toml
# Professional approach
# pyproject.toml
[project]
dependencies = [
    "requests>=2.25.1",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]
# Installed with: uv sync
```

### Key Benefits of the Professional Approach

- **Version pinning** – Specify minimum versions to ensure compatibility.
- **Reproducible builds** – Same versions installed every time (via lock files like `uv.lock`).
- **Security** – Easier to apply security updates while controlling version ranges.
- **Dependency groups** – Separate dev, test, and production dependencies for lean deployments.

---

## 3. Dependency Groups Explained

**Concept:** Different sets of dependencies for different purposes (dev, test, docs, etc.).

```toml
[project.optional-dependencies]
dev = [    # Development tools (not needed in production)
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pytest>=7.0.0"
]
test = [   # Testing dependencies
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0"
]
docs = [   # Documentation tools
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.0.0"
]
```

### Installation with `uv`

```bash
# Production only
uv sync

# Production + development tools
uv sync --group dev

# Production + testing
uv sync --group test

# Everything (all groups)
uv sync --all-groups
```

This lets you keep **production images lean** while still having rich tooling in development.

---

## 4. Code Formatting and Quality Tools

### What are linters and formatters?

- **Formatters (Black)** – Automatically format code to a consistent style.
- **Linters (Flake8)** – Analyze code for potential errors and style issues.
- **Type checkers (MyPy)** – Check type annotations for correctness and consistency.

### Example configuration in `pyproject.toml`

```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
```

Putting these configurations in `pyproject.toml`:

- Centralizes tool configuration.
- Keeps your repo clean (fewer dot-files like `.flake8`, `mypy.ini`).
- Makes it easier for teammates and CI to use the same settings.

---

## 5. Project Structure: `src` Layout vs Flat Layout

### Flat layout (common in scripts)

```bash
my_project/
├── my_code.py
├── utils.py
└── setup.py
```

### `src` layout (professional)

```bash
my_project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── main.py
│       └── utils.py
├── tests/
└── pyproject.toml
```

### Benefits of `src` layout

- **Prevents accidental imports** – You don’t accidentally import from the project root; you import from the installed package.
- **Clean separation** – Source code is clearly separated from tests and config.
- **Accurate testing** – Tests run against the **installed package**, not local files.
- **Packaging ready** – Easy to build and distribute to PyPI or internal indexes.

---

## 6. Understanding Our `pyproject.toml` (Inventory System Example)

Let’s break down a realistic example:

```toml
[project]
name = "inventory-system"
version = "0.1.0"
description = "Professional Inventory Management System"
dependencies = [
    "pydantic>=2.0.0",    # Data validation
    "sqlalchemy>=2.0.0",  # Database ORM
    "fastapi>=0.100.0",   # Web framework
    "uvicorn>=0.23.0",    # ASGI server
]
requires-python = ">=3.11"  # Minimum Python version

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=23.0.0"]          # Development tools
test = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]     # Testing tools

[build-system]
requires = ["hatchling"]                   # Build backend dependency
build-backend = "hatchling.build"          # How to build the package
```

**Key ideas:**

- `[project]` – Core metadata and runtime dependencies.
- `optional-dependencies` – Extra groups you can install on demand.
- `[build-system]` – Defines how your package is built (here: with Hatchling).

---

## 7. Environment Configuration with Pydantic

### What is Pydantic?

[Pydantic](https://docs.pydantic.dev/) is a data validation library that uses type hints to parse and validate data. With `pydantic-settings`, it becomes a powerful **configuration management** tool.

### Traditional vs Pydantic approach

```python
# Traditional configuration (error-prone)
import os

db_host = os.getenv("DB_HOST", "localhost")
db_port = int(os.getenv("DB_PORT", "1433"))  # Might crash if not int!
```

```python
# Professional approach with Pydantic
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 1433  # Automatically validated and converted

    class Config:
        env_prefix = "APP_"  # Optional prefix, e.g. APP_DB_HOST

settings = Settings()  # Automatically loads from environment variables
```

### Benefits

- **Type safety** – Automatic type conversion and validation.
- **Environment support** – Loads from environment variables and/or `.env` files.
- **Default values** – Sensible defaults with easy overrides.
- **Validation** – Catches configuration errors early (at startup).

---

## 8. Dependency Installation with `uv`

### How `uv` manages dependencies

```bash
# Initialize project (creates pyproject.toml and virtual environment)
uv init --package inventory-system

# Add dependencies
uv add fastapi sqlalchemy pydantic

# Install all dependencies (including optional groups)
uv sync --all-groups

# Update dependencies to newer compatible versions
uv update

# Remove a dependency
uv remove package-name
```

### What happens when you run `uv sync`?

1. Reads `pyproject.toml`.
2. Resolves the dependency tree (finds compatible versions).
3. Creates or updates the virtual environment.
4. Installs all required packages.
5. Writes/updates `uv.lock` for reproducible installs.

Result: **Fast, reliable, and reproducible** dependency management.

---

## 9. Common Questions

**Q: Why not use `requirements.txt` anymore?**  
**A:** `pyproject.toml` is the modern standard that handles more than just dependencies – it also includes metadata, build system, and tool configs, all in one place.

---

**Q: What's the difference between `dependencies` and `optional-dependencies`?**  
**A:**

- `dependencies` – Always installed (runtime requirements).
- `optional-dependencies` – Installed only on demand (e.g., `dev`, `test`, `docs`) so production deployments stay lean.

---

**Q: Why use Pydantic for settings instead of just `os.getenv()`?**  
**A:** Pydantic provides:

- Validation & type conversion.
- Clear, typed configuration objects.
- Easy integration with `.env` files and different environments.

This reduces boilerplate and prevents subtle configuration bugs.

---

**Q: What is a build system and why do we need it?**  
**A:** The build system converts your source code into a distributable package (wheel or sdist). Tools like **Hatchling** handle:

- Building packages from your `src/` layout.
- Respecting metadata and config from `pyproject.toml`.
- Integrating with `pip`, `uv`, and other tools.

---

## 10. Further Reading

### Essential References

- Pyproject.toml Guide – <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>
- PEP 621 – <https://peps.python.org/pep-0621/>
- UV Documentation – <https://docs.astral.sh/uv/>
- Pydantic Settings – <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>

### Deep Dive Topics

- Python Packaging User Guide – <https://packaging.python.org/en/latest/>
- Dependency Resolution – <https://pip.pypa.io/en/stable/topics/dependency-resolution/>
- Semantic Versioning – <https://semver.org/> (how to version your packages)

---

## 11. Practice Exercises (Day 2)

1. **Create a new project** with `uv init --package` and experiment with adding dependencies.
2. **Create a settings class** with Pydantic that reads from environment variables (e.g., database config).
3. **Experiment with version specifiers**: `>=`, `==`, `~=`, and observe how `uv` resolves versions.
4. **Set up Black** via `pyproject.toml` and run it on a sample Python file.
5. (Optional) Add a simple test using `pytest` and run it inside the `uv`-managed environment.

---

## 12. Key Takeaways

- `pyproject.toml` replaces multiple configuration files with **one modern standard**.
- Dependency management is about **reproducibility, security, and clarity**.
- The `src/` layout helps avoid import issues and prepares your project for packaging.
- Pydantic makes configuration **safe, typed, and easy to manage**.
- `uv` provides fast, reliable dependency resolution and environment management.

---

## 13. Coming Up Next (Day 3)

Tomorrow we’ll dive into **database setup** and learn about **SQLAlchemy ORM patterns**, building the foundation for a real-world, database-backed application.
