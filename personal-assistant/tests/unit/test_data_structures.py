"""
测试数据结构：字段类型、完整性、边界条件、数据一致性
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


class TestFinanceDataStructure:
    """财务模块数据结构测试"""

    def test_category_required_fields(self, db):
        """分类表必填字段约束"""
        # name 和 type 是必填的
        with pytest.raises(Exception):
            db.execute("INSERT INTO finance_categories (name) VALUES ('测试')")
        with pytest.raises(Exception):
            db.execute("INSERT INTO finance_categories (type) VALUES ('expense')")

    def test_category_type_check_constraint(self, db):
        """分类 type 只能为 income 或 expense"""
        db.execute("INSERT INTO finance_categories (name, type) VALUES ('正常', 'income')")
        with pytest.raises(Exception):
            db.execute("INSERT INTO finance_categories (name, type) VALUES ('非法', 'invalid')")

    def test_record_amount_must_be_positive(self, db):
        """记录金额必须大于0"""
        db.execute("INSERT INTO finance_categories (name, type) VALUES ('餐费', 'expense')")
        cat_id = db.execute("SELECT id FROM finance_categories WHERE name='餐费'").fetchone()["id"]
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO finance_records (category_id, type, amount, date, created_at) VALUES (?, 'expense', -10, '2026-06-11', '2026-06-11T12:00')",
                (cat_id,))
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO finance_records (category_id, type, amount, date, created_at) VALUES (?, 'expense', 0, '2026-06-11', '2026-06-11T12:00')",
                (cat_id,))

    def test_record_type_check_constraint(self, db):
        """记录 type 只能为 income 或 expense"""
        db.execute("INSERT INTO finance_categories (name, type) VALUES ('测试', 'expense')")
        cat_id = db.execute("SELECT id FROM finance_categories WHERE name='测试'").fetchone()["id"]
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO finance_records (category_id, type, amount, date, created_at) VALUES (?, 'invalid', 100, '2026-06-11', '2026-06-11T12:00')",
                (cat_id,))

    def test_soft_delete_flag_is_integer(self, db):
        """is_deleted 是整数标志"""
        db.execute("INSERT INTO finance_categories (name, type, is_deleted) VALUES ('测试', 'expense', 0)")
        row = db.execute("SELECT is_deleted FROM finance_categories WHERE name='测试'").fetchone()
        assert row["is_deleted"] == 0
        assert isinstance(row["is_deleted"], int)

    def test_deleted_records_not_in_summary(self, db):
        """已删除记录不出现在统计中"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        # Create category and records
        cat = svc.create_category("测试", "expense")
        svc.add_record(cat["id"], "expense", 100.0, "2026-06-01", "有效")
        svc.add_record(cat["id"], "expense", 200.0, "2026-06-01", "待删除")
        # Delete second record
        recs = svc.list_records()
        to_delete = [r for r in recs if r["note"] == "待删除"][0]
        svc.delete_record(to_delete["id"])
        # Summary should only count non-deleted
        summary = svc.get_monthly_summary(2026, 6)
        assert summary["total_expense"] == 100.0

    def test_category_type_mismatch_with_record(self, db):
        """分类类型与记录类型一致——现在正确校验了"""
        from app.modules.finance.service import FinanceService
        svc = FinanceService(db)
        cat = svc.create_category("餐饮", "expense")
        # 用支出分类记录收入——应该被拒绝
        with pytest.raises(ValueError, match="不匹配"):
            svc.add_record(cat["id"], "income", 100, "2026-06-11", "收入但用了支出分类")
        # 正确的类型应成功
        rec = svc.add_record(cat["id"], "expense", 100, "2026-06-11", "正确的支出")
        assert rec["type"] == "expense"


class TestHealthDataStructure:
    """健康模块数据结构测试"""

    def test_weight_positive_constraint(self, db):
        """体重必须大于0"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_weight (weight, date) VALUES (-1, '2026-06-11')")
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_weight (weight, date) VALUES (0, '2026-06-11')")

    def test_exercise_duration_positive(self, db):
        """运动时长必须大于0"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_exercise (type, duration, date) VALUES ('跑步', 0, '2026-06-11')")

    def test_exercise_calories_non_negative(self, db):
        """消耗卡路里不能为负"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_exercise (type, duration, calories, date) VALUES ('跑步', 30, -1, '2026-06-11')")

    def test_exercise_type_not_null(self, db):
        """运动类型不能为空"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_exercise (duration, date) VALUES (30, '2026-06-11')")

    def test_water_amount_positive(self, db):
        """饮水量必须大于0"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_water (amount, date) VALUES (0, '2026-06-11')")

    def test_sleep_quality_range(self, db):
        """睡眠质量在1-5之间"""
        db.execute("INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES ('22:00','06:00',3,'2026-06-11')")
        db.execute("INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES ('22:00','06:00',1,'2026-06-10')")
        db.execute("INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES ('22:00','06:00',5,'2026-06-09')")
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES ('22:00','06:00',0,'2026-06-08')")
        with pytest.raises(Exception):
            db.execute("INSERT INTO health_sleep (start_time, end_time, quality, date) VALUES ('22:00','06:00',6,'2026-06-07')")

    def test_sleep_date_format_handling(self, db):
        """睡眠数据的日期格式处理——修复后支持多种格式"""
        from app.modules.health.service import HealthService
        svc = HealthService(db)

        # 纯时间字符串，跨夜睡眠（已修复：现在正确处理）
        rec = svc.record_sleep("22:00", "07:00", 4, "2026-06-11")
        assert rec["start_time"] == "22:00"
        assert rec["quality"] == 4

        # 带日期+时间，跨夜
        rec2 = svc.record_sleep("2026-06-11 22:00", "2026-06-12 07:00", 4, "2026-06-11")
        assert "2026" in rec2["start_time"]

        # ISO 格式
        rec3 = svc.record_sleep("2026-06-11T22:00", "2026-06-12T07:00", 4, "2026-06-11")
        assert rec3["quality"] == 4

        # 无效时间格式
        with pytest.raises(ValueError, match="起床时间必须晚于入睡时间"):
            svc.record_sleep("22:00", "21:00", 4, "2026-06-11")


class TestScheduleDataStructure:
    """日程模块数据结构测试"""

    def test_event_category_check(self, db):
        """日程分类只能是 工作/个人/紧急"""
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO schedule_events (title, start_time, category) VALUES ('测试', '2026-06-11T10:00', '无效')")

    def test_event_priority_range(self, db):
        """优先级必须在1-3之间"""
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO schedule_events (title, start_time, priority) VALUES ('测试', '2026-06-11T10:00', 0)")
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO schedule_events (title, start_time, priority) VALUES ('测试', '2026-06-11T10:00', 4)")

    def test_event_title_not_null(self, db):
        """日程标题不能为空"""
        with pytest.raises(Exception):
            db.execute("INSERT INTO schedule_events (start_time) VALUES ('2026-06-11T10:00')")

    def test_event_iso_format_start_time(self, db):
        """日程开始时间的ISO格式"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        # ISO datetime 格式
        ev = svc.create_event("会议", "2026-06-11T10:00", "2026-06-11T11:00")
        assert "T" in ev["start_time"]
        # 非ISO格式也能存储（SQLite 没有日期校验）
        ev2 = svc.create_event("午餐", "12:00", "13:00")
        assert ev2["start_time"] == "12:00"
        # 但比较 '12:00' >= '13:00' 在字符串比较中是 False（'1' == '1', '2' < '3'）
        # 而 '2026-06-11T12:00' >= '2026-06-11T13:00' 也是 False
        # 所以纯时间字符串的比较是碰巧正确的

    def test_event_end_time_can_be_empty(self, db):
        """结束时间可以为空"""
        from app.modules.schedule.service import ScheduleService
        svc = ScheduleService(db)
        ev = svc.create_event("全天事件", "2026-06-11", end_time="")
        assert ev["end_time"] == ""


class TestMemoDataStructure:
    """备忘录模块数据结构测试"""

    def test_note_created_at_updated_at(self, db):
        """笔记创建时间和更新时间自动设置"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        note = svc.create_note("测试笔记", "内容", "工作", "标签1,标签2")
        assert note["created_at"]  # 不应为空
        assert note["updated_at"]  # 不应为空
        assert note["created_at"] == note["updated_at"]  # 新创建时二者相等

    def test_note_updated_at_changes_on_update(self, db):
        """更新笔记时 updated_at 应变化"""
        from app.modules.memo.service import MemoService
        import time
        svc = MemoService(db)
        note = svc.create_note("测试", "内容")
        original_updated = note["updated_at"]
        time.sleep(0.1)
        updated = svc.update_note(note["id"], content="新内容")
        assert updated["updated_at"] != original_updated

    def test_note_title_required(self, db):
        """笔记标题必填"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        with pytest.raises(ValueError, match="标题不能为空"):
            svc.create_note("", "内容")

    def test_note_update_does_not_validate_title(self, db):
        """更新笔记时也校验标题——行为已一致"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        note = svc.create_note("测试", "内容")
        # 更新为空标题——现在会报错
        with pytest.raises(ValueError, match="标题不能为空"):
            svc.update_note(note["id"], title="")
        # 但保留现有标题的更新应成功
        updated = svc.update_note(note["id"], content="新内容")
        assert updated["content"] == "新内容"
        assert updated["title"] == "测试"

    def test_note_tags_format(self, db):
        """标签是逗号分隔字符串"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        note = svc.create_note("标签测试", tags="工作,重要,紧急")
        assert note["tags"] == "工作,重要,紧急"
        # 搜索标签
        results = svc.list_notes(tag="重要")
        assert len(results) == 1
        # 部分匹配
        results2 = svc.list_notes(tag="工")
        assert len(results2) == 1

    def test_note_is_pinned_default(self, db):
        """新笔记默认不置顶"""
        from app.modules.memo.service import MemoService
        svc = MemoService(db)
        note = svc.create_note("测试")
        assert note["is_pinned"] == 0


class TestAIDataStructure:
    """AI模块数据结构测试"""

    def test_message_role_check_constraint(self, db):
        """消息角色只能是 user/assistant/system"""
        now = datetime.now().isoformat()
        db.execute("INSERT INTO ai_conversations (created_at, updated_at) VALUES (?, ?)", (now, now))
        conv_id = db.execute("SELECT id FROM ai_conversations").fetchone()["id"]
        db.execute(
            "INSERT INTO ai_messages (conversation_id, role, content, created_at) VALUES (?, 'user', 'test', ?)",
            (conv_id, now))
        db.execute(
            "INSERT INTO ai_messages (conversation_id, role, content, created_at) VALUES (?, 'assistant', 'test', ?)",
            (conv_id, now))
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO ai_messages (conversation_id, role, content, created_at) VALUES (?, 'invalid', 'test', ?)",
                (conv_id, now))

    def test_conversation_cascade_delete(self, db):
        """删除对话时——消息表的外键级联行为"""
        now = datetime.now().isoformat()
        db.execute("INSERT INTO ai_conversations (created_at, updated_at) VALUES (?, ?)", (now, now))
        conv_id = db.execute("SELECT id FROM ai_conversations").fetchone()["id"]
        db.execute(
            "INSERT INTO ai_messages (conversation_id, role, content, created_at) VALUES (?, 'user', 'test', ?)",
            (conv_id, now))
        # 验证 foreign_keys 已启用
        fk_enabled = db.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk_enabled == 1, "foreign_keys 应为 ON"

        # 删除对话（外键级联应自动删除关联消息）
        # 注意：SQLite 外键需要表创建时定义 ON DELETE CASCADE，
        # 当前 schema 中 FOREIGN KEY 未指定 ON DELETE CASCADE，
        # 所以是 RESTRICT 模式——但这在 DELETE 时会阻止删除（如果还有子记录）
        # 实际代码通过先删消息再删对话来处理（ai/routes.py 第122-124行）
        # 所以这里测试实际行为
        msgs_before = db.execute("SELECT * FROM ai_messages WHERE conversation_id=?", (conv_id,)).fetchall()
        assert len(msgs_before) > 0  # 有消息

        # 手动级联删除（模拟 routes.py 的做法）
        db.execute("DELETE FROM ai_messages WHERE conversation_id=?", (conv_id,))
        db.execute("DELETE FROM ai_conversations WHERE id=?", (conv_id,))
        msgs_after = db.execute("SELECT * FROM ai_messages WHERE conversation_id=?", (conv_id,)).fetchall()
        assert len(msgs_after) == 0

    def test_tool_called_json_format(self, db):
        """工具调用数据的 JSON 存储"""
        now = datetime.now().isoformat()
        db.execute("INSERT INTO ai_conversations (created_at, updated_at) VALUES (?, ?)", (now, now))
        conv_id = db.execute("SELECT id FROM ai_conversations").fetchone()["id"]
        tool_called = json.dumps([{"id": "call_123", "function": {"name": "add_finance_record", "arguments": '{"amount":100}'}}], ensure_ascii=False)
        db.execute(
            "INSERT INTO ai_messages (conversation_id, role, content, tool_called, created_at) VALUES (?, 'assistant', '已记账', ?, ?)",
            (conv_id, tool_called, now))
        row = db.execute("SELECT tool_called FROM ai_messages WHERE conversation_id=?", (conv_id,)).fetchone()
        parsed = json.loads(row["tool_called"])
        assert isinstance(parsed, list)
        assert parsed[0]["function"]["name"] == "add_finance_record"


class TestSettingsDataStructure:
    """设置模块数据结构测试"""

    def test_key_unique(self, db):
        """配置键必须唯一"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        svc.set("test_key", "value1")
        svc.set("test_key", "value2")  # 应该覆盖
        assert svc.get("test_key") == "value2"

    def test_empty_value_allowed(self, db):
        """配置值可以为空字符串"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        svc.set("empty_key", "")
        assert svc.get("empty_key") == ""

    def test_get_nonexistent_with_default(self, db):
        """获取不存在的键返回默认值"""
        from app.modules.settings.service import SettingsService
        svc = SettingsService(db)
        assert svc.get("nonexistent", "default_val") == "default_val"
