"""
CRUD (Create, Read, Update, Delete) operations for tickets.

Each function takes a SQLAlchemy session and operates on the Ticket model.
Keeping database logic here — separate from the route handlers — makes the
codebase easier to test and reuse.
"""

from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
import schemas


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    """Return a single ticket by its ID, or None if not found."""
    return db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()


def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[models.Ticket]:
    """
    Return a list of tickets, optionally filtered by status, category,
    or priority.
    """
    query = db.query(models.Ticket)

    if status:
        query = query.filter(models.Ticket.status == status)
    if category:
        query = query.filter(models.Ticket.issue_category == category)
    if priority:
        query = query.filter(models.Ticket.priority == priority)

    return (
        query.order_by(models.Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def search_tickets(
    db: Session,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[models.Ticket]:
    """
    Search tickets by keyword across employee_name, department, description,
    and resolution_notes, with optional filters.
    """
    query = db.query(models.Ticket)

    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                models.Ticket.employee_name.ilike(pattern),
                models.Ticket.department.ilike(pattern),
                models.Ticket.description.ilike(pattern),
                models.Ticket.resolution_notes.ilike(pattern),
                models.Ticket.issue_category.ilike(pattern),
            )
        )

    if status:
        query = query.filter(models.Ticket.status == status)
    if category:
        query = query.filter(models.Ticket.issue_category == category)
    if priority:
        query = query.filter(models.Ticket.priority == priority)

    return query.order_by(models.Ticket.created_at.desc()).all()


def get_summary(db: Session) -> dict:
    """Return aggregate ticket counts used by the dashboard."""
    total = db.query(models.Ticket).count()
    open_count = db.query(models.Ticket).filter(models.Ticket.status == "Open").count()
    in_progress = db.query(models.Ticket).filter(models.Ticket.status == "In Progress").count()
    resolved = db.query(models.Ticket).filter(models.Ticket.status == "Resolved").count()
    closed = db.query(models.Ticket).filter(models.Ticket.status == "Closed").count()
    critical = db.query(models.Ticket).filter(models.Ticket.priority == "Critical").count()
    high = db.query(models.Ticket).filter(models.Ticket.priority == "High").count()

    return {
        "total_tickets": total,
        "open_tickets": open_count,
        "in_progress_tickets": in_progress,
        "resolved_tickets": resolved,
        "closed_tickets": closed,
        "critical_priority": critical,
        "high_priority": high,
    }


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def create_ticket(db: Session, ticket: schemas.TicketCreate) -> models.Ticket:
    """Create and persist a new ticket."""
    db_ticket = models.Ticket(
        employee_name=ticket.employee_name,
        department=ticket.department,
        issue_category=ticket.issue_category.value,
        description=ticket.description,
        priority=ticket.priority.value,
        status="Open",  # Newly-created tickets always start as Open
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(
    db: Session, ticket_id: int, ticket_update: schemas.TicketUpdate
) -> Optional[models.Ticket]:
    """Partially update a ticket. Returns None if the ticket does not exist."""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    # `exclude_unset=True` makes this a true PATCH — only the fields the
    # caller explicitly sent are touched.
    update_data = ticket_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        # Pydantic enums need their `.value` extracted before being assigned
        # to a plain string column.
        if hasattr(value, "value"):
            value = value.value
        setattr(db_ticket, key, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    """Delete a ticket. Returns True if a row was deleted, False otherwise."""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False

    db.delete(db_ticket)
    db.commit()
    return True
