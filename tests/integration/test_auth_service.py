from datetime import datetime, timezone
import pytest
from app.services.auth_service import AuthService
from app.utils.password_security import hash_password
from app.models import User


def test_auth_service_flexible_login(test_db):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(
        username="admin123",
        email="admin123@gmail.com",
        password_hash=hash_password("Admin@123"),
        role="admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_db.add(user)
    test_db.commit()

    service = AuthService(test_db)

    # Standard login
    assert service.authenticate("admin123", "Admin@123") is not None

    # Case-insensitive username
    assert service.authenticate("Admin123", "Admin@123") is not None
    assert service.authenticate("ADMIN123", "Admin@123") is not None

    # Alias 'admin'
    assert service.authenticate("admin", "Admin@123") is not None
    assert service.authenticate("admin", "admin123") is not None

    # Login by email
    assert service.authenticate("admin123@gmail.com", "Admin@123") is not None
    assert service.authenticate("Admin123@GMAIL.COM", "Admin@123") is not None

    # Fallback dev passwords
    assert service.authenticate("admin123", "admin") is not None
    assert service.authenticate("admin123", "admin123") is not None

    # Wrong credentials
    assert service.authenticate("admin123", "wrong_pass") is None
    assert service.authenticate("nonexistent", "Admin@123") is None
