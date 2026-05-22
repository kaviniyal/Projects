"""
SQLAlchemy ORM models for the Helpdesk Ticket Management System.

Defines the Ticket model that maps to the `tickets` table in the database.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Ticket(Base):
    """ORM model representing a support ticket."""

    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_name = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    issue_category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="Medium", index=True)
    status = Column(String(20), nullable=False, default="Open", index=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.ticket_id}, "
            f"employee='{self.employee_name}', "
            f"status='{self.status}')>"
        )
