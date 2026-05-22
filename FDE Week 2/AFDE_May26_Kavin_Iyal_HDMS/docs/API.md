# API Documentation

Base URL: `http://localhost:8000`

All endpoints return JSON. Errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors (HTTP 422) also include an `errors` array with per-field details.

---

## Health Endpoints

### `GET /`

Root endpoint. Returns service metadata.

**Response 200:**
```json
{
  "message": "Helpdesk Ticket Management System API",
  "version": "1.0.0",
  "docs": "/docs",
  "status": "running"
}
```

### `GET /health`

Simple health check.

**Response 200:**
```json
{ "status": "healthy" }
```

---

## Ticket Endpoints

### `GET /tickets`

Retrieve all tickets, optionally filtered.

**Query parameters:**

| Name | Type | Description |
|---|---|---|
| skip | int | Records to skip (default 0) |
| limit | int | Max records to return (default 100, max 500) |
| status | string | Filter by status |
| category | string | Filter by issue category |
| priority | string | Filter by priority |

**Example:** `GET /tickets?status=Open&priority=High&limit=10`

**Response 200:**
```json
[
  {
    "ticket_id": 1,
    "employee_name": "John Doe",
    "department": "Engineering",
    "issue_category": "VPN Issue",
    "description": "Cannot connect to VPN from home",
    "priority": "High",
    "status": "Open",
    "resolution_notes": null,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

---

### `GET /tickets/summary`

Get aggregate ticket statistics for the dashboard.

**Response 200:**
```json
{
  "total_tickets": 42,
  "open_tickets": 15,
  "in_progress_tickets": 10,
  "resolved_tickets": 12,
  "closed_tickets": 5,
  "critical_priority": 3,
  "high_priority": 8
}
```

---

### `GET /tickets/{id}`

Retrieve a single ticket by ID.

**Path parameter:** `id` (integer) — ticket ID

**Response 200:** ticket object (same shape as above).

**Response 404:**
```json
{ "detail": "Ticket with id 999 not found" }
```

---

### `POST /tickets`

Create a new ticket.

**Request body:**
```json
{
  "employee_name": "John Doe",
  "department": "Engineering",
  "issue_category": "VPN Issue",
  "description": "Cannot connect to VPN from home",
  "priority": "High"
}
```

**Required fields:** `employee_name`, `department`, `issue_category`, `description`
**Optional fields:** `priority` (defaults to "Medium")

**Constraints:**
- `employee_name`: 1–100 characters
- `department`: 1–100 characters
- `issue_category`: must be one of the allowed values (see below)
- `description`: minimum 5 characters
- `priority`: must be one of the allowed values
- `status`: always "Open" for new tickets (set automatically by the server)

**Response 201:** the newly created ticket object.

**Response 422:** validation error.

---

### `PUT /tickets/{id}`

Update an existing ticket. All fields are optional — only fields you send will be updated.

**Path parameter:** `id` (integer)

**Request body example:**
```json
{
  "status": "In Progress",
  "resolution_notes": "Investigating the issue"
}
```

**Updatable fields:** `employee_name`, `department`, `issue_category`, `description`, `priority`, `status`, `resolution_notes`

**Response 200:** the updated ticket object.

**Response 404:** ticket not found.

---

### `DELETE /tickets/{id}`

Delete a ticket.

**Path parameter:** `id` (integer)

**Response 200:**
```json
{ "message": "Ticket 1 deleted successfully" }
```

**Response 404:** ticket not found.

---

## Search Endpoint

### `GET /search`

Search tickets with a free-text keyword and/or filters.

**Query parameters:**

| Name | Type | Description |
|---|---|---|
| keyword | string | Searches across employee_name, department, description, resolution_notes, and category |
| status | string | Filter by status |
| category | string | Filter by category |
| priority | string | Filter by priority |

**Example:** `GET /search?keyword=VPN&status=Open`

**Response 200:** array of matching ticket objects.

---

## Allowed Values

### Issue Categories
- `VPN Issue`
- `Password Reset`
- `Software Installation`
- `Laptop Issue`
- `Email Access`
- `Network Connectivity`
- `Hardware Request`

### Priorities
- `Low`
- `Medium`
- `High`
- `Critical`

### Statuses
- `Open`
- `In Progress`
- `Resolved`
- `Closed`

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | OK — request succeeded |
| 201 | Created — new resource was created |
| 404 | Not Found — resource doesn't exist |
| 422 | Unprocessable Entity — validation error |
| 500 | Internal Server Error — unexpected server error |

---

## Interactive Documentation

Once the backend is running, FastAPI provides interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both are auto-generated from the API code, so they always reflect the actual implementation.
