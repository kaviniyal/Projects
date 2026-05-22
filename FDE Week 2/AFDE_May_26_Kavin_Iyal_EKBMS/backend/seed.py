"""
Seed script — initializes roles, a default admin user, and sample categories.

Runs automatically on backend startup if the database is empty. Idempotent:
running it multiple times is safe.
"""

from sqlalchemy.orm import Session

import models
from auth import hash_password


DEFAULT_ROLES = [
    ("Admin", "Full system access — manage users, categories, and settings"),
    ("Author", "Create and manage knowledge articles"),
    ("Reviewer", "Review and approve submitted articles"),
    ("Employee", "Search and read approved articles"),
]

DEFAULT_CATEGORIES = [
    ("HR Policies", "Human resources policies and procedures"),
    ("IT Support", "Technical support and troubleshooting guides"),
    ("Infrastructure", "Network, servers, and infrastructure documentation"),
    ("Training Materials", "Onboarding and training documents"),
    ("Finance", "Finance and accounting procedures"),
    ("Operations", "Operational SOPs and process documentation"),
]


def seed_roles(db: Session):
    """Create the four standard roles if they don't already exist."""
    for name, desc in DEFAULT_ROLES:
        existing = db.query(models.Role).filter(models.Role.role_name == name).first()
        if not existing:
            db.add(models.Role(role_name=name, description=desc))
    db.commit()


def seed_admin(db: Session):
    """
    Create a default admin user if no admin exists yet.

    Default credentials (CHANGE IN PRODUCTION):
        email:    admin@example.com
        password: admin123
    """
    admin_role = db.query(models.Role).filter(models.Role.role_name == "Admin").first()
    if not admin_role:
        return

    existing_admin = db.query(models.User).filter(models.User.role_id == admin_role.role_id).first()
    if existing_admin:
        return

    admin = models.User(
        name="System Administrator",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        department="IT",
        role_id=admin_role.role_id,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("[OK] Default admin created - email: admin@example.com, password: admin123")


def seed_categories(db: Session):
    """Create the default categories if none exist."""
    if db.query(models.Category).count() > 0:
        return
    for name, desc in DEFAULT_CATEGORIES:
        db.add(models.Category(category_name=name, description=desc))
    db.commit()


def seed_all(db: Session):
    """Run all seeders in order."""
    seed_roles(db)
    seed_admin(db)
    seed_categories(db)
