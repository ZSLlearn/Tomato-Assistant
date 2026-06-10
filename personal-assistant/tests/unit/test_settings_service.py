from app.modules.settings.service import SettingsService


def test_set_and_get(db):
    svc = SettingsService(db)
    svc.set("deepseek_api_key", "sk-test123")
    assert svc.get("deepseek_api_key") == "sk-test123"


def test_get_nonexistent_key(db):
    svc = SettingsService(db)
    assert svc.get("nonexistent") is None
    assert svc.get("nonexistent", "默认值") == "默认值"


def test_set_overwrite(db):
    svc = SettingsService(db)
    svc.set("key", "value1")
    svc.set("key", "value2")
    assert svc.get("key") == "value2"


def test_get_all(db):
    svc = SettingsService(db)
    svc.set("key1", "value1")
    svc.set("key2", "value2")
    all_config = svc.get_all()
    assert all_config["key1"] == "value1"
    assert all_config["key2"] == "value2"


def test_get_all_empty(db):
    svc = SettingsService(db)
    assert svc.get_all() == {}
