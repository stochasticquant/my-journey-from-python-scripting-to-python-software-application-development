
# Day 1 – Professional Development Environment Setup

> Goal: Move from “just running scripts” to working like a professional Python application developer by setting up a clean, reproducible, and production‑like environment.

---

## 1. Development Environment Philosophy

A professional development environment is more than just having Python installed. It's about creating a **reproducible, isolated, and efficient** workspace that mirrors production as closely as possible.

**Why it matters:**

- **Isolation** – Prevents conflicts between different projects.
- **Reproducibility** – Team members can set up identical environments.
- **Consistency** – Development matches the production environment.
- **Efficiency** – Tools and workflows that speed up development.

---

## 2. Python Environment Management with Pyenv

### What is Pyenv?

[Pyenv](https://github.com/pyenv/pyenv) is a Python version management tool that allows you to:

- Install multiple Python versions side by side.
- Switch between versions per project.
- Set global and local Python versions.

### How it works

```bash
# Traditional Python installation (what you might be used to)
sudo apt install python3.11  # System-wide installation

# With pyenv (professional approach)
pyenv install 3.11.5         # User-space installation
pyenv global 3.11.5          # Sets default version
pyenv local 3.11.5           # Sets version for current project only
```

### Key Benefits

- No `sudo` required for package installation.
- Different projects can use different Python versions.
- Clean separation from the system Python (reduces “I broke my OS Python” issues).

---

## 3. Modern Package Management with UV

### What is UV?

[UV](https://docs.astral.sh/uv/) is a **fast** Python package manager and resolver written in Rust. Think of it as a supercharged `pip` that also manages virtual environments and `pyproject.toml` for you.

### Traditional vs UV approach

```bash
# Traditional pip (what you know)
pip install -r requirements.txt
pip freeze > requirements.txt

# Modern UV approach
uv add fastapi sqlalchemy pydantic  # Adds to pyproject.toml
uv sync                             # Installs all dependencies
```

### Why UV?

- **Speed** – Often 10–100x faster than `pip`.
- **Modern** – Uses `pyproject.toml` standard (replaces `setup.py` + `requirements.txt` in most cases).
- **Reliable** – Better dependency resolution.
- **All‑in‑one** – Handles virtual environments, package installation, and more.

---

## 4. Containerization with Docker

### What is Docker?

[Docker](https://www.docker.com/) allows you to package applications with all their dependencies into **containers**.

**Analogy:** Think of Docker containers like shipping containers:

- **Standardized** – Run the same way everywhere.
- **Isolated** – Don't interfere with each other.
- **Portable** – Run on any system with Docker installed.

### Traditional vs Docker approach

```bash
# Traditional deployment
# "It works on my machine" problem
python app.py  # Might work on your machine but not on the server

# Docker approach
docker build -t myapp .          # Build container
docker run -p 8000:8000 myapp    # Run anywhere the same way
```

Docker is not only for deployment; it is also useful for **local development** (e.g., running databases and services that mirror production).

---

## 5. Project Structure Philosophy

### Example structure

```bash
inventory-system/
├── src/                    # Source code (installable package)
│   └── inventory_system/   # Actual Python package
├── tests/                  # Test code (separate from source)
├── deployments/            # Deployment configurations (Docker, k8s, etc.)
└── pyproject.toml          # Modern project configuration
```

### Why organize code this way?

- **Clear separation** – Source code vs tests vs deployment.
- **Installable** – Your package can be installed with `pip install .`.
- **Professional** – Follows modern Python packaging standards.
- **Scalable** – Easy to grow from a small app to a larger system.

---

## 6. Implementation Details – Shell Configuration (`.zshrc`)

To make sure your tools are available in every terminal session, add the following to your `~/.zshrc`:

```bash
# Pyenv initialization
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# UV path (if installed via cargo)
export PATH="$HOME/.cargo/bin:$PATH"
```

After editing `.zshrc`, reload it:

```bash
source ~/.zshrc
```

---

## 7. Why This Setup Matters for Software Development

### From Scripting to Engineering

- **Scripts** – Single files, run directly (e.g., `python my_script.py`).
- **Software** – Structured packages, installed, tested, and deployed.

Today’s setup is about laying the foundation to think like an **engineer**, not just a script runner.

### Collaboration Ready

- Anyone can reproduce your environment.
- Consistent development experience across the team.
- Easier onboarding when new people join the project.

### Production Ready

- Same tools used in development and production.
- Containerized deployment reduces “works on my machine” issues.
- Clear project structure supports CI/CD and automated testing.

---

## 8. Common Questions

**Q: Why not just use system Python?**  
**A:** System Python is managed by your OS. Installing packages might require `sudo`, which can break system tools or conflict with OS packages. Pyenv keeps everything in your user space and under your control.

---

**Q: Why UV instead of pip?**  
**A:** UV is **faster** and **more modern**. It:

- Manages virtual environments automatically.
- Uses `pyproject.toml` instead of ad‑hoc `requirements.txt` files.
- Performs smarter dependency resolution.

---

**Q: Do I need Docker for development?**  
**A:** For professional development, it’s highly recommended. Docker ensures your app and its dependencies (databases, cache, etc.) match production, and it simplifies onboarding and deployment.

---

## 9. Further Reading

### Essential References

- Pyenv Documentation – <https://github.com/pyenv/pyenv>
- UV Documentation – <https://docs.astral.sh/uv/>
- Docker Getting Started – <https://docs.docker.com/get-started/>
- Python Packaging User Guide – <https://packaging.python.org/>

### Deep Dive Topics

- Virtual Environments – <https://docs.python.org/3/tutorial/venv.html>
- Python Application Dependency Management – <https://hynek.me/articles/python-app-deps/>
- Containerization Benefits – <https://www.docker.com/resources/what-container/>

---

## 10. Practice Exercises (Day 1)

1. **Create a new project directory** and set up the same structure as shown above.
2. **Install Pyenv** and experiment with switching between at least two Python versions.
3. **Use UV** to create a new project and add dependencies (e.g., `fastapi`, `pydantic`).
4. **Write a simple Python application** (e.g., “hello world” web app) and run it in a Docker container.

---

## 11. Key Takeaways

- Professional development starts with **proper environment setup**.
- Tools like **Pyenv** and **UV** solve real problems you will encounter in teams.
- **Containerization (Docker)** is not just for deployment; it improves development workflows too.
- A **good project structure** makes your code maintainable, testable, and shareable.

---

## 12. Coming Up Next (Day 2)

Tomorrow we’ll build on this foundation by creating a proper **Python package structure** and **dependency management system**, moving from “a folder with scripts” to a clean, installable Python application.
