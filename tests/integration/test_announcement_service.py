from app.services.announcement_service import AnnouncementService


def test_announcement_lifecycle(test_db):
    service = AnnouncementService(test_db)

    # Create announcement
    ann = service.create_announcement(
        title="Annual Company Offsite",
        content="The annual offsite will take place in Goa from Dec 10-14.",
        priority="Urgent",
        target_role="all",
        posted_by="admin123",
    )

    assert ann.id is not None
    assert ann.title == "Annual Company Offsite"
    assert ann.is_active is True

    # Get active announcements
    active = service.get_active(target_role="employee")
    assert len(active) >= 1
    assert any(a.id == ann.id for a in active)

    # Toggle status
    toggled = service.toggle_status(ann.id, is_active=False, actor_username="admin123")
    assert toggled.is_active is False

    # Check active again
    active_after = service.get_active(target_role="employee")
    assert not any(a.id == ann.id for a in active_after)

    # Delete
    deleted = service.delete(ann.id, actor_username="admin123")
    assert deleted is True
