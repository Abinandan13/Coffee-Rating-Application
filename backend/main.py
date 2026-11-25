"""
Main FastAPI Application for Coffee Rating Application.
Module 3: Database Integration with SQLite & SQLAlchemy

Features:
- Persistent SQLite database storage (coffee_rating.db).
- Automatic table creation and initial seed data on startup.
- Atomic vote increment transactions to prevent concurrency race conditions.
- GET /health: API health check.
- GET /api/coffees: Retrieve all coffees from SQLite with latest vote counts.
- POST /api/coffees/{coffee_id}/vote: Increment vote count atomically by 1.
- Automatic Swagger documentation at /docs.
- CORS enabled for local frontend development.
"""

from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import update

from database import init_db, get_db, Coffee
from models import CoffeeResponse, HealthResponse, ErrorResponse


# ==============================================================================
# FastAPI Lifespan Handler (Startup & Shutdown)
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that initializes the SQLite database
    and seeds initial coffee records on application startup.
    """
    init_db()
    yield


# ==============================================================================
# FastAPI Application Initialization & Metadata
# ==============================================================================
app = FastAPI(
    title="Coffee Rating API",
    description=(
        "Backend API service for the Coffee Rating Application (Module 3). "
        "Provides persistent SQLite coffee catalogue storage, real-time "
        "atomic vote tracking, and health status monitoring."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ==============================================================================
# CORS Configuration
# ==============================================================================
# Allows the local frontend development server or browser to interact with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Check Backend Health",
    description="Returns backend health status and service confirmation."
)
def get_health() -> HealthResponse:
    """Check if backend service is operational."""
    return HealthResponse(status="healthy", service="Coffee Rating API")


@app.get(
    "/api/coffees",
    response_model=List[CoffeeResponse],
    status_code=status.HTTP_200_OK,
    tags=["Coffees"],
    summary="Get All Coffees",
    description="Returns all four coffee items retrieved from SQLite along with their latest vote counts."
)
def get_coffees(db: Session = Depends(get_db)) -> List[CoffeeResponse]:
    """Retrieve all available coffees and their vote counts from the SQLite database."""
    coffees = db.query(Coffee).all()
    return coffees


@app.post(
    "/api/coffees/{coffee_id}/vote",
    response_model=CoffeeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Coffee ID was not found in the database"
        }
    },
    tags=["Voting"],
    summary="Vote for a Coffee",
    description="Atomically increases the vote count of the specified coffee by exactly 1 in SQLite and returns updated details."
)
def vote_for_coffee(coffee_id: str, db: Session = Depends(get_db)) -> CoffeeResponse:
    """
    Accepts a coffee ID, finds the coffee in the database,
    atomically increments its vote count by exactly 1,
    commits the change to SQLite, and returns updated details.
    Raises HTTP 404 if the coffee ID does not exist.
    """
    normalized_id = coffee_id.strip().lower()

    # Perform atomic update to prevent race conditions during concurrent voting
    stmt = (
        update(Coffee)
        .where(Coffee.id == normalized_id)
        .values(votes=Coffee.votes + 1)
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coffee with ID '{coffee_id}' not found."
        )

    # Commit atomic transaction to SQLite
    db.commit()

    # Query and return updated record
    updated_coffee = db.query(Coffee).filter(Coffee.id == normalized_id).first()
    return updated_coffee


# ==============================================================================
# Entry Point for Direct Execution
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    init_db()  # Direct fallback for running directly without ASGI lifespan
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
