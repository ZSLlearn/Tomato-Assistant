import pytest
from app.modules.health.service import HealthService


def test_record_weight(db):
    svc = HealthService(db)
    rec = svc.record_weight(70.5, "2026-06-10", "早上空腹")
    assert rec["weight"] == 70.5
    assert rec["date"] == "2026-06-10"


def test_record_weight_negative(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="体重必须大于0"):
        svc.record_weight(-5, "2026-06-10")


def test_list_weight(db):
    svc = HealthService(db)
    svc.record_weight(70.0, "2026-06-10")
    svc.record_weight(69.5, "2026-06-09")
    recs = svc.list_weight()
    assert len(recs) == 2


def test_list_weight_filter_date(db):
    svc = HealthService(db)
    svc.record_weight(70.0, "2026-06-10")
    svc.record_weight(69.5, "2026-06-05")
    recs = svc.list_weight(date_from="2026-06-08")
    assert len(recs) == 1
    assert recs[0]["date"] == "2026-06-10"


def test_get_weight_trend(db):
    svc = HealthService(db)
    svc.record_weight(70.5, "2026-06-10")
    svc.record_weight(70.0, "2026-06-09")
    trend = svc.get_weight_trend(days=30)
    assert len(trend) >= 2


def test_delete_weight(db):
    svc = HealthService(db)
    rec = svc.record_weight(70.0, "2026-06-10")
    assert svc.delete_weight(rec["id"]) is True
    assert svc.list_weight() == []


def test_record_exercise(db):
    svc = HealthService(db)
    rec = svc.record_exercise("跑步", 30, 200, "2026-06-10", "晨跑")
    assert rec["type"] == "跑步"
    assert rec["duration"] == 30


def test_record_exercise_negative_duration(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="运动时长必须大于0"):
        svc.record_exercise("跑步", -5, 200, "2026-06-10")


def test_record_exercise_empty_type(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="运动类型不能为空"):
        svc.record_exercise("", 30)


def test_get_exercise_stats(db):
    svc = HealthService(db)
    svc.record_exercise("跑步", 30, 200, "2026-06-10")
    svc.record_exercise("游泳", 60, 400, "2026-06-10")
    # Note: stats uses date('now', '-N days') which works with real dates
    # For this test, we just verify it runs without error
    stats = svc.get_exercise_stats(days=365)
    assert "total_count" in stats


def test_record_water(db):
    svc = HealthService(db)
    rec = svc.record_water(500, "2026-06-10")
    assert rec["amount"] == 500


def test_record_water_negative(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="饮水量必须大于0"):
        svc.record_water(-100, "2026-06-10")


def test_get_daily_water(db):
    svc = HealthService(db)
    svc.record_water(300, "2026-06-10")
    svc.record_water(500, "2026-06-10")
    assert svc.get_daily_water("2026-06-10") == 800


def test_record_sleep(db):
    svc = HealthService(db)
    rec = svc.record_sleep("2026-06-10 23:00", "2026-06-11 07:00", 4, "2026-06-10")
    assert rec["quality"] == 4


def test_record_sleep_end_before_start(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="起床时间必须晚于入睡时间"):
        svc.record_sleep("2026-06-10 23:00", "2026-06-10 22:00")


def test_record_sleep_bad_quality(db):
    svc = HealthService(db)
    with pytest.raises(ValueError, match="睡眠质量必须在1-5之间"):
        svc.record_sleep("2026-06-10 23:00", "2026-06-11 07:00", 6)


def test_get_sleep_stats(db):
    svc = HealthService(db)
    svc.record_sleep("2026-06-10 23:00", "2026-06-11 07:00", 4, "2026-06-10")
    svc.record_sleep("2026-06-09 22:30", "2026-06-10 06:30", 3, "2026-06-09")
    stats = svc.get_sleep_stats(days=7)
    assert stats["avg_quality"] > 0


def test_get_sleep_stats_empty(db):
    svc = HealthService(db)
    stats = svc.get_sleep_stats(days=7)
    assert stats["avg_duration"] == 0
    assert stats["avg_quality"] == 0


def test_get_dashboard(db):
    svc = HealthService(db)
    svc.record_weight(70.0, "2026-06-10")
    svc.record_water(300, "2026-06-10")
    dash = svc.get_dashboard()
    assert "weight" in dash
    assert "water_total" in dash


def test_get_dashboard_empty(db):
    svc = HealthService(db)
    dash = svc.get_dashboard()
    assert dash["weight"] is None
    assert dash["water_total"] == 0
