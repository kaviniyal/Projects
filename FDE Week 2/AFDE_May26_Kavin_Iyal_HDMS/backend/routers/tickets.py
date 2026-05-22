"""
Ticket-related API routes.

All endpoints related to ticket CRUD operations and search are mounted
under the `/tickets` and `/search` paths from `main.py`.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Ticket CRUD endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/tickets",
    response_model=List[schemas.TicketResponse],
    summary="Retrieve all tickets",
    tags=["Tickets"],
)
def read_tickets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
):
    """Retrieve all tickets, optionally filtered."""
    return crud.get_tickets(
        db, skip=skip, limit=limit, status=status, category=category, priority=priority
    )


@router.get(
    "/tickets/summary",
    response_model=schemas.TicketSummary,
    summary="Get ticket summary statistics",
    tags=["Tickets"],
)
def read_ticket_summary(db: Session = Depends(get_db)):
    """Return aggregate ticket counts for the dashboard."""
    return crud.get_summary(db)


@router.get(
    "/tickets/{ticket_id}",
    response_model=schemas.TicketResponse,
    summary="Retrieve a ticket by ID",
    tags=["Tickets"],
)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a single ticket by its ID."""
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found",
        )
    return db_ticket


@router.post(
    "/tickets",
    response_model=schemas.TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ticket",
    tags=["Tickets"],
)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    """Create a new support ticket."""
    return crud.create_ticket(db=db, ticket=ticket)


@router.put(
    "/tickets/{ticket_id}",
    response_model=schemas.TicketResponse,
    summary="Update a ticket",
    tags=["Tickets"],
)
def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing ticket (partial updates supported)."""
    db_ticket = crud.update_ticket(db, ticket_id=ticket_id, ticket_update=ticket_update)
    if db_ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found",
        )
    return db_ticket


@router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a ticket",
    tags=["Tickets"],
)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket by its ID."""
    if not crud.delete_ticket(db, ticket_id=ticket_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found",
        )
    return {"message": f"Ticket {ticket_id} deleted successfully"}


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=List[schemas.TicketResponse],
    summary="Search tickets",
    tags=["Search"],
)
def search_tickets(
    keyword: Optional[str] = Query(None, description="Free-text search term"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
):
    """Search tickets by keyword, with optional filters."""
    return crud.search_tickets(
        db,
        keyword=keyword,
        status=status,
        category=category,
        priority=priority,
    )
