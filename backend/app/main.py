"""
FastAPI application entry point
CORS enabled for frontend development
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.utils.logger import setup_logging

# Setup structured logging
logger = setup_logging()

# Create FastAPI app with metadata
app = FastAPI(
    title="Academic Paper Analysis API",
    description="Backend API for analyzing and visualizing academic paper citation networks",
    version=__version__,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# CORS configuration for frontend - MUST BE FIRST MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: Allow all origins
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Include API routes
app.include_router(router)

# Log application startup
logger.info(f"Academic Paper Analysis API v{__version__} initialized")
logger.info("CORS enabled: allow_origins=['*'], allow_methods=['*'], allow_headers=['*']")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint - redirects to docs"""
    return {"message": "Academic Paper Analysis API", "version": __version__, "docs": "/docs"}
