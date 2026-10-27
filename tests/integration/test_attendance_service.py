from datetime import date, timedelta
from app.models.employee import Employee
from app.services.attendance_service import AttendanceService


def test_clock_in_and_clock_out(test_db):
    emp = Employee(
        employee_id="TEST_EMP_02",
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        phone="9876543211",
        department="HR",
        designation="HR Specialist",
        joining_date=date.today() - timedelta(days=50),
        salary=60000.0,
        status="active",
        created_at=date.today(),
        updated_at=date.today(),
    )
    test_db.add(emp)
    test_db.commit()
    test_db.refresh(emp)

    service = AttendanceService(test_db)

    # Initial status
    status = service.get_today_status(emp.id)
    assert status["clocked_in"] is False

    # Clock in
    record = service.clock_in(emp.id, notes="On time", actor_username="alice.smith")
    assert record.clock_in is not None

    status_after_in = service.get_today_status(emp.id)
    assert status_after_in["clocked_in"] is True
    assert status_after_in["clocked_out"] is False

    # Clock out
    record_out = service.clock_out(emp.id, actor_username="alice.smith")
    assert record_out.clock_out is not None

    status_after_out = service.get_today_status(emp.id)
    assert status_after_out["clocked_out"] is True

    # Daily summary
    summary = service.get_daily_summary()
    assert summary["present_count"] >= 1
