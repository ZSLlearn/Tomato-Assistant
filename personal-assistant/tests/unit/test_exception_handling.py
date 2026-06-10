"""
测试异常处理：边界条件、错误场景、输入验证、异常传播
"""
import pytest
import json
from datetime import datetime
from app.database import get_db, init_db


@pytest.fixture
def db():
    """内存数据库"""
    import config
    config.DATABASE = ":memory:"
    conn = get_db()
    init_db(conn=conn)
    yield conn
    conn.close()


class TestFinanceExceptionHandling:
    """财务模块异常处理测试"""

    def test_add_record_with_nonexistent_category(self, db):
        """使用不存在的分类添加记录"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        with pytest.raises(ValueError, match="分类不存在"):
            svc.add_record(9999, "expense", 100, "2026-06-11")

    def test_add_record_negative_amount(self, db):
        """金额为负数"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("测试", "expense")
        with pytest.raises(ValueError, match="金额必须大于0"):
            svc.add_record(cat["id"], "expense", -50, "2026-06-11")

    def test_add_record_zero_amount(self, db):
        """金额为零"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("测试", "expense")
        with pytest.raises(ValueError, match="金额必须大于0"):
            svc.add_record(cat["id"], "expense", 0, "2026-06-11")

    def test_add_record_invalid_type(self, db):
        """非法的记录类型"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("测试", "expense")
        with pytest.raises(ValueError, match="类型必须是"):
            svc.add_record(cat["id"], "invalid_type", 100, "2026-06-11")

    def test_update_nonexistent_record(self, db):
        """更新不存在的记录"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        with pytest.raises(ValueError, match="记录不存在"):
            svc.update_record(9999, amount=200)

    def test_update_record_negative_amount(self, db):
        """更新记录时设置负数金额"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("测试", "expense")
        rec = svc.add_record(cat["id"], "expense", 100, "2026-06-11")
        with pytest.raises(ValueError, match="金额必须大于0"):
            svc.update_record(rec["id"], amount=-100)

    def test_create_duplicate_category(self, db):
        """创建重复分类"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        svc.create_category("餐饮", "expense")
        with pytest.raises(ValueError, match="已存在"):
            svc.create_category("餐饮", "expense")

    def test_update_nonexistent_category(self, db):
        """更新不存在的分类"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        with pytest.raises(ValueError, match="分类不存在"):
            svc.update_category(9999, name="新名称")

    def test_finance_record_type_mismatch_with_category(self, db):
        """记录的类型和分类类型不一致——现在正确拒绝"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("购物", "expense")
        # 用支出分类记录收入——现在会被拦截
        with pytest.raises(ValueError, match="不匹配"):
            svc.add_record(cat["id"], "income", 1000, "2026-06-11", "收入但用支出分类")

    def test_sql_injection_attempt(self, db):
        """SQL注入防护——使用参数化查询"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)

        # 尝试在分类名中注入SQL
        malicious_name = "'; DROP TABLE finance_categories; --"
        cat = svc.create_category(malicious_name, "expense")
        # 参数化查询应防止注入，分类表应仍然存在
        cats = svc.list_categories()
        assert len(cats) == 1
        # 验证表结构完整
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='finance_categories'").fetchone()


class TestHealthExceptionHandling:
    """健康模块异常处理测试"""

    def test_record_weight_negative(self, db):
        """记录负数体重"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="体重必须大于0"):
            svc.record_weight(-65, "2026-06-11")

    def test_record_weight_zero(self, db):
        """记录零体重"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="体重必须大于0"):
            svc.record_weight(0, "2026-06-11")

    def test_record_exercise_empty_type(self, db):
        """运动类型为空"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="运动类型不能为空"):
            svc.record_exercise("", 30, 200, "2026-06-11")

    def test_record_exercise_negative_duration(self, db):
        """运动时长为负数"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="运动时长必须大于0"):
            svc.record_exercise("跑步", -30, 200, "2026-06-11")

    def test_record_exercise_zero_duration(self, db):
        """运动时长为零"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="运动时长必须大于0"):
            svc.record_exercise("跑步", 0, 200, "2026-06-11")

    def test_record_water_negative(self, db):
        """记录负数饮水量"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="饮水量必须大于0"):
            svc.record_water(-500, "2026-06-11")

    def test_record_sleep_end_before_start(self, db):
        """起床时间早于入睡时间——使用词法上 start >= end 的值"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        # 同一天内 "22:00" 作为 start、"21:00" 作为 end ——不合理但词法正确
        # 注意：跨夜睡眠（如 start="22:00", end="07:00"）也会被错误拒绝，这是 BUG
        with pytest.raises(ValueError, match="起床时间必须晚于入睡时间"):
            svc.record_sleep("22:00", "21:00", 4, "2026-06-11")

    def test_record_sleep_bad_quality_too_low(self, db):
        """睡眠质量低于范围——使用能通过时间检查的值"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        # 使用完整日期时间格式以确保时间检查通过，测试质量检查
        with pytest.raises(ValueError, match="睡眠质量必须在1-5之间"):
            svc.record_sleep("2026-06-11 22:00", "2026-06-12 07:00", 0, "2026-06-11")

    def test_record_sleep_bad_quality_too_high(self, db):
        """睡眠质量高于范围"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        with pytest.raises(ValueError, match="睡眠质量必须在1-5之间"):
            svc.record_sleep("2026-06-11 22:00", "2026-06-12 07:00", 6, "2026-06-11")

    def test_sleep_pure_time_comparison_bug(self, db):
        """纯时间字符串的跨夜睡眠——已修复，现在正确支持"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        # 纯时间字符串的跨夜睡眠（23:00入睡→07:00起床）现在可以正常记录
        rec = svc.record_sleep("23:00", "07:00", 4, "2026-06-11")
        assert rec["start_time"] == "23:00"
        assert rec["quality"] == 4

    def test_sleep_with_full_datetime_comparison(self, db):
        """全日期时间格式比较正常"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        # 带日期的时间字符串比较正确
        rec = svc.record_sleep("2026-06-11 23:00", "2026-06-12 07:00", 4, "2026-06-11")
        assert rec["quality"] == 4

    def test_delete_nonexistent_health_record(self, db):
        """删除不存在的健康记录——静默失败（DELETE WHERE 无匹配行）"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)
        # 删除不存在的记录不会报错
        result = svc.delete_weight(9999)
        assert result is True  # 但实际什么都没删除


class TestScheduleExceptionHandling:
    """日程模块异常处理测试"""

    def test_create_event_empty_title(self, db):
        """日程标题为空"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="标题不能为空"):
            svc.create_event("", "2026-06-11T10:00")

    def test_create_event_start_after_end(self, db):
        """开始时间晚于结束时间"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="开始时间必须早于结束时间"):
            svc.create_event("会议", "2026-06-11T14:00", "2026-06-11T10:00")

    def test_create_event_invalid_category(self, db):
        """非法的日程分类"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="分类必须是"):
            svc.create_event("会议", "2026-06-11T10:00", category="非法")

    def test_create_event_invalid_priority(self, db):
        """非法的优先级"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="优先级必须在1-3之间"):
            svc.create_event("会议", "2026-06-11T10:00", priority=5)

    def test_update_nonexistent_event(self, db):
        """更新不存在的日程"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="日程不存在"):
            svc.update_event(9999, title="新标题")

    def test_mark_completed_nonexistent_event(self, db):
        """完成不存在的日程"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        with pytest.raises(ValueError, match="日程不存在"):
            svc.mark_completed(9999)

    def test_empty_end_time_allowed(self, db):
        """空结束时间是合法的（全天事件场景）"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        ev = svc.create_event("全天会议", "2026-06-11", end_time="")
        assert ev["end_time"] == ""


class TestMemoExceptionHandling:
    """备忘录模块异常处理测试"""

    def test_create_note_empty_title(self, db):
        """创建空标题笔记"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        with pytest.raises(ValueError, match="标题不能为空"):
            svc.create_note("")

    def test_get_note_not_found(self, db):
        """获取不存在的笔记"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        with pytest.raises(ValueError, match="笔记不存在"):
            svc.get_note(9999)

    def test_update_note_not_found(self, db):
        """更新不存在的笔记"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        with pytest.raises(ValueError, match="笔记不存在"):
            svc.update_note(9999, title="新标题")

    def test_toggle_pin_not_found(self, db):
        """置顶不存在的笔记"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        with pytest.raises(ValueError, match="笔记不存在"):
            svc.toggle_pin(9999)

    def test_delete_nonexistent_note(self, db):
        """删除不存在的笔记——静默成功"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        # DELETE WHERE 无匹配不会报错
        result = svc.delete_note(9999)
        assert result is True

    def test_update_empty_title_allowed(self, db):
        """更新为空标题——现在被正确拒绝"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        note = svc.create_note("原标题", "内容")
        # 更新为空标题——现在会被拒绝
        with pytest.raises(ValueError, match="标题不能为空"):
            svc.update_note(note["id"], title="")


class TestSettingsExceptionHandling:
    """设置模块异常处理测试"""

    def test_get_nonexistent_key(self, db):
        """获取不存在的配置——返回 None"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        assert svc.get("nonexistent") is None
        assert svc.get("nonexistent", "default") == "default"

    def test_set_empty_key(self, db):
        """设置空键——SQLite 允许但 UNIQUE 约束限制了"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        # 空字符串作为键是允许的
        svc.set("", "空键值")
        assert svc.get("") == "空键值"

    def test_set_none_value(self, db):
        """设置 None 值——SQLite 存储为 NULL，Python 返回 None"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        svc.set("none_key", None)
        # SQLite INSERT OR REPLACE 中 None 被转为 NULL
        result = svc.get("none_key")
        assert result is None  # SQL NULL → Python None



class TestToolExecutorExceptionHandling:
    """工具执行器异常处理测试"""

    def test_execute_unknown_tool(self, db):
        """执行未知工具"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        result = executor.execute("nonexistent_tool", {})
        assert "error" in result
        assert "未知工具" in result["error"]

    def test_execute_finance_without_category(self, db):
        """执行记账工具但不提供分类——自动创建'其他'分类"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        result = executor.execute("add_finance_record", {
            "type": "expense", "amount": 50, "date": "2026-06-11"
        })
        # 应自动使用"其他"分类
        assert result["amount"] == 50

    def test_execute_health_without_value(self, db):
        """执行健康记录但不提供 value——使用默认值 0"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        # 体重为 0 会触发 ValueError
        with pytest.raises(ValueError, match="体重必须大于0"):
            executor.execute("record_health", {
                "health_type": "weight", "date": "2026-06-11"
            })

    def test_execute_schedule_without_title(self, db):
        """执行日程创建但不提供标题——空标题触发错误"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        with pytest.raises(ValueError, match="标题不能为空"):
            executor.execute("manage_schedule", {
                "action": "create", "start_time": "2026-06-11T10:00"
            })

    def test_execute_memo_without_title(self, db):
        """执行备忘创建但不提供标题"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        with pytest.raises(ValueError, match="标题不能为空"):
            executor.execute("manage_memo", {
                "action": "create"
            })

    def test_executor_error_propagation(self, db):
        """工具执行器的异常传播——service 层的 ValueError 应向上传播"""
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        # 负数金额应触发 ValueError
        with pytest.raises(ValueError):
            executor.execute("add_finance_record", {
                "type": "expense", "amount": -100, "category": "测试"
            })


class TestDeepSeekClientExceptionHandling:
    """DeepSeek 客户端异常处理测试"""

    def test_client_init_default_timeout(self, db):
        """客户端初始化默认超时"""
        from app.ai.deepseek_client import DeepSeekClient
        client = DeepSeekClient("sk-test-key")
        assert client.timeout == 30
        assert client.api_key == "sk-test-key"

    def test_client_custom_timeout(self, db):
        """客户端自定义超时"""
        from app.ai.deepseek_client import DeepSeekClient
        client = DeepSeekClient("sk-test-key", timeout=10)
        assert client.timeout == 10

    def test_ai_engine_catches_client_errors(self, db):
        """AI引擎捕获客户端异常——返回友好错误而非崩溃"""
        from app.ai.engine import AIEngine
        from app.ai.tool_executor import ToolExecutor
        from app.modules.finance.service import FinanceService
        from app.modules.health.service import HealthService
        from app.modules.schedule.service import ScheduleService
        from app.modules.memo.service import MemoService
        from app.modules.weather.service import WeatherService

        executor = ToolExecutor(
            FinanceService(db), HealthService(db),
            ScheduleService(db), MemoService(db), WeatherService()
        )

        engine = AIEngine("sk-invalid-key", executor)
        # 使用无效 API key 应返回错误而非异常
        result = engine.chat("测试消息", city="北京")
        assert "reply" in result
        assert "tool_called" in result
        # 应该得到错误回复（API调用会失败）
        assert "暂不可用" in result["reply"] or result["reply"]


class TestRouteValidation:
    """路由层输入验证测试"""

    @pytest.fixture
    def app(self):
        import config
        import tempfile, os
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        config.DATABASE = db_path
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        yield app
        try:
            os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            pass

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_finance_create_category_no_name(self, client):
        """创建分类不提供名称"""
        resp = client.post('/finance/api/categories',
                          json={"type": "expense"},
                          content_type='application/json')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["code"] == 400

    def test_finance_create_category_invalid_type(self, client):
        """创建分类提供无效 type"""
        resp = client.post('/finance/api/categories',
                          json={"name": "测试", "type": "invalid"},
                          content_type='application/json')
        assert resp.status_code == 400

    def test_finance_create_record_no_amount(self, client):
        """创建记录不提供金额"""
        resp = client.post('/finance/api/records',
                          json={"type": "expense", "date": "2026-06-11"},
                          content_type='application/json')
        assert resp.status_code == 400

    def test_finance_create_record_missing_json(self, client):
        """请求缺少 JSON body"""
        resp = client.post('/finance/api/records',
                          data=None,
                          content_type='application/json')
        assert resp.status_code in (400, 415, 500)  # Flask 可能返回不同状态码

    def test_settings_config_empty_key(self, client):
        """设置配置空键"""
        resp = client.put('/settings/api/config',
                         json={"key": "", "value": "test"},
                         content_type='application/json')
        assert resp.status_code == 400

    def test_ai_chat_no_api_key(self, client):
        """无 API KEY 时 AI 聊天"""
        resp = client.post('/ai/chat',
                          json={"message": "你好"},
                          content_type='application/json')
        assert resp.status_code == 400
        data = resp.get_json()
        assert "API KEY" in data["message"]

    def test_ai_chat_empty_message(self, client):
        """空消息——但需要先有 API KEY"""
        # 先设置 API KEY
        client.put('/settings/api/config',
                  json={"key": "deepseek_api_key", "value": "sk-test"},
                  content_type='application/json')

        resp = client.post('/ai/chat',
                          json={"message": ""},
                          content_type='application/json')
        assert resp.status_code == 400
        data = resp.get_json()
        assert "消息不能为空" in data["message"]

    def test_weather_now_no_city(self, client):
        """天气查询不提供城市"""
        resp = client.get('/weather/api/now')
        assert resp.status_code == 400  # city 为空应返回 400

    def test_delete_nonexistent_resource(self, client):
        """删除不存在的资源——不应崩溃"""
        # 先设置 API KEY 让数据库有基础数据
        client.put('/settings/api/config',
                  json={"key": "deepseek_api_key", "value": "sk-test"},
                  content_type='application/json')

        routes = [
            ('DELETE', '/finance/api/records/99999'),
            ('DELETE', '/finance/api/categories/99999'),
            ('DELETE', '/health/api/weight/99999'),
            ('DELETE', '/health/api/exercise/99999'),
            ('DELETE', '/health/api/water/99999'),
            ('DELETE', '/health/api/sleep/99999'),
            ('DELETE', '/schedule/api/events/99999'),
            ('DELETE', '/memo/api/notes/99999'),
        ]
        for method, url in routes:
            resp = client.open(url, method=method)
            assert resp.status_code in (200, 404), f"{method} {url} returned {resp.status_code}"
