"""
Demo Banking Application Entrypoint.
FastAPI application simulating a core banking system with customer, account, and transaction services.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, get_db
from .seeder import seed_banking_data
from .core.exceptions import BankingException
from .api import health, customers, accounts, transactions, validation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    # Seed realistic synthetic banking records
    db = next(get_db())
    try:
        seed_banking_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="CloudGuard Monitored Banking Application",
    description="Demo core banking platform running FastAPI and PostgreSQL for disaster recovery verification.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BankingException)
async def banking_exception_handler(request: Request, exc: BankingException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )


# Register API Routers
app.include_router(health.router)
app.include_router(customers.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(validation.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "CloudGuard Monitored Banking Application",
        "version": "2.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "ready_url": "/ready"
    }
