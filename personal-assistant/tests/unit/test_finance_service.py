import pytest
from app.modules.finance.service import FinanceService


def test_create_category(db):
    svc = FinanceService(db)
    result = svc.create_category("餐饮", "expense", "🍔")
    assert result["name"] == "餐饮"
    assert result["type"] == "expense"
    assert result["icon"] == "🍔"


def test_list_categories_empty(db):
    svc = FinanceService(db)
    assert svc.list_categories() == []


def test_list_categories_filtered(db):
    svc = FinanceService(db)
    svc.create_category("工资", "income")
    svc.create_category("餐饮", "expense")
    income_cats = svc.list_categories(type="income")
    assert len(income_cats) == 1
    assert income_cats[0]["name"] == "工资"


def test_create_duplicate_category(db):
    svc = FinanceService(db)
    svc.create_category("餐饮", "expense")
    with pytest.raises(ValueError, match="已存在"):
        svc.create_category("餐饮", "income")


def test_update_category(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    updated = svc.update_category(cat["id"], name="美食", icon="🍽")
    assert updated["name"] == "美食"


def test_update_nonexistent_category(db):
    svc = FinanceService(db)
    with pytest.raises(ValueError, match="不存在"):
        svc.update_category(999, name="test")


def test_delete_category(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    assert svc.delete_category(cat["id"]) is True
    assert svc.list_categories() == []


def test_add_record(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    rec = svc.add_record(cat["id"], "expense", 30.0, "2026-06-10", "午饭")
    assert rec["amount"] == 30.0
    assert rec["note"] == "午饭"


def test_add_record_negative_amount(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    with pytest.raises(ValueError, match="金额必须大于0"):
        svc.add_record(cat["id"], "expense", -5, "2026-06-10")


def test_add_record_zero_amount(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    with pytest.raises(ValueError, match="金额必须大于0"):
        svc.add_record(cat["id"], "expense", 0, "2026-06-10")


def test_add_record_nonexistent_category(db):
    svc = FinanceService(db)
    with pytest.raises(ValueError, match="分类不存在"):
        svc.add_record(999, "expense", 30, "2026-06-10")


def test_list_records(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    svc.add_record(cat["id"], "expense", 30, "2026-06-10", "午饭")
    svc.add_record(cat["id"], "expense", 50, "2026-06-09", "晚饭")
    recs = svc.list_records()
    assert len(recs) == 2


def test_list_records_filter_date(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    svc.add_record(cat["id"], "expense", 30, "2026-06-10")
    svc.add_record(cat["id"], "expense", 50, "2026-06-05")
    recs = svc.list_records(date_from="2026-06-08")
    assert len(recs) == 1
    assert recs[0]["date"] == "2026-06-10"


def test_update_record(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    rec = svc.add_record(cat["id"], "expense", 30, "2026-06-10")
    updated = svc.update_record(rec["id"], amount=45.0)
    assert updated["amount"] == 45.0


def test_delete_record(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    rec = svc.add_record(cat["id"], "expense", 30, "2026-06-10")
    assert svc.delete_record(rec["id"]) is True
    assert svc.list_records() == []


def test_get_monthly_summary(db):
    svc = FinanceService(db)
    cat_income = svc.create_category("工资", "income")
    cat_expense = svc.create_category("餐饮", "expense")
    svc.add_record(cat_income["id"], "income", 5000, "2026-06-10")
    svc.add_record(cat_expense["id"], "expense", 200, "2026-06-10")
    summary = svc.get_monthly_summary(2026, 6)
    assert summary["total_income"] == 5000
    assert summary["total_expense"] == 200
    assert summary["balance"] == 4800
    assert len(summary["by_category"]) >= 1


def test_get_monthly_summary_empty(db):
    svc = FinanceService(db)
    summary = svc.get_monthly_summary(2026, 6)
    assert summary["total_income"] == 0
    assert summary["total_expense"] == 0
    assert summary["balance"] == 0


def test_get_trend(db):
    svc = FinanceService(db)
    cat_income = svc.create_category("工资", "income")
    cat_expense = svc.create_category("餐饮", "expense")
    svc.add_record(cat_income["id"], "income", 5000, "2026-06-10")
    svc.add_record(cat_expense["id"], "expense", 200, "2026-06-10")
    svc.add_record(cat_expense["id"], "expense", 100, "2026-06-10")
    trend = svc.get_trend(2026, 6)
    assert len(trend) >= 1
    day = trend[0]
    assert day["income"] == 5000
    assert day["expense"] == 300


def test_add_record_invalid_type(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    with pytest.raises(ValueError, match="类型必须是"):
        svc.add_record(cat["id"], "invalid", 30, "2026-06-10")
