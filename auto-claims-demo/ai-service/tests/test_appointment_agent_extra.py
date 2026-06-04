
def test_create_calendar_event_extra():
    from appointment_agent import create_calendar_event
    res = create_calendar_event("Shop X", "2024-01-01", "10:00 AM", "John")
    assert "appointment confirmed" in res.lower()
