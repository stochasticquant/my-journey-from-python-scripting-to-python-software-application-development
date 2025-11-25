
# Day 8 – Production Docker Setup

> Goal: Containerize the application with a **production-grade Docker setup**, using multi-stage builds, environment-based configuration, and Docker Compose for a real-world deployment workflow.

---

## 1. Containerization vs Virtualization

### What is Containerization?

Containerization is a lightweight form of virtualization that packages an application **and its dependencies** together in an isolated environment so it runs the same everywhere.

### Traditional vs Containerized Deployment

```bash
# Traditional deployment
# The classic "it works on my machine" problem
python app.py  # Works on developer machine

# On server:
# - Missing dependencies
# - Wrong Python version
# - Different OS
```

```bash
# Containerized deployment  
docker build -t myapp .   # Package everything
docker run myapp          # Runs exactly the same everywhere
```

### Containers vs Virtual Machines

**Virtual Machine:**

```text
+-------------------------------+
|          Application          |
+-------------------------------+
|        Guest OS (Full)        |
+-------------------------------+
|     Hypervisor (Virtual)      |
+-------------------------------+
|        Host OS (Real)         |
+-------------------------------+
|        Hardware (Real)        |
+-------------------------------+
```

**Container:**

```text
+-------------------------------+
|          Application          |
+-------------------------------+
|        Docker Engine          |
+-------------------------------+
|        Host OS (Real)         |
+-------------------------------+
|        Hardware (Real)        |
+-------------------------------+
```

### Key Differences

- **Virtual Machines**
  - Full OS isolation
  - Heavy (GBs)
  - Slow startup

- **Containers**
  - Process-level isolation
  - Lightweight (MBs)
  - Fast startup

For Python web apps, containers are usually the preferred choice in modern deployments.

---

## 2. Docker Architecture and Components

### Core Docker Concepts

- **Dockerfile** – Blueprint for building images.
- **Image** – Read-only template with the app + dependencies.
- **Container** – A running instance of an image.
- **Docker Compose** – Tool for defining and running multi-container applications.

### Example Dockerfile

```dockerfile
FROM python:3.11-slim          # Base image
WORKDIR /app                   # Working directory
COPY requirements.txt .        # Copy dependency list
RUN pip install -r requirements.txt  # Install dependencies
COPY . .                       # Copy application code
CMD ["python", "app.py"]       # Default command
```

### Building an Image

```bash
docker build -t myapp .  # Creates image from Dockerfile
```

### Running a Container

```bash
docker run -p 8000:8000 myapp  # Creates container from image
```

### Docker Compose Example

```yaml
services:
  web:
    build: .
    ports: ["8000:8000"]
  database:
    image: postgres:13
```

Docker Compose lets you define multi-service setups (app + database + cache, etc.) in a single file.

---

## 3. Multi-stage Docker Builds

### What Are Multi-stage Builds?

A technique to create **smaller, more secure** Docker images by using multiple stages in one Dockerfile (e.g., **builder** and **runtime** stages).

### Single-stage vs Multi-stage

```dockerfile
# SINGLE-STAGE: Large image (includes build tools)
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt  # Includes build tools and extra artifacts
CMD ["python", "app.py"]
```

```dockerfile
# MULTI-STAGE: Small image (only runtime dependencies)

# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt  # Build step

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app /app        # Only copy built application
CMD ["python", "app.py"]             # No build tools in final image
```

### Benefits of Multi-stage Builds

- **Smaller images** – No compilers, build tools, or intermediate files in final image.
- **Better security** – Fewer packages → smaller attack surface.
- **Faster deployment** – Smaller images push/pull faster.

---

## 4. Docker Layer Caching

### How Docker Builds Work

Docker builds images in **layers**, and each instruction in a Dockerfile creates a new layer:

```dockerfile
FROM python:3.11-slim                    # Layer 1: Base image
WORKDIR /app                             # Layer 2
COPY requirements.txt .                  # Layer 3
RUN pip install -r requirements.txt      # Layer 4
COPY . .                                 # Layer 5
CMD ["python", "app.py"]                 # Layer 6
```

### Optimizing Build Cache

- Put **rarely-changing steps first** (like dependency installation).
- Put **frequently-changing steps last** (like copying source code).

This allows Docker to **reuse cached layers** when only your code changes.

---

## 5. Environment Variables and Configuration

Following the **12-Factor App** principles, configuration should be stored in **environment variables**, not hard-coded.

### Docker Environment Variables

Set defaults in Dockerfile:

```dockerfile
ENV APP_PORT=8000
ENV DB_HOST=localhost
```

Override at runtime:

```bash
docker run -e APP_PORT=9000 -e DB_HOST=db.myapp.com myapp
```

### Docker Compose Environment Variables

```yaml
services:
  app:
    build: .
    environment:
      - DB_HOST=sqlserver
      - DB_PASSWORD=${DB_PASSWORD}  # From your shell or .env file
    env_file:
      - .env  # Load additional variables from file
```

This makes your image reusable across dev, test, and prod environments with different configs.

---

## 6. Multi-stage Production Dockerfile (Breakdown)

Let’s examine a production-grade Dockerfile using **UV** and SQL Server:

```dockerfile
# Stage 1: Builder stage (includes build tools)
FROM python:3.11-slim as builder

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency specification
COPY pyproject.toml ./

# Copy source code
COPY src/ ./src/

# Install dependencies (creates virtual environment)
RUN uv sync --frozen --no-dev


# Stage 2: Runtime stage (minimal, production-only)
FROM python:3.11-slim

# Install SQL Server ODBC driver (runtime dependency)
RUN apt-get update && apt-get install -y     curl     gnupg     && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -     && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list     && apt-get update     && ACCEPT_EULA=Y apt-get install -y msodbcsql18     && apt-get clean     && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy application from builder stage
COPY --from=builder /app /home/app

# Set environment variables
ENV PYTHONPATH=/home/app/src
ENV PATH="/home/app/.venv/bin:$PATH"

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "inventory_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key points:

- Builder stage installs dependencies via **uv**.
- Runtime stage is minimal and runs as a **non-root user**.
- SQL Server ODBC driver is installed only where needed.
- Healthcheck ensures container liveness.

---

## 7. Security Best Practices

### Non-root User

```dockerfile
# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app  # Switch to non-root user
```

**Why non-root?**

- Limits damage if the application is compromised.
- Follows **principle of least privilege**.
- Required or recommended by many production platforms.

### Layer Cleaning

```dockerfile
RUN apt-get update && apt-get install -y     package1     package2     && apt-get clean     && rm -rf /var/lib/apt/lists/*
```

- Use **chained commands** to minimize layers.
- Clean package caches to reduce image size.

---

## 8. Health Checks

### What Are Health Checks?

Health checks let Docker (and orchestrators like Kubernetes) know if your application is healthy.

```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health || exit 1
```

Parameters:

- `--interval=30s` – Check every 30 seconds.
- `--timeout=30s` – Fail if check takes longer than 30 seconds.
- `--start-period=5s` – Wait 5 seconds before first check.
- `--retries=3` – Mark container as unhealthy after 3 failures.

You’ll expose a `/health` endpoint in your API to support this.

---

## 9. Production Docker Compose Setup

### Example `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      SA_PASSWORD: "${DB_PASSWORD}"  # From environment variable or .env
      ACCEPT_EULA: "Y"
      MSSQL_PID: "Standard"  # Production edition
    volumes:
      - sqlserver_data:/var/opt/mssql  # Persistent storage
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P ${DB_PASSWORD} -Q 'SELECT 1' || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3

  app:
    build: 
      context: .
      dockerfile: Dockerfile
    environment:
      - DB_HOST=sqlserver        # Use service name as host
      - DB_PORT=1433
      - DB_NAME=inventory
      - DB_USER=sa
      - DB_PASSWORD=${DB_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false              # Production setting
    ports:
      - "8000:8000"
    depends_on:
      sqlserver:
        condition: service_healthy  # Wait for DB to be ready
    networks:
      - app-network
    restart: unless-stopped        # Auto-restart on failure

networks:
  app-network:
    driver: bridge

volumes:
  sqlserver_data:
```

### Why This Setup?

- **Service discovery** – `DB_HOST=sqlserver` uses the Compose service name.
- **Persistence** – `sqlserver_data` volume keeps DB data across restarts.
- **Health checks** – App waits until SQL Server is healthy.
- **Restart policy** – Automatically restarts crashed containers.

---

## 10. Environment Configuration

### `.env` File (Not Committed to Git)

```bash
# .env
DB_PASSWORD=YourStrongProductionPassw0rd!
SECRET_KEY=your-super-secret-production-key
DEBUG=false
```

Compose will load this automatically if `.env` is in the same directory, or you can specify:

```yaml
services:
  app:
    env_file:
      - .env
```

**Rule of thumb:** Secrets and environment-specific values live **outside** the image.

---

## 11. Network and Volume Configuration

### Docker Networks

```yaml
networks:
  app-network:
    driver: bridge
```

- Containers in the same network can reach each other by **service name**.
- Provides **isolation** from other containers on the host.

### Volumes

```yaml
volumes:
  sqlserver_data:

services:
  sqlserver:
    volumes:
      - sqlserver_data:/var/opt/mssql
```

- **Named volumes** – Managed by Docker, ideal for production data.
- **Bind mounts** – Map to host directories (more common in development).

---

## 12. Common Questions

**Q: Why use slim Python images?**  
**A:** They are smaller (tens or hundreds of MB vs ~1GB) and contain only essential OS components, which improves:

- Security (smaller attack surface).
- Speed (faster downloads and starts).

---

**Q: What's the difference between `CMD` and `ENTRYPOINT`?**  

- `ENTRYPOINT` – Defines the main executable.
- `CMD` – Provides default arguments or command.

Most apps can use `CMD` alone; combining both gives fine-grained control.

---

**Q: Why copy from the builder stage instead of building in the final stage?**  
**A:** The builder stage can contain compilers, dev tools, and package managers like `uv`. The final stage remains **minimal and secure**, containing only what’s needed at runtime.

---

**Q: What does `restart: unless-stopped` do?**  
**A:** Docker will restart the container if it exits unexpectedly, but **not** if you stop it manually.

---

**Q: Why use health checks?**  
**A:** They allow Docker and orchestrators (like Kubernetes) to detect unhealthy containers and restart/replace them automatically.

---

## 13. Building and Running

### Building the Image

```bash
# Build latest image
docker build -t inventory-system:latest .

# Build with specific tag
docker build -t inventory-system:v1.0.0 .

# View built images
docker images
```

### Running with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale application instances
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

### Environment Setup

```bash
# Create .env file for production
echo "DB_PASSWORD=YourStrongProductionPassw0rd!" > .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "DEBUG=false" >> .env
```

---

## 14. Monitoring and Maintenance

### Container Status

```bash
# Check running containers
docker ps

# View container logs
docker logs <container_id>

# Real-time stats (CPU, memory)
docker stats

# Exec into a running container
docker exec -it <container_id> bash

# View health status
docker inspect --format='{{.State.Health.Status}}' <container_id>
```

### Compose Logs

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs app

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f app
```

---

## 15. Further Reading

### Essential References

- Docker Documentation – <https://docs.docker.com/>
- Dockerfile Reference – <https://docs.docker.com/engine/reference/builder/>
- Docker Compose Reference – <https://docs.docker.com/compose/compose-file/>
- The Twelve-Factor App – <https://12factor.net/>

### Deep Dive Topics

- Docker Security Best Practices – <https://docs.docker.com/engine/security/>
- Multi-stage Builds – <https://docs.docker.com/build/building/multi-stage/>
- Docker Storage – <https://docs.docker.com/storage/>
- Container Networking – <https://docs.docker.com/network/>

---

## 16. Practice Exercises (Day 8)

1. **Optimize your Dockerfile** for faster builds using layer caching.
2. Create **separate Dockerfiles** for development and production.
3. Implement **Docker image scanning** (e.g., with Trivy or Docker Scout) for vulnerabilities.
4. Set up **centralized logging** for Docker containers (e.g., ELK, Loki).
5. Create a **CI/CD pipeline** that builds, tests, and pushes Docker images to a registry.

---

## 17. Key Takeaways

- **Multi-stage builds** create smaller, more secure production images.
- Use **non-root users** and minimal base images for better security.
- **Health checks** enable automatic container monitoring and recovery.
- **Docker Compose** simplifies multi-container deployments.
- **Environment variables** provide flexible, environment-specific configuration.
- **Named volumes** ensure data persistence across container restarts.
- **Custom networks** enable secure service communication between containers.

---

## 18. Coming Up Next (Day 9)

Tomorrow we’ll deploy the containerized application to **Kubernetes** for production orchestration, exploring Deployments, Services, ConfigMaps, and Secrets.
