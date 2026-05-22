-- ============================================================================
-- Helpdesk Ticket Management System — Database Schema
-- ============================================================================
-- This script creates the tickets table.
-- ============================================================================

-- SQLite version
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name    VARCHAR(100) NOT NULL,
    department       VARCHAR(100) NOT NULL,
    issue_category   VARCHAR(100) NOT NULL,
    description      TEXT NOT NULL,
    priority         VARCHAR(20)  NOT NULL DEFAULT 'Medium',
    status           VARCHAR(20)  NOT NULL DEFAULT 'Open',
    resolution_notes TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common lookups and filters
CREATE INDEX IF NOT EXISTS idx_tickets_status        ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority      ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category      ON tickets(issue_category);
CREATE INDEX IF NOT EXISTS idx_tickets_employee      ON tickets(employee_name);
CREATE INDEX IF NOT EXISTS idx_tickets_department    ON tickets(department);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at    ON tickets(created_at);


