"""
Pydantic Models for Coffee Rating Application.
Module 2: Backend Development
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status response model."""
    status: str = Field(default="healthy", description="Status of the backend API service")
    service: str = Field(default="Coffee Rating API", description="Name of the service")


class CoffeeBase(BaseModel):
    """Base schema for coffee items."""
    id: str = Field(..., description="Unique alphanumeric identifier for the coffee", example="cappuccino")
    name: str = Field(..., description="Display name of the coffee", example="Cappuccino")
    description: str = Field(..., description="Short appetizing description of the coffee flavor profile")
    image_url: str = Field(..., description="URL to high-quality coffee image")


class CoffeeResponse(CoffeeBase):
    """Response schema representing a coffee item including current vote count."""
    votes: int = Field(default=0, ge=0, description="Total independent votes cast for this coffee")

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., description="Error message explaining what went wrong")
