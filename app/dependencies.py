"""
Shared dependencies for FastAPI endpoints.

This file contains reusable dependencies that can be used across multiple endpoints.
This follows the DRY (Don't Repeat Yourself) principle and makes code more maintainable.
"""

from fastapi import Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db


# ============ Pagination Dependency ============
# This is a reusable pagination dependency that can be used in any endpoint
# Use this when you have simple pagination needs (1-3 query params)

class PaginationParams:
    """
    Reusable pagination parameters.
    
    Use this for simple endpoints that only need pagination.
    For complex endpoints with many filters, use query parameter schemas instead.
    """
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(10, ge=1, le=100, description="Maximum records to return")
    ):
        self.skip = skip
        self.limit = limit


# ============ Simple Query Parameter Examples ============
# These show when individual Query() parameters are appropriate

def get_simple_product_filters(
    name: Optional[str] = Query(None, description="Filter by product name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    Simple filter dependency for products.
    
    Use this pattern when you have 1-3 simple filters.
    For 4+ filters, use a schema with Depends() instead.
    """
    return {
        "name": name,
        "is_active": is_active
    }


# ============ Database Session Dependency ============
# Already in database.py, but shown here for reference
# This is the standard pattern for database access

def get_database_session() -> Session:
    """
    Dependency for database session.
    
    This is already defined in database.py as get_db().
    Shown here as an example of dependency pattern.
    """
    return Depends(get_db)

