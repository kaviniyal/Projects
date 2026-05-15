"""
Pydantic schemas for request validation and response serialization.

Separating input (Create / Update) from output (Response) schemas keeps
the API contract explicit and prevents accidentally exposing internal
fields.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations — kept as string-valued enums so they serialize cleanly to
# JSON and remain human-readable in the database.
# ---------------------------------------------------------------------------


class PriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class StatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class CategoryEnum(str, Enum):
    VPN_ISSUE = "VPN Issue"
    PASSWORD_RESET = "Password Reset"
    SOFTWARE_INSTALLATION = "Software Installation"
    LAPTOP_ISSUE = "Laptop Issue"
    EMAIL_ACCESS = "Email Access"
    NETWORK_CONNECTIVITY = "Network Connectivity"
    HARDWARE_REQUEST = "Hardware Request"


# ---------------------------------------------------------------------------
# Ticket schemas
# ---------------------------------------------------------------------------


class TicketBase(BaseModel):
    """Fields common to ticket creation and updates."""

    employee_name: str = Field(..., min_length=1, max_length=100, description="Name of the employee raising the ticket")
    department: str = Field(..., min_length=1, max_length=100, description="Department of the employee")
    issue_category: CategoryEnum = Field(..., description="Category of the issue")
    description: str = Field(..., min_length=5, description="Detailed description of the issue")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Priority level")


class TicketCreate(TicketBase):
    """Schema used when creating a new ticket."""

    pass


class TicketUpdate(BaseModel):
    """
    Schema used when updating a ticket.

    All fields are optional so the caller can perform partial updates;
    only the fields they include will be modified.
    """

    employee_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    issue_category: Optional[CategoryEnum] = None
    description: Optional[str] = Field(None, min_length=5)
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    resolution_notes: Optional[str] = None


class TicketResponse(TicketBase):
    """Schema used when returning a ticket to the client."""

    ticket_id: int
    status: StatusEnum
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode


class TicketSummary(BaseModel):
    """Aggregate counts used by the dashboard."""

    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    critical_priority: int
    high_priority: int
