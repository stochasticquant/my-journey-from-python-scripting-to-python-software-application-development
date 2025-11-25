# Dockerfile
FROM python:3.11-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.11-slim

# Install SQL Server ODBC driver
RUN apt-get update && apt-get install -y     curl     gnupg     && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -     && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list     && apt-get update     && ACCEPT_EULA=Y apt-get install -y msodbcsql18     && apt-get clean     && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy from builder
COPY --from=builder /app /home/app

# Set environment variables
ENV PYTHONPATH=/home/app/src
ENV PATH="/home/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "inventory_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
