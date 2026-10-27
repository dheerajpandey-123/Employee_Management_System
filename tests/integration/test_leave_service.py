from datetime import date, timedelta
from app.models.employee import Employee
from app.services.leave_service import LeaveService


def test_apply_and_review_leave(test_db):
    # Setup employee
    emp = Employee(
        employee_id="TEST_EMP_01",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="9876543210",
        department="Engineering",
        designation="Software Engineer",
        joining_date=date.today() - timedelta(days=100),
        salary=75000.0,
        status="active",
        created_at=date.today(),
        updated_at=date.today(),
    )
    test_db.add(emp)
    test_db.commit()
    test_db.refresh(emp)

    service = LeaveService(test_db)

    # Apply leave
    start = date.today() + timedelta(days=1)
    end = date.today() + timedelta(days=3)
    leave = service.apply_leave(
        employee_id=emp.id,
        leave_type="Casual Leave",
        start_date=start,
        end_date=end,
        reason="Family event",
        actor_username="john.doe",
    )

    assert leave.id is not None
    assert leave.days_count == 3
    assert leave.status == "Pending"

    # Count pending
    assert service.count_pending() >= 1

    # Leave balance
    balance = service.get_leave_balance(emp.id)
    assert balance["Casual Leave"]["pending"] == 3
    assert balance["Casual Leave"]["total"] == 12

    # Review leave - Approve
    reviewed = service.review_leave(
        leave_id=leave.id,
        status="Approved",
        admin_remarks="Approved by Manager",
        actor_username="admin123",
    )
    assert reviewed.status == "Approved"
    assert reviewed.admin_remarks == "Approved by Manager"

    # Balance check after approval
    balance2 = service.get_leave_balance(emp.id)
    assert balance2["Casual Leave"]["used"] == 3
    assert balance2["Casual Leave"]["remaining"] == 9
