import pytest
from app.modules.memo.service import MemoService


def test_create_note(db):
    svc = MemoService(db)
    note = svc.create_note("读书笔记", "# 读后感", "学习", "读书,笔记")
    assert note["title"] == "读书笔记"
    assert note["content"] == "# 读后感"
    assert note["category"] == "学习"
    assert note["is_pinned"] == 0


def test_create_note_empty_title(db):
    svc = MemoService(db)
    with pytest.raises(ValueError, match="标题不能为空"):
        svc.create_note("")


def test_get_note(db):
    svc = MemoService(db)
    note = svc.create_note("笔记1", "内容")
    fetched = svc.get_note(note["id"])
    assert fetched["title"] == "笔记1"


def test_get_note_not_found(db):
    svc = MemoService(db)
    with pytest.raises(ValueError, match="笔记不存在"):
        svc.get_note(999)


def test_list_notes(db):
    svc = MemoService(db)
    svc.create_note("笔记1", "内容1", "工作")
    svc.create_note("笔记2", "内容2", "生活")
    assert len(svc.list_notes()) == 2


def test_list_notes_filter_category(db):
    svc = MemoService(db)
    svc.create_note("笔记1", "内容1", "工作")
    svc.create_note("笔记2", "内容2", "生活")
    recs = svc.list_notes(category="工作")
    assert len(recs) == 1


def test_list_notes_search(db):
    svc = MemoService(db)
    svc.create_note("Python学习", "Python测试框架")
    svc.create_note("Java入门", "Java基础语法")
    recs = svc.list_notes(keyword="Python")
    assert len(recs) == 1


def test_list_notes_search_content(db):
    svc = MemoService(db)
    svc.create_note("标题", "包含关键词的内容")
    svc.create_note("其他", "其他内容")
    recs = svc.search("关键词")
    assert len(recs) == 1


def test_update_note(db):
    svc = MemoService(db)
    note = svc.create_note("标题", "内容")
    updated = svc.update_note(note["id"], title="新标题", content="新内容")
    assert updated["title"] == "新标题"
    assert updated["content"] == "新内容"


def test_update_note_not_found(db):
    svc = MemoService(db)
    with pytest.raises(ValueError, match="笔记不存在"):
        svc.update_note(999, title="test")


def test_toggle_pin(db):
    svc = MemoService(db)
    note = svc.create_note("标题")
    pinned = svc.toggle_pin(note["id"])
    assert pinned["is_pinned"] == 1
    unpinned = svc.toggle_pin(note["id"])
    assert unpinned["is_pinned"] == 0


def test_delete_note(db):
    svc = MemoService(db)
    note = svc.create_note("标题")
    assert svc.delete_note(note["id"]) is True
    assert svc.list_notes() == []


def test_search_returns_all_results(db):
    svc = MemoService(db)
    svc.create_note("Python学习", "Python测试")
    svc.create_note("Python进阶", "高级Python")
    recs = svc.search("Python")
    assert len(recs) == 2
