import pytest
from app.modules.schedule.service import ScheduleService


def test_create_event(db):
    svc = ScheduleService(db)
    ev = svc.create_event("晨会", "2026-06-10 09:00", "2026-06-10 10:00",
                          "讨论需求", "工作", 1)
    assert ev["title"] == "晨会"
    assert ev["category"] == "工作"
    assert ev["priority"] == 1
    assert ev["is_completed"] == 0


def test_create_event_empty_title(db):
    svc = ScheduleService(db)
    with pytest.raises(ValueError, match="标题不能为空"):
        svc.create_event("", "2026-06-10 09:00")


def test_create_event_start_after_end(db):
    svc = ScheduleService(db)
    with pytest.raises(ValueError, match="开始时间必须早于结束时间"):
        svc.create_event("test", "2026-06-10 10:00", "2026-06-10 09:00")


def test_create_event_invalid_category(db):
    svc = ScheduleService(db)
    with pytest.raises(ValueError, match="分类必须是"):
        svc.create_event("test", "2026-06-10 09:00", category="无效")


def test_create_event_invalid_priority(db):
    svc = ScheduleService(db)
    with pytest.raises(ValueError, match="优先级必须在1-3之间"):
        svc.create_event("test", "2026-06-10 09:00", priority=5)


def test_list_events(db):
    svc = ScheduleService(db)
    svc.create_event("晨会", "2026-06-10 09:00")
    svc.create_event("午餐", "2026-06-10 12:00")
    recs = svc.list_events()
    assert len(recs) == 2


def test_list_events_filter_category(db):
    svc = ScheduleService(db)
    svc.create_event("晨会", "2026-06-10 09:00", category="工作")
    svc.create_event("跑步", "2026-06-10 18:00", category="个人")
    recs = svc.list_events(category="工作")
    assert len(recs) == 1
    assert recs[0]["title"] == "晨会"


def test_update_event(db):
    svc = ScheduleService(db)
    ev = svc.create_event("晨会", "2026-06-10 09:00")
    updated = svc.update_event(ev["id"], title="项目晨会", priority=1)
    assert updated["title"] == "项目晨会"
    assert updated["priority"] == 1


def test_update_nonexistent_event(db):
    svc = ScheduleService(db)
    with pytest.raises(ValueError, match="日程不存在"):
        svc.update_event(999, title="test")


def test_mark_completed(db):
    svc = ScheduleService(db)
    ev = svc.create_event("晨会", "2026-06-10 09:00")
    completed = svc.mark_completed(ev["id"])
    assert completed["is_completed"] == 1
    # Toggle again
    uncompleted = svc.mark_completed(ev["id"])
    assert uncompleted["is_completed"] == 0


def test_delete_event(db):
    svc = ScheduleService(db)
    ev = svc.create_event("晨会", "2026-06-10 09:00")
    assert svc.delete_event(ev["id"]) is True
    assert svc.list_events() == []


def test_get_events_by_date(db):
    svc = ScheduleService(db)
    svc.create_event("晨会", "2026-06-10 09:00")
    svc.create_event("午餐", "2026-06-11 12:00")
    recs = svc.get_events_by_date("2026-06-10")
    assert len(recs) == 1


def test_get_events_by_month(db):
    svc = ScheduleService(db)
    svc.create_event("晨会", "2026-06-10 09:00")
    svc.create_event("午餐", "2026-07-01 12:00")
    recs = svc.get_events_by_month(2026, 6)
    assert len(recs) == 1
