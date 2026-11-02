"""
CloudGuard API Application Entrypoint.
FastAPI backend orchestrating disaster recovery verification and compliance reporting.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.config import settings
    from app.database import engine, Base
    from app.core.logging import logger
    from app.api import health, recovery_tests, backups, validations, reports, dr_pipeline, applications
except ImportError:
    from .config import settings
    from .database import engine, Base
    from .core.logging import logger
    from .api import health, recovery_tests, backups, validations, reports, dr_pipeline, applications


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CloudGuard API and creating database schemas if not present...")
    Base.metadata.create_all(bind=engine)
    logger.info("CloudGuard API ready to receive DR verification requests.")
    yield
    logger.info("CloudGuard API shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Disaster Recovery Verification and Reporting Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(recovery_tests.router)
app.include_router(backups.router)
app.include_router(validations.router)
app.include_router(reports.router)
app.include_router(dr_pipeline.router)
app.include_router(applications.router)


@app.get("/", tags=["Root"])
def root_info():
    return {
        "platform": "CloudGuard Disaster Recovery Monitoring and Reporting Platform",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "health_url": "/health",
        "readiness_url": "/ready"
    }
