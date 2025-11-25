# src/inventory_system/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.products import router as products_router
from .config.database import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_manager.setup()
    db_manager.create_tables()
    yield
    # Shutdown
    # Close database connections if needed


app = FastAPI(
    title="Inventory Management System",
    description="Professional inventory management API",
    version="1.0.0",
    lifespan=lifespan,
)


# Include routers
app.include_router(products_router)


@app.get("/")
async def root():
    return {"message": "Inventory Management System API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    from .config.settings import settings

    uvicorn.run(
        "inventory_system.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
