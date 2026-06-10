from app.modules.finance.service import FinanceService
from app.modules.health.service import HealthService
from app.modules.schedule.service import ScheduleService
from app.modules.memo.service import MemoService
from app.modules.weather.service import WeatherService
from app.ai.tool_executor import ToolExecutor


class FakeWeatherService:
    """Mock weather service for testing without API calls."""
    def get_real_time(self, city):
        return {"city": city, "temp": "25", "text": "晴"}
    def get_forecast(self, city, days=7):
        return [{"date": "2026-06-10", "temp_max": "30", "temp_min": "20"}]
    def get_life_index(self, city):
        return [{"type": "穿衣", "level": "1", "text": "较舒适"}]


def test_execute_add_finance(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    executor = ToolExecutor(svc, None, None, None, None)
    result = executor.execute("add_finance_record",
                              {"category_id": cat["id"], "type": "expense", "amount": 30,
                               "date": "2026-06-10", "note": "午饭"})
    assert result["amount"] == 30


def test_execute_query_finance(db):
    svc = FinanceService(db)
    cat = svc.create_category("工资", "income")
    svc.add_record(cat["id"], "income", 5000, "2026-06-10")
    executor = ToolExecutor(svc, None, None, None, None)
    result = executor.execute("query_finance",
                              {"query_type": "monthly_summary", "year": 2026, "month": 6})
    assert result["total_income"] == 5000


def test_execute_record_health_weight(db):
    svc = HealthService(db)
    executor = ToolExecutor(None, svc, None, None, None)
    result = executor.execute("record_health",
                              {"health_type": "weight", "value": 70.5, "date": "2026-06-10"})
    assert result["weight"] == 70.5


def test_execute_query_health_dashboard(db):
    svc = HealthService(db)
    executor = ToolExecutor(None, svc, None, None, None)
    result = executor.execute("query_health", {"query_type": "dashboard"})
    assert "weight" in result


def test_execute_manage_schedule_create(db):
    svc = ScheduleService(db)
    executor = ToolExecutor(None, None, svc, None, None)
    result = executor.execute("manage_schedule",
                              {"action": "create", "title": "晨会", "start_time": "2026-06-10 09:00"})
    assert result["title"] == "晨会"


def test_execute_manage_schedule_auto_query(db):
    svc = ScheduleService(db)
    svc.create_event("晨会", "2026-06-10 09:00")
    executor = ToolExecutor(None, None, svc, None, None)
    result = executor.execute("manage_schedule", {"action": "query"})
    assert len(result) == 1


def test_execute_manage_memo_create(db):
    svc = MemoService(db)
    executor = ToolExecutor(None, None, None, svc, None)
    result = executor.execute("manage_memo",
                              {"action": "create", "title": "笔记", "content": "内容"})
    assert result["title"] == "笔记"


def test_execute_manage_memo_search(db):
    svc = MemoService(db)
    svc.create_note("Python", "学习")
    executor = ToolExecutor(None, None, None, svc, None)
    result = executor.execute("manage_memo", {"action": "search", "keyword": "Python"})
    assert len(result) == 1


def test_execute_query_weather(db):
    fake_weather = FakeWeatherService()
    executor = ToolExecutor(None, None, None, None, fake_weather)
    result = executor.execute("query_weather", {"city": "北京", "type": "now"})
    assert result["city"] == "北京"
    assert result["temp"] == "25"


def test_execute_query_weather_forecast(db):
    fake_weather = FakeWeatherService()
    executor = ToolExecutor(None, None, None, None, fake_weather)
    result = executor.execute("query_weather", {"city": "北京", "type": "forecast", "days": 3})
    assert len(result) == 1


def test_execute_unknown_tool(db):
    executor = ToolExecutor(None, None, None, None, None)
    result = executor.execute("unknown_tool", {})
    assert "error" in result
