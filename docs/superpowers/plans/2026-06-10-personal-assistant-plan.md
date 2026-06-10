# 个人助手程序 — 实施计划

> **目标**: 按 PRD 构建可测试的个人助手 Web 应用  
> **技术栈**: Flask 3.x + SQLite + 原生 HTML/JS/CSS + DeepSeek API + 和风天气 API  
> **方法**: TDD — 先写测试，再写实现

---

## 阶段 0：项目脚手架

### Task 0.1: 创建项目目录结构

```
personal-assistant/
├── run.py
├── config.py
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── modules/
│   │   ├── finance/    (__init__.py, routes.py, service.py, models.py)
│   │   ├── health/     (同上)
│   │   ├── schedule/   (同上)
│   │   ├── memo/       (同上)
│   │   ├── weather/    (同上 + hefeng_client.py)
│   │   └── settings/   (__init__.py, routes.py, service.py)
│   ├── ai/             (__init__.py, routes.py, engine.py, deepseek_client.py, tool_executor.py)
│   ├── templates/      (base.html, index.html + 6 模块子目录)
│   └── static/         (css/style.css, js/*.js)
└── tests/              (conftest.py, unit/, integration/)
```

### Task 0.2: 编写 requirements.txt

```
flask>=3.0
requests>=2.31
pytest>=8.0
pytest-cov>=5.0
```

### Task 0.3: 编写 config.py

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "data.db")
HEFENG_API_KEY = "你的和风天气KEY"   # 开发者填写
DEFAULT_CITY = "北京"
```

### Task 0.4: 编写 app/database.py

```python
import sqlite3
from config import DATABASE

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS finance_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            icon TEXT DEFAULT '',
            is_deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS finance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS health_weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL CHECK(weight > 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS health_exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            duration INTEGER NOT NULL CHECK(duration > 0),
            calories REAL DEFAULT 0 CHECK(calories >= 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS health_water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL CHECK(amount > 0),
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS health_sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            quality INTEGER DEFAULT 3 CHECK(quality BETWEEN 1 AND 5),
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS schedule_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            start_time TEXT NOT NULL,
            end_time TEXT DEFAULT '',
            category TEXT DEFAULT '个人' CHECK(category IN ('工作','个人','紧急')),
            priority INTEGER DEFAULT 2 CHECK(priority BETWEEN 1 AND 3),
            is_completed INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS memo_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            category TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            is_pinned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
```

### Task 0.5: 编写 app/__init__.py (Flask 工厂)

```python
from flask import Flask
from app.database import init_db

def create_app():
    app = Flask(__name__)
    init_db()

    from app.modules.finance import bp as finance_bp
    from app.modules.health import bp as health_bp
    from app.modules.schedule import bp as schedule_bp
    from app.modules.memo import bp as memo_bp
    from app.modules.weather import bp as weather_bp
    from app.modules.settings import bp as settings_bp
    from app.ai import bp as ai_bp

    app.register_blueprint(finance_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(memo_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(ai_bp)

    return app
```

### Task 0.6: 编写 run.py

```python
from app import create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
```

### Task 0.7: 编写 tests/conftest.py

```python
import pytest
from app import create_app
from app.database import get_db, init_db

@pytest.fixture
def app():
    import config
    config.DATABASE = ":memory:"       # 测试用内存库
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    conn = get_db()
    yield conn
    conn.close()
```

---

## 阶段 1：收支记账模块

每个文件按顺序：**测试 → 实现 → 验证**。

### Task 1.1: 编写 tests/unit/test_finance_service.py

```python
from app.modules.finance.service import FinanceService

def test_create_category(db):
    svc = FinanceService(db)
    result = svc.create_category("餐饮", "expense", "🍔")
    assert result["name"] == "餐饮"
    assert result["type"] == "expense"

def test_list_categories_empty(db):
    svc = FinanceService(db)
    assert svc.list_categories() == []

def test_create_category_duplicate_name(db):
    svc = FinanceService(db)
    svc.create_category("餐饮", "expense")
    try:
        svc.create_category("餐饮", "income")
        assert False, "Should raise"
    except ValueError:
        pass

def test_add_record(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    record = svc.add_record(cat["id"], "expense", 30.0, "2026-06-10", "午饭")
    assert record["amount"] == 30.0

def test_add_record_negative_amount(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    try:
        svc.add_record(cat["id"], "expense", -5, "2026-06-10")
        assert False
    except ValueError:
        pass

def test_add_record_zero_amount(db):
    svc = FinanceService(db)
    cat = svc.create_category("餐饮", "expense")
    try:
        svc.add_record(cat["id"], "expense", 0, "2026-06-10")
        assert False
    except ValueError:
        pass

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
```

### Task 1.2: 编写 app/modules/finance/service.py

```python
from datetime import datetime

class FinanceService:
    def __init__(self, db):
        self.db = db

    def create_category(self, name, type, icon=""):
        existing = self.db.execute(
            "SELECT id FROM finance_categories WHERE name=? AND is_deleted=0",
            (name,)
        ).fetchone()
        if existing:
            raise ValueError(f"分类 '{name}' 已存在")
        cur = self.db.execute(
            "INSERT INTO finance_categories (name, type, icon) VALUES (?, ?, ?)",
            (name, type, icon)
        )
        self.db.commit()
        return {"id": cur.lastrowid, "name": name, "type": type, "icon": icon}

    def list_categories(self, type=None):
        if type:
            rows = self.db.execute(
                "SELECT * FROM finance_categories WHERE type=? AND is_deleted=0",
                (type,)
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM finance_categories WHERE is_deleted=0"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_category(self, category_id, **kwargs):
        row = self.db.execute(
            "SELECT * FROM finance_categories WHERE id=? AND is_deleted=0",
            (category_id,)
        ).fetchone()
        if not row:
            raise ValueError("分类不存在")
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE finance_categories SET {sets} WHERE id=?",
            (*kwargs.values(), category_id)
        )
        self.db.commit()
        return self._get_category(category_id)

    def delete_category(self, category_id):
        self.db.execute(
            "UPDATE finance_categories SET is_deleted=1 WHERE id=?",
            (category_id,)
        )
        self.db.commit()
        return True

    def add_record(self, category_id, type, amount, date, note=""):
        if amount <= 0:
            raise ValueError("金额必须大于0")
        if type not in ("income", "expense"):
            raise ValueError("类型必须是 income 或 expense")
        cat = self.db.execute(
            "SELECT * FROM finance_categories WHERE id=? AND is_deleted=0",
            (category_id,)
        ).fetchone()
        if not cat:
            raise ValueError("分类不存在")
        created_at = datetime.now().isoformat()
        cur = self.db.execute(
            "INSERT INTO finance_records (category_id, type, amount, date, note, created_at) VALUES (?,?,?,?,?,?)",
            (category_id, type, amount, date, note, created_at)
        )
        self.db.commit()
        return {"id": cur.lastrowid, "category_id": category_id, "type": type,
                "amount": amount, "date": date, "note": note, "created_at": created_at}

    def list_records(self, date_from=None, date_to=None, category_id=None, type=None):
        sql = "SELECT r.*, c.name as category_name FROM finance_records r LEFT JOIN finance_categories c ON r.category_id=c.id WHERE r.is_deleted=0"
        params = []
        if date_from:
            sql += " AND r.date >= ?"; params.append(date_from)
        if date_to:
            sql += " AND r.date <= ?"; params.append(date_to)
        if category_id:
            sql += " AND r.category_id = ?"; params.append(category_id)
        if type:
            sql += " AND r.type = ?"; params.append(type)
        sql += " ORDER BY r.date DESC, r.created_at DESC"
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def update_record(self, record_id, **kwargs):
        row = self.db.execute(
            "SELECT * FROM finance_records WHERE id=? AND is_deleted=0",
            (record_id,)
        ).fetchone()
        if not row:
            raise ValueError("记录不存在")
        if "amount" in kwargs and kwargs["amount"] <= 0:
            raise ValueError("金额必须大于0")
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self.db.execute(
            f"UPDATE finance_records SET {sets} WHERE id=?",
            (*kwargs.values(), record_id)
        )
        self.db.commit()
        return self._get_record(record_id)

    def delete_record(self, record_id):
        self.db.execute(
            "UPDATE finance_records SET is_deleted=1 WHERE id=?", (record_id,)
        )
        self.db.commit()
        return True

    def get_monthly_summary(self, year, month):
        prefix = f"{year}-{month:02d}"
        income_row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM finance_records WHERE type='income' AND is_deleted=0 AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()
        expense_row = self.db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM finance_records WHERE type='expense' AND is_deleted=0 AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()
        cats = self.db.execute(
            "SELECT c.name, COALESCE(SUM(r.amount), 0) as amount FROM finance_categories c LEFT JOIN finance_records r ON c.id=r.category_id AND r.is_deleted=0 AND r.date LIKE ? WHERE c.is_deleted=0 AND c.type='expense' GROUP BY c.id",
            (f"{prefix}%",)
        ).fetchall()
        total_income = income_row["total"]
        total_expense = expense_row["total"]
        by_category = []
        for c in cats:
            pct = round(c["amount"] / total_expense * 100, 1) if total_expense > 0 else 0
            by_category.append({"name": c["name"], "amount": c["amount"], "percent": pct})
        return {
            "total_income": total_income, "total_expense": total_expense,
            "balance": total_income - total_expense, "by_category": by_category
        }

    def get_trend(self, year, month):
        prefix = f"{year}-{month:02d}"
        rows = self.db.execute(
            "SELECT date, type, SUM(amount) as total FROM finance_records WHERE is_deleted=0 AND date LIKE ? GROUP BY date, type ORDER BY date",
            (f"{prefix}%",)
        ).fetchall()
        result = {}
        for r in rows:
            if r["date"] not in result:
                result[r["date"]] = {"date": r["date"], "income": 0, "expense": 0}
            result[r["date"]][r["type"]] = r["total"]
        return list(result.values())

    def _get_category(self, cid):
        r = self.db.execute("SELECT * FROM finance_categories WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None

    def _get_record(self, rid):
        r = self.db.execute(
            "SELECT r.*, c.name as category_name FROM finance_records r LEFT JOIN finance_categories c ON r.category_id=c.id WHERE r.id=?",
            (rid,)
        ).fetchone()
        return dict(r) if r else None
```

### Task 1.3: 编写 app/modules/finance/routes.py

```python
from flask import Blueprint, request, jsonify, render_template
from app.database import get_db
from .service import FinanceService

bp = Blueprint('finance', __name__, url_prefix='/finance')

def _svc():
    return FinanceService(get_db())

@bp.route('/')
def page():
    return render_template('finance/index.html')

@bp.route('/api/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'GET':
        cats = _svc().list_categories(request.args.get('type'))
        return jsonify({"code": 200, "message": "ok", "data": cats})
    data = request.get_json()
    errors = _validate_category(data)
    if errors:
        return jsonify({"code": 400, "message": "; ".join(errors), "data": None}), 400
    try:
        cat = _svc().create_category(data['name'], data['type'], data.get('icon', ''))
        return jsonify({"code": 201, "message": "创建成功", "data": cat}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400

@bp.route('/api/categories/<int:cid>', methods=['PUT', 'DELETE'])
def category_detail(cid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            cat = _svc().update_category(cid, **data)
            return jsonify({"code": 200, "message": "ok", "data": cat})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    else:
        _svc().delete_category(cid)
        return jsonify({"code": 200, "message": "删除成功", "data": None})

@bp.route('/api/records', methods=['GET', 'POST'])
def records():
    if request.method == 'GET':
        records = _svc().list_records(
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
            category_id=request.args.get('category_id', type=int),
            type=request.args.get('type')
        )
        return jsonify({"code": 200, "message": "ok", "data": records})
    data = request.get_json()
    errors = _validate_record(data)
    if errors:
        return jsonify({"code": 400, "message": "; ".join(errors), "data": None}), 400
    try:
        record = _svc().add_record(**data)
        return jsonify({"code": 201, "message": "创建成功", "data": record}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400

@bp.route('/api/records/<int:rid>', methods=['PUT', 'DELETE'])
def record_detail(rid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            record = _svc().update_record(rid, **data)
            return jsonify({"code": 200, "message": "ok", "data": record})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    else:
        _svc().delete_record(rid)
        return jsonify({"code": 200, "message": "删除成功", "data": None})

@bp.route('/api/summary')
def summary():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_monthly_summary(year, month)})

@bp.route('/api/trend')
def trend():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_trend(year, month)})

def _validate_category(data):
    errs = []
    if not data.get('name'):
        errs.append("分类名不能为空")
    if data.get('type') not in ('income', 'expense'):
        errs.append("类型必须是 income 或 expense")
    return errs

def _validate_record(data):
    errs = []
    if data.get('type') not in ('income', 'expense'):
        errs.append("类型必须是 income 或 expense")
    if not data.get('amount') or data['amount'] <= 0:
        errs.append("金额必须大于0")
    if not data.get('date'):
        errs.append("日期不能为空")
    return errs
```

### Task 1.4: 编写 app/modules/finance/__init__.py 和 models.py

`__init__.py`:
```python
from .routes import bp
```

`models.py` — 仅文档，表定义在 database.py 中。

### Task 1.5: 编写 tests/integration/test_finance_routes.py

```python
def test_create_category_api(client):
    resp = client.post('/finance/api/categories',
        json={"name": "餐饮", "type": "expense"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "餐饮"

def test_create_category_no_name(client):
    resp = client.post('/finance/api/categories',
        json={"name": "", "type": "expense"})
    assert resp.status_code == 400

def test_add_record_api(client):
    client.post('/finance/api/categories', json={"name": "餐饮", "type": "expense"})
    resp = client.post('/finance/api/records',
        json={"category_id": 1, "type": "expense", "amount": 30, "date": "2026-06-10"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["amount"] == 30

def test_add_record_invalid_amount(client):
    resp = client.post('/finance/api/records',
        json={"category_id": 1, "type": "expense", "amount": -5, "date": "2026-06-10"})
    assert resp.status_code == 400

def test_monthly_summary_api(client):
    client.post('/finance/api/categories', json={"name": "工资", "type": "income"})
    client.post('/finance/api/categories', json={"name": "餐饮", "type": "expense"})
    client.post('/finance/api/records', json={"category_id": 1, "type": "income", "amount": 5000, "date": "2026-06-10"})
    client.post('/finance/api/records', json={"category_id": 2, "type": "expense", "amount": 200, "date": "2026-06-10"})
    resp = client.get('/finance/api/summary?year=2026&month=6')
    data = resp.get_json()["data"]
    assert data["balance"] == 4800
```

---

## 阶段 2：健康管理模块

结构与阶段 1 相同。按 PRD 第 6.2 节的接口实现 `HealthService`。

**关键点**：
- 4 个子模块（体重/运动/饮水/睡眠），每个有独立的 CRUD + 统计方法
- `get_dashboard()` 返回今日汇总
- `get_weight_trend()` 用最近 N 天数据
- `get_sleep_stats()` 计算平均时长和质量

**路由**：`/health/api/weight|exercise|water|sleep` + `/health/api/dashboard`

**测试重点**：
- 睡眠：起床时间 < 入睡时间 → 422
- 体重：负数 → 400
- 饮水：超大单次值（如 99999ml）→ 仍接受但可记录
- 看板：无数据时返回空值

---

## 阶段 3：日程安排模块

按 PRD 第 6.3 节接口实现 `ScheduleService`。

**关键点**：
- `get_events_by_date()` / `_by_week()` / `_by_month()` 三个视图
- `mark_completed()` 切换完成状态
- `get_upcoming_events(hours)` 未来 N 小时内日程

**路由**：`/schedule/api/events` + 子路由 `<int:id>` + `<int:id>/complete`

**测试重点**：
- 开始时间 > 结束时间 → 422
- 空标题 → 400
- 跨月周视图边界测试
- 重复标记完成 → 幂等

---

## 阶段 4：备忘录笔记模块

按 PRD 第 6.4 节接口实现 `MemoService`。

**关键点**：
- `search(keyword)` 全文搜索（SQLite `LIKE %keyword%`）
- `toggle_pin()` 切换置顶
- `updated_at` 每次修改自动更新

**路由**：`/memo/api/notes` + 子路由 `<int:id>` + `<int:id>/pin`

**测试重点**：
- 空标题 → 400
- 搜索中文/英文/特殊字符
- Markdown 内容存储和读取一致性

---

## 阶段 5：天气查询模块

### Task 5.1: 编写 app/modules/weather/hefeng_client.py

```python
import requests

class HefengClient:
    BASE = "https://devapi.qweather.com/v7"

    def __init__(self, api_key):
        self.api_key = api_key

    def search_city(self, keyword):
        resp = requests.get(f"{self.BASE}/city/lookup",
            params={"location": keyword, "key": self.api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [{"id": loc["id"], "name": loc["name"],
                 "adm1": loc.get("adm1",""), "adm2": loc.get("adm2",""),
                 "lat": loc["lat"], "lon": loc["lon"]}
                for loc in data.get("location", [])]

    def get_now(self, location_id):
        resp = requests.get(f"{self.BASE}/weather/now",
            params={"location": location_id, "key": self.api_key}, timeout=10)
        resp.raise_for_status()
        now = resp.json()["now"]
        return {"temp": now["temp"], "feels_like": now["feelsLike"],
                "text": now["text"], "icon": now["icon"],
                "humidity": now["humidity"], "wind_dir": now["windDir"],
                "wind_speed": now["windSpeed"]}

    def get_forecast(self, location_id, days=7):
        resp = requests.get(f"{self.BASE}/weather/{days}d",
            params={"location": location_id, "key": self.api_key}, timeout=10)
        resp.raise_for_status()
        return [{"date": d["fxDate"], "temp_max": d["tempMax"], "temp_min": d["tempMin"],
                 "text_day": d["textDay"], "text_night": d["textNight"],
                 "humidity": d["humidity"], "wind_dir": d["windDirDay"],
                 "wind_speed": d["windSpeedDay"]}
                for d in resp.json()["daily"]]

    def get_life_index(self, location_id):
        resp = requests.get(f"{self.BASE}/indices/1d",
            params={"location": location_id, "type": "1,2,3,5,8", "key": self.api_key}, timeout=10)
        resp.raise_for_status()
        return [{"type": d["name"], "level": d["category"], "text": d["text"]}
                for d in resp.json()["daily"]]
```

### Task 5.2: 编写 WeatherService + routes

- Service 封装 HefengClient，加缓存逻辑
- Routes: `/weather/api/now`, `/forecast`, `/life-index`, `/search`

---

## 阶段 6：系统设置模块

```python
class SettingsService:
    def __init__(self, db): self.db = db
    def get(self, key, default=None):
        r = self.db.execute("SELECT value FROM system_config WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default
    def set(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?,?)", (key, value))
        self.db.commit()
```

---

## 阶段 7：AI 助手模块

### Task 7.1: 编写 app/ai/deepseek_client.py

```python
import requests

class DeepSeekClient:
    BASE = "https://api.deepseek.com/v1"

    def __init__(self, api_key, timeout=30):
        self.api_key = api_key
        self.timeout = timeout

    def chat_completion(self, messages, tools=None, model="deepseek-chat"):
        payload = {"model": model, "messages": messages, "temperature": 0.7}
        if tools:
            payload["tools"] = tools
        resp = requests.post(f"{self.BASE}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
```

### Task 7.2: 编写 app/ai/tool_executor.py

```python
class ToolExecutor:
    def __init__(self, finance_svc, health_svc, schedule_svc, memo_svc, weather_svc):
        self.finance = finance_svc
        self.health = health_svc
        self.schedule = schedule_svc
        self.memo = memo_svc
        self.weather = weather_svc

    def execute(self, tool_name, params):
        if tool_name == "add_finance_record":
            return self.finance.add_record(
                params["category_id"], params["type"],
                params["amount"], params.get("date", ""), params.get("note", ""))
        if tool_name == "query_finance":
            qt = params["query_type"]
            if qt == "monthly_summary":
                return self.finance.get_monthly_summary(params["year"], params["month"])
            return self.finance.list_records()
        if tool_name == "record_health":
            ht = params["health_type"]
            if ht == "weight":
                return self.health.record_weight(params["value"], params.get("date", ""))
            if ht == "exercise":
                return self.health.record_exercise(params.get("type",""), params["duration"],
                    params.get("calories",0), params.get("date",""))
            if ht == "water":
                return self.health.record_water(params["amount"], params["date"])
            if ht == "sleep":
                return self.health.record_sleep(params["start_time"], params["end_time"],
                    params.get("quality",3), params.get("date",""))
        if tool_name == "query_health":
            qt = params["query_type"]
            if qt == "dashboard": return self.health.get_dashboard()
            if qt == "weight_trend": return self.health.get_weight_trend(params.get("days", 30))
            if qt == "sleep_stats": return self.health.get_sleep_stats(params.get("days", 7))
            if qt == "exercise_stats": return self.health.get_exercise_stats(params.get("days", 30))
        if tool_name == "manage_schedule":
            action = params["action"]
            if action == "create":
                return self.schedule.create_event(
                    params["title"], params.get("start_time",""),
                    params.get("end_time",""), params.get("description",""),
                    params.get("category","个人"), params.get("priority",2))
            if action == "query":
                return self.schedule.list_events(date_from=params.get("date"))
            if action == "complete":
                return self.schedule.mark_completed(params["event_id"])
            if action == "delete":
                return self.schedule.delete_event(params["event_id"])
        if tool_name == "manage_memo":
            action = params["action"]
            if action == "create":
                return self.memo.create_note(params["title"], params.get("content",""),
                    params.get("category",""), params.get("tags",""))
            if action == "search":
                return self.memo.search(params.get("keyword",""))
            if action == "query":
                return self.memo.list_notes()
        if tool_name == "query_weather":
            return self.weather.get_real_time(params["city"])
        return {"error": f"Unknown tool: {tool_name}"}
```

### Task 7.3: 编写 app/ai/engine.py

```python
import json
from .deepseek_client import DeepSeekClient

AI_TOOLS = [
    # 7 个工具定义（见 PRD 7.2 节）
]

SYSTEM_PROMPT = """你是个人助手，帮助管理记账、健康、日程、备忘录和天气查询。..."""

class AIEngine:
    def __init__(self, api_key, tool_executor):
        self.client = DeepSeekClient(api_key)
        self.executor = tool_executor

    def chat(self, user_message, history=None):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        try:
            resp = self.client.chat_completion(messages, tools=AI_TOOLS)
            choice = resp["choices"][0]
            msg = choice["message"]
            if "tool_calls" in msg and msg["tool_calls"]:
                tc = msg["tool_calls"][0]
                tool_name = tc["function"]["name"]
                params = json.loads(tc["function"]["arguments"])
                tool_result = self.executor.execute(tool_name, params)
                return {"reply": f"{tool_name} 执行成功", "tool_called": tool_name, "tool_result": tool_result}
            return {"reply": msg.get("content", ""), "tool_called": None, "tool_result": None}
        except Exception as e:
            return {"reply": f"AI 服务暂时不可用: {str(e)}", "tool_called": None, "tool_result": None}
```

### Task 7.4: 编写 app/ai/routes.py

```python
from flask import Blueprint, request, jsonify
from app.database import get_db
from app.ai.engine import AIEngine
from app.ai.tool_executor import ToolExecutor
from app.modules.finance.service import FinanceService
from app.modules.health.service import HealthService
from app.modules.schedule.service import ScheduleService
from app.modules.memo.service import MemoService
from app.modules.weather.service import WeatherService
from app.modules.settings.service import SettingsService
from config import HEFENG_API_KEY

bp = Blueprint('ai', __name__, url_prefix='/ai')

def _get_engine():
    db = get_db()
    settings = SettingsService(db)
    api_key = settings.get("deepseek_api_key")
    if not api_key:
        return None
    executor = ToolExecutor(
        FinanceService(db), HealthService(db), ScheduleService(db),
        MemoService(db), WeatherService(HEFENG_API_KEY)
    )
    return AIEngine(api_key, executor)

@bp.route('/chat', methods=['POST'])
def chat():
    engine = _get_engine()
    if not engine:
        return jsonify({"code": 400, "message": "请先在设置中配置 DeepSeek API KEY", "data": None}), 400
    data = request.get_json()
    result = engine.chat(data.get("message", ""), data.get("history"))
    return jsonify({"code": 200, "message": "ok", "data": result})

@bp.route('/test-connection', methods=['POST'])
def test_connection():
    from app.ai.deepseek_client import DeepSeekClient
    api_key = request.get_json().get("api_key", "")
    try:
        client = DeepSeekClient(api_key, timeout=10)
        client.chat_completion([{"role": "user", "content": "hi"}], model="deepseek-chat")
        return jsonify({"code": 200, "message": "连接成功", "data": {"ok": True}})
    except Exception as e:
        return jsonify({"code": 503, "message": str(e), "data": {"ok": False}})
```

---

## 阶段 8：前端模板与静态文件

### Task 8.1: 编写 app/templates/base.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}个人助手{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
</head>
<body>
    <nav class="navbar">
        <a href="/">🏠 首页</a>
        <a href="/finance">💰 记账</a>
        <a href="/health">❤️ 健康</a>
        <a href="/schedule">📅 日程</a>
        <a href="/memo">📝 备忘录</a>
        <a href="/weather">🌤 天气</a>
        <a href="/settings">⚙️ 设置</a>
    </nav>
    <div class="layout">
        <aside class="ai-panel" id="ai-panel">
            <!-- AI 对话面板 -->
            <div class="ai-messages" id="ai-messages"></div>
            <div class="ai-input">
                <input type="text" id="ai-input" placeholder="对我说点什么...">
                <button onclick="sendMessage()">发送</button>
            </div>
        </aside>
        <main class="content">
            {% block content %}{% endblock %}
        </main>
    </div>
    <script src="/static/js/common.js"></script>
    <script src="/static/js/ai-chat.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Task 8.2: 各模块页面模板（以记账为例）

`app/templates/finance/index.html`:
```html
{% extends "base.html" %}
{% block title %}收支记账{% endblock %}
{% block content %}
<h1>💰 收支记账</h1>
<div class="summary-cards" id="summary"></div>
<form id="record-form">
    <select id="type"><option value="expense">支出</option><option value="income">收入</option></select>
    <input type="number" id="amount" placeholder="金额" step="0.01" min="0.01">
    <select id="category_id"></select>
    <input type="date" id="date">
    <input type="text" id="note" placeholder="备注">
    <button type="submit">保存</button>
</form>
<table id="records-table"><thead><tr><th>日期</th><th>分类</th><th>金额</th><th>备注</th><th>操作</th></tr></thead><tbody></tbody></table>
{% endblock %}
{% block scripts %}<script src="/static/js/finance.js"></script>{% endblock %}
```

其他模块模板结构类似。

### Task 8.3: 编写核心 CSS 和 JS

**`static/css/style.css`** — 导航栏 + 侧边栏 AI 面板 + 主内容区布局，CSS 变量主题色，移动端响应式基础。

**`static/js/common.js`** — 封装 `api(url, method, body)` 通用请求函数。

**`static/js/ai-chat.js`** — AI 对话发送/渲染逻辑。

**`static/js/finance.js`** — 加载分类/账单、提交表单、渲染统计图表（Chart.js）。

健康/日程/备忘录/天气模块的 JS 文件结构与 finance 类似。

---

## 阶段 9：最终收尾

1. 确认所有 Blueprint 在 `app/__init__.py` 中注册
2. 运行 `pytest tests/ -v` 确保全部通过
3. 运行 `python run.py` 启动应用，手动验证各页面
4. 确认 `config.py` 中已填写和风天气 API KEY

---

## 执行顺序建议

| 阶段 | 内容 | 预估时间 |
|------|------|---------|
| 0 | 项目脚手架 | 30 min |
| 1 | 收支记账（含测试） | 60 min |
| 2 | 健康管理（含测试） | 45 min |
| 3 | 日程安排（含测试） | 40 min |
| 4 | 备忘录笔记（含测试） | 30 min |
| 5 | 天气查询（含测试） | 30 min |
| 6 | 系统设置 | 15 min |
| 7 | AI 助手 | 45 min |
| 8 | 前端模板与静态文件 | 60 min |
| 9 | 收尾集成 | 15 min |
| **总计** | | **~6 hours** |

> 开发完成后，自行设计白盒和黑盒测试用例，使用 `pytest-cov` 生成覆盖率报告。
