# 个人助手程序 — 产品需求文档 (PRD)

> **版本**: v1.0
> **日期**: 2026-06-10
> **状态**: 设计已确认，待实施

---

## 目录

1. [产品概述](#1-产品概述)
2. [技术选型](#2-技术选型)
3. [总体架构](#3-总体架构)
4. [项目结构](#4-项目结构)
5. [数据库设计](#5-数据库设计)
6. [功能模块详细设计](#6-功能模块详细设计)
7. [AI 助手设计](#7-ai-助手设计)
8. [前端设计](#8-前端设计)
9. [接口路由设计](#9-接口路由设计)
10. [非功能性需求](#10-非功能性需求)

---

## 1. 产品概述

### 1.1 产品定位

个人助手程序是一款轻量级 Web 应用，帮助用户管理日常生活中的记账、健康、日程、备忘录和天气查询五大场景，并内置 AI 对话助手，通过自然语言交互操作各模块功能。

### 1.2 目标用户

- 需要集中管理个人日常事务的用户
- 对数据隐私敏感、希望数据100%本地存储的用户
- 本项目同时作为"软件质量保证与测试"课程的测试对象

### 1.3 核心功能一览

| 模块          | 核心功能                          | 细分功能                                                   |
| ------------- | --------------------------------- | ---------------------------------------------------------- |
| 💰 收支记账   | 记录收入/支出，分类管理，统计分析 | 添加/编辑/删除账单，自定义分类，月度统计，收支趋势         |
| ❤️ 健康管理 | 多维度健康数据记录与看板          | 体重记录与趋势，运动记录，饮水记录，睡眠记录，数据统计     |
| 📅 日程安排   | 日程 CRUD，多视图，提醒           | 日/周/月视图，分类（工作/个人/紧急），优先级，即将到来提醒 |
| 📝 备忘录笔记 | 笔记管理，搜索                    | 创建/编辑/删除，Markdown，分类标签，置顶，全文搜索         |
| 🌤️ 天气查询 | 实时天气，预报，生活指数          | 当前天气，7天预报，城市搜索，穿衣/紫外线等指数             |
| 🤖 AI 助手    | 自然语言操作各模块                | 用户配置 DeepSeek API KEY，对话式增删查改，半自动模式      |

### 1.4 设计原则

- **高内聚低耦合**: 5 个功能模块互不依赖，各自独立，仅 AI 引擎可跨模块调用
- **可测试性优先**: Service 层纯 Python 逻辑，剥离 Web 框架依赖，方便白盒/黑盒测试
- **简单部署**: 单进程 Python 应用，SQLite 零配置数据库，`python run.py` 即可启动
- **数据所有权**: 用户数据 100% 本地 SQLite 存储，不上传任何第三方

---

## 2. 技术选型

| 层级               | 技术                            | 版本  | 选型理由                                 |
| ------------------ | ------------------------------- | ----- | ---------------------------------------- |
| **后端框架** | Flask                           | 3.x   | 轻量、同步模型利于测试、内置 test_client |
| **数据库**   | SQLite                          | 3.x   | 零配置、文件级存储、测试可切内存库       |
| **前端**     | Jinja2 + 原生 JS + 原生 CSS     | —    | 无构建工具链，极简，匹配"简单程序"定位   |
| **图表**     | Chart.js (CDN)                  | 4.x   | 轻量，仅用于健康趋势和财务图表           |
| **AI 服务**  | DeepSeek API (Chat Completions) | v1    | 用户自行配置 API KEY                     |
| **天气服务** | Open-Meteo API                  | —     | 完全免费，无需注册/API KEY，全球天气数据  |
| **语言**     | Python                          | 3.11+ | AI/API 调用生态最佳                      |

---

## 3. 总体架构

### 3.1 分层架构图

```
┌─────────────────────────────────────────────────┐
│                   前端层 (Templates)              │
│   Jinja2 模板 + 原生 JS + CSS  (每个模块独立目录)  │
├─────────────────────────────────────────────────┤
│                   路由层 (Routes)                 │
│   5 个 Blueprint + 1 个 AI Blueprint             │
│   每个 Blueprint 只做：参数校验 → 调 Service → 响应 │
├─────────────────────────────────────────────────┤
│                  业务逻辑层 (Service)              │
│   5 个 Service 模块 + AI 引擎                     │
│   纯 Python 类/函数，不依赖 Flask                  │
│   ← 白盒测试主战场                                │
├─────────────────────────────────────────────────┤
│                   数据层 (Models)                 │
│   SQLite + 原生 SQL 或 SQLAlchemy ORM             │
│   每个模块定义自己的表                             │
├─────────────────────────────────────────────────┤
│                   外部依赖                        │
│   DeepSeek API  ·  Open-Meteo API                   │
│   各自封装独立 Client 类，可 Mock                  │
└─────────────────────────────────────────────────┘
```

### 3.2 模块依赖规则

```
finance ←─┐
health ←──┤
schedule ←┼── AI 引擎（唯一调用者，其他模块互不调用）
memo ←────┤
weather ←┘
```

- ✅ 每个模块独立运行，不 import 其他模块的 Service
- ✅ AI 引擎通过 `tool_executor.py` 统一调用各模块 Service
- ❌ 模块间禁止互相引用，保证低耦合
- ❌ Service 层不依赖 Flask（不 import `request`、`session` 等）

---

## 4. 项目结构

```
personal-assistant/
├── run.py                       # 启动入口
├── config.py                    # 集中配置
├── requirements.txt             # Flask, requests, pytest, coverage 等
│
├── app/
│   ├── __init__.py              # Flask 工厂函数 create_app()
│   ├── database.py              # SQLite 初始化 + 表创建
│   │
│   ├── modules/                 # 5 个功能模块 — 每个互不依赖
│   │   ├── finance/             # 收支记账
│   │   │   ├── __init__.py      # Blueprint('finance', __name__, url_prefix='/finance')
│   │   │   ├── routes.py        # /finance/* 路由
│   │   │   ├── service.py       # 记账业务逻辑
│   │   │   └── models.py        # 财务表定义
│   │   ├── health/              # 健康管理（结构同上）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   ├── schedule/            # 日程安排（结构同上）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   ├── memo/                # 备忘录笔记（结构同上）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   ├── weather/             # 天气查询（结构同上）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── service.py
│   │   │   └── hefeng_client.py # Open-Meteo API 封装
│   │   └── settings/            # 系统设置
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── service.py
│   │
│   ├── ai/                      # AI 助手模块
│   │   ├── __init__.py          # Blueprint('ai', __name__, url_prefix='/ai')
│   │   ├── routes.py            # /ai/chat 对话端点
│   │   ├── engine.py            # AI 对话引擎
│   │   ├── deepseek_client.py   # DeepSeek API 封装
│   │   ├── intent_parser.py     # 意图识别与参数提取
│   │   └── tool_executor.py     # 操作执行器（调各模块 Service）
│   │
│   ├── templates/               # 前端模板
│   │   ├── base.html            # 公共布局（导航栏、侧边栏 AI 面板）
│   │   ├── index.html           # 首页仪表盘
│   │   ├── finance/             # 记账模块页面
│   │   ├── health/              # 健康模块页面
│   │   ├── schedule/            # 日程模块页面
│   │   ├── memo/                # 备忘录模块页面
│   │   ├── weather/             # 天气模块页面
│   │   └── settings/            # 设置页面
│   │
│   └── static/                  # 静态资源
│       ├── css/
│       │   └── style.css         # 全局样式
│       └── js/
│           ├── common.js        # 公共工具函数
│           ├── ai-chat.js       # AI 对话面板逻辑
│           ├── finance.js       # 记账模块交互
│           ├── health.js        # 健康模块交互
│           ├── schedule.js      # 日程模块交互
│           ├── memo.js          # 备忘录模块交互
│           └── weather.js       # 天气模块交互
│
└── tests/                       # 测试目录（由学生自行设计）
    ├── conftest.py              # pytest 夹具
    ├── unit/                    # 白盒测试
    ├── integration/             # 集成测试
    └── system/                  # 系统测试
```

---

## 5. 数据库设计

### 5.1 设计原则

- 每个模块独立的表，无跨模块外键关联
- 所有表使用自增 `id` 作主键
- 时间字段统一用 ISO 8601 字符串存储（SQLite 无原生 datetime 类型）
- 软删除（`is_deleted`）代替物理删除

### 5.2 收支记账表

**分类表 `finance_categories`**

| 字段       | 类型    | 约束                                          | 说明                         |
| ---------- | ------- | --------------------------------------------- | ---------------------------- |
| id         | INTEGER | PK, AUTOINCREMENT                             | 主键                         |
| name       | TEXT    | NOT NULL                                      | 分类名（餐饮、交通、工资…） |
| type       | TEXT    | NOT NULL, CHECK(type IN ('income','expense')) | 收入/支出                    |
| icon       | TEXT    | DEFAULT ''                                    | 图标 emoji                   |
| is_deleted | INTEGER | DEFAULT 0                                     | 软删除标记                   |

**账单表 `finance_records`**

| 字段        | 类型    | 约束                                          | 说明                           |
| ----------- | ------- | --------------------------------------------- | ------------------------------ |
| id          | INTEGER | PK, AUTOINCREMENT                             | 主键                           |
| category_id | INTEGER | NOT NULL                                      | 关联 `finance_categories.id` |
| type        | TEXT    | NOT NULL, CHECK(type IN ('income','expense')) | 收入/支出                      |
| amount      | REAL    | NOT NULL, CHECK(amount > 0)                   | 金额                           |
| date        | TEXT    | NOT NULL                                      | 日期 "YYYY-MM-DD"              |
| note        | TEXT    | DEFAULT ''                                    | 备注                           |
| created_at  | TEXT    | NOT NULL                                      | 创建时间戳                     |
| is_deleted  | INTEGER | DEFAULT 0                                     | 软删除标记                     |

### 5.3 健康管理表

**体重记录表 `health_weight`**

| 字段   | 类型    | 约束                        | 说明         |
| ------ | ------- | --------------------------- | ------------ |
| id     | INTEGER | PK, AUTOINCREMENT           | 主键         |
| weight | REAL    | NOT NULL, CHECK(weight > 0) | 体重 kg      |
| date   | TEXT    | NOT NULL                    | "YYYY-MM-DD" |
| note   | TEXT    | DEFAULT ''                  | 备注         |

**运动记录表 `health_exercise`**

| 字段     | 类型    | 约束                            | 说明         |
| -------- | ------- | ------------------------------- | ------------ |
| id       | INTEGER | PK, AUTOINCREMENT               | 主键         |
| type     | TEXT    | NOT NULL                        | 运动类型     |
| duration | INTEGER | NOT NULL, CHECK(duration > 0)   | 时长（分钟） |
| calories | REAL    | DEFAULT 0, CHECK(calories >= 0) | 消耗卡路里   |
| date     | TEXT    | NOT NULL                        | "YYYY-MM-DD" |
| note     | TEXT    | DEFAULT ''                      | 备注         |

**饮水记录表 `health_water`**

| 字段   | 类型    | 约束                        | 说明         |
| ------ | ------- | --------------------------- | ------------ |
| id     | INTEGER | PK, AUTOINCREMENT           | 主键         |
| amount | INTEGER | NOT NULL, CHECK(amount > 0) | 饮水量 ml    |
| date   | TEXT    | NOT NULL                    | "YYYY-MM-DD" |

**睡眠记录表 `health_sleep`**

| 字段       | 类型    | 约束                                      | 说明                        |
| ---------- | ------- | ----------------------------------------- | --------------------------- |
| id         | INTEGER | PK, AUTOINCREMENT                         | 主键                        |
| start_time | TEXT    | NOT NULL                                  | 入睡时间 "YYYY-MM-DD HH:MM" |
| end_time   | TEXT    | NOT NULL                                  | 起床时间 "YYYY-MM-DD HH:MM" |
| quality    | INTEGER | DEFAULT 3, CHECK(quality BETWEEN 1 AND 5) | 睡眠质量 1-5                |
| date       | TEXT    | NOT NULL                                  | 所属日期 "YYYY-MM-DD"       |

### 5.4 日程安排表

**`schedule_events`**

| 字段         | 类型    | 约束                                                      | 说明       |
| ------------ | ------- | --------------------------------------------------------- | ---------- |
| id           | INTEGER | PK, AUTOINCREMENT                                         | 主键       |
| title        | TEXT    | NOT NULL                                                  | 标题       |
| description  | TEXT    | DEFAULT ''                                                | 描述       |
| start_time   | TEXT    | NOT NULL                                                  | 开始时间   |
| end_time     | TEXT    | DEFAULT ''                                                | 结束时间   |
| category     | TEXT    | DEFAULT '个人', CHECK(category IN ('工作','个人','紧急')) | 分类       |
| priority     | INTEGER | DEFAULT 2, CHECK(priority BETWEEN 1 AND 3)                | 优先级     |
| is_completed | INTEGER | DEFAULT 0                                                 | 是否完成   |
| is_deleted   | INTEGER | DEFAULT 0                                                 | 软删除标记 |

### 5.5 备忘录笔记表

**`memo_notes`**

| 字段       | 类型    | 约束              | 说明                  |
| ---------- | ------- | ----------------- | --------------------- |
| id         | INTEGER | PK, AUTOINCREMENT | 主键                  |
| title      | TEXT    | NOT NULL          | 标题                  |
| content    | TEXT    | DEFAULT ''        | 内容（支持 Markdown） |
| category   | TEXT    | DEFAULT ''        | 分类标签              |
| tags       | TEXT    | DEFAULT ''        | 标签，逗号分隔        |
| is_pinned  | INTEGER | DEFAULT 0         | 是否置顶              |
| created_at | TEXT    | NOT NULL          | 创建时间戳            |
| updated_at | TEXT    | NOT NULL          | 最后修改时间戳        |

### 5.6 系统配置表

**`system_config`**

| 字段  | 类型    | 约束              | 说明   |
| ----- | ------- | ----------------- | ------ |
| id    | INTEGER | PK, AUTOINCREMENT | 主键   |
| key   | TEXT    | UNIQUE, NOT NULL  | 配置键 |
| value | TEXT    | DEFAULT ''        | 配置值 |

用途：存储 DeepSeek API KEY（用户配置）、默认城市等。

### 5.7 天气查询

无需建表，实时查询Open-Meteo API，不持久化。内存中缓存最近一次查询结果。

### 5.8 ER 概览

所有表模块间无关联，总计 11 张表。

```
finance_categories ←── finance_records (category_id)

health_weight    (独立)
health_exercise  (独立)
health_water     (独立)
health_sleep     (独立)

schedule_events  (独立)
memo_notes       (独立)
system_config    (独立)
```

---

## 6. 功能模块详细设计

### 6.1 收支记账 `FinanceService`

```python
class FinanceService:
    # === 分类管理 ===
    def create_category(name: str, type: str, icon: str = "") -> dict
    def list_categories(type: str = None) -> list[dict]
    def update_category(category_id: int, **kwargs) -> dict
    def delete_category(category_id: int) -> bool

    # === 账单 CRUD ===
    def add_record(category_id: int, type: str, amount: float,
                   date: str, note: str = "") -> dict
    def list_records(date_from: str = None, date_to: str = None,
                     category_id: int = None, type: str = None) -> list[dict]
    def update_record(record_id: int, **kwargs) -> dict
    def delete_record(record_id: int) -> bool

    # === 统计 ===
    def get_monthly_summary(year: int, month: int) -> dict
        # 返回: {"total_income": x, "total_expense": y, "balance": z,
        #         "by_category": [{name, amount, percent}, ...]}
    def get_trend(year: int, month: int) -> list[dict]
        # 返回: [{date, income, expense}, ...] 每日流水
```

### 6.2 健康管理 `HealthService`

```python
class HealthService:
    # === 体重 ===
    def record_weight(weight: float, date: str, note: str = "") -> dict
    def list_weight(date_from: str = None, date_to: str = None) -> list[dict]
    def get_weight_trend(days: int = 30) -> list[dict]
    def delete_weight(record_id: int) -> bool

    # === 运动 ===
    def record_exercise(type: str, duration: int, calories: float = 0,
                        date: str = "", note: str = "") -> dict
    def list_exercise(date_from: str = None, date_to: str = None) -> list[dict]
    def get_exercise_stats(days: int = 30) -> dict
        # 返回: {"total_count": n, "total_duration": m, "total_calories": c}
    def delete_exercise(record_id: int) -> bool

    # === 饮水 ===
    def record_water(amount: int, date: str) -> dict
    def list_water(date_from: str = None, date_to: str = None) -> list[dict]
    def get_daily_water(date: str) -> int
    def delete_water(record_id: int) -> bool

    # === 睡眠 ===
    def record_sleep(start_time: str, end_time: str,
                     quality: int = 3, date: str = "") -> dict
    def list_sleep(date_from: str = None, date_to: str = None) -> list[dict]
    def get_sleep_stats(days: int = 7) -> dict
        # 返回: {"avg_duration": h, "avg_quality": q, "trend": [...]}
    def delete_sleep(record_id: int) -> bool

    # === 看板 ===
    def get_dashboard() -> dict
        # 返回今日汇总: {weight, water_total, exercise_today, sleep_last}
```

### 6.3 日程安排 `ScheduleService`

```python
class ScheduleService:
    def create_event(title: str, start_time: str, end_time: str = "",
                     description: str = "", category: str = "个人",
                     priority: int = 2) -> dict
    def list_events(date_from: str = None, date_to: str = None,
                    category: str = None, is_completed: bool = None) -> list[dict]
    def get_events_by_date(date: str) -> list[dict]
    def get_events_by_week(date: str) -> dict
    def get_events_by_month(year: int, month: int) -> dict
    def update_event(event_id: int, **kwargs) -> dict
    def mark_completed(event_id: int) -> dict
    def delete_event(event_id: int) -> bool
    def get_upcoming_events(hours: int = 24) -> list[dict]
```

### 6.4 备忘录笔记 `MemoService`

```python
class MemoService:
    def create_note(title: str, content: str = "",
                    category: str = "", tags: str = "") -> dict
    def get_note(note_id: int) -> dict
    def list_notes(category: str = None, tag: str = None,
                   keyword: str = None, is_pinned: bool = None) -> list[dict]
    def update_note(note_id: int, **kwargs) -> dict
    def toggle_pin(note_id: int) -> dict
    def delete_note(note_id: int) -> bool
    def search(keyword: str) -> list[dict]
        # 全文搜索标题+内容，返回匹配项
```

### 6.5 天气查询 `WeatherService`

```python
class WeatherService:
    def __init__(self, api_key: str): ...
    def get_real_time(city: str) -> dict
        # 返回: {city, temp, feels_like, humidity, wind_dir, wind_speed,
        #         text, icon}
    def get_forecast(city: str, days: int = 7) -> list[dict]
        # 返回: [{date, temp_max, temp_min, text_day, text_night, humidity,
        #          wind_dir, wind_speed}, ...]
    def search_city(keyword: str) -> list[dict]
        # 返回: [{id, name, adm1, adm2, lat, lon}, ...]
    def get_life_index(city: str) -> dict
        # 返回: [{type, level, category}, ...]
```

### 6.6 系统设置 `SettingsService`

```python
class SettingsService:
    def get(key: str, default=None) -> str | None
    def set(key: str, value: str) -> None
    def test_deepseek_connection(api_key: str) -> bool
```

---

## 7. AI 助手设计

### 7.1 整体流程

```
用户输入 "帮我记一笔午饭 30 元"
        │
        ▼
┌──────────────────┐
│  DeepSeek API    │  发送对话 + 可用工具列表 (Function Calling)
│  (Chat Completions)│
└──────┬───────────┘
       │ 返回 tool_call JSON
       ▼
┌──────────────────┐
│  intent_parser   │  解析 DeepSeek 返回的工具调用
│  意图解析器       │  提取: {tool_name, parameters: {...}}
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  tool_executor   │  根据 tool_name 调用对应模块 Service
│  操作执行器       │  FinanceService().add_record(...)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  返回结果给用户   │  "已记录：午饭 餐饮 30.00 元 ✅"
└──────────────────┘
```

### 7.2 AI 工具定义（Function Calling）

| 工具名                 | 用途         | 关键参数                                                              |
| ---------------------- | ------------ | --------------------------------------------------------------------- |
| `add_finance_record` | 添加收支记录 | type, amount, category, date, note                                    |
| `query_finance`      | 查询收支     | query_type (recent/monthly_summary/by_category/trend), year, month    |
| `record_health`      | 记录健康数据 | health_type (weight/exercise/water/sleep), value, date                |
| `query_health`       | 查询健康数据 | query_type (dashboard/weight_trend/sleep_stats/exercise_stats)        |
| `manage_schedule`    | 管理日程     | action (create/query/update/complete/delete), title, start_time, date |
| `manage_memo`        | 管理备忘录   | action (create/query/search/update/delete), title, content, keyword   |
| `query_weather`      | 查询天气     | city, type (now/forecast/life_index), days                            |

### 7.3 AI 引擎核心

```python
class AIEngine:
    def __init__(self, api_key: str, tool_executor: ToolExecutor):
        self.client = DeepSeekClient(api_key)
        self.executor = tool_executor

    def chat(self, user_message: str,
             history: list[dict] = None) -> dict:
        """
        返回:
        {
            "reply": "AI 回复文本",
            "tool_called": "add_finance_record" | None,
            "tool_result": {...} | None
        }
        """
```

### 7.4 DeepSeek API 封装

```python
class DeepSeekClient:
    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, api_key: str, timeout: int = 30): ...
    def chat_completion(self, messages: list[dict],
                        tools: list[dict] = None,
                        model: str = "deepseek-chat") -> dict: ...
```

### 7.5 操作执行器

```python
class ToolExecutor:
    """
    依赖注入所有模块 Service，根据 tool_name 路由到对应方法。
    每个 tool_name 对应一个独立分支，方便白盒测试。
    """
    def __init__(self, finance_svc, health_svc, schedule_svc,
                 memo_svc, weather_svc): ...
    def execute(self, tool_name: str, params: dict) -> dict: ...
```

### 7.6 API KEY 配置分工

| API              | 配置者 | 存储位置                 | 说明                             |
| ---------------- | ------ | ------------------------ | -------------------------------- |
| DeepSeek API KEY | 用户   | SQLite `system_config` | 通过设置页面配置，存在本地数据库 |
| Open-Meteo       | 无需   | —                        | 完全免费，无需 API KEY           |

### 7.7 异常处理

| 场景                    | 处理方式                                                                      |
| ----------------------- | ----------------------------------------------------------------------------- |
| DeepSeek API KEY 未配置 | 返回提示"请先在设置中配置 DeepSeek API KEY"                                   |
| API 网络超时/错误       | 返回友好提示，不影响各模块手动使用                                            |
| API 余额不足 (402)      | 检测状态码，提示用户充值                                                      |
| AI 解析意图失败         | 降级为普通文本回复                                                            |
| 用户输入无关话题        | AI 礼貌拒绝："我是个人助手，只负责记账、健康、日程、备忘录和天气相关的事务。" |

---

## 8. 前端设计

### 8.1 整体布局

```
┌─────────────────────────────────────────────┐
│  ┌─────────────────────────────────────┐    │
│  │         顶部导航栏                    │    │
│  │  🏠首页 │ 💰记账 │ ❤️健康 │ 📅日程   │    │
│  │  📝备忘录 │ 🌤天气 │ ⚙️设置          │    │
│  └─────────────────────────────────────┘    │
│  ┌──────────┐  ┌──────────────────────────┐ │
│  │          │  │                          │ │
│  │  AI 助手 │  │     主内容区             │ │
│  │  对话面板 │  │  (各模块页面切换)        │ │
│  │ (320px)  │  │                          │ │
│  │ ┌──────┐ │  │                          │ │
│  │ │聊天区 │ │  │                          │ │
│  │ └──────┘ │  │                          │ │
│  │ ┌──────┐ │  │                          │ │
│  │ │输入框 │ │  │                          │ │
│  │ └──────┘ │  │                          │ │
│  └──────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 8.2 页面路由

| URL           | 页面       | 说明                           |
| ------------- | ---------- | ------------------------------ |
| `/`         | 首页仪表盘 | 今日概览卡片汇总               |
| `/finance`  | 收支记账   | 完整记账功能页面               |
| `/health`   | 健康管理   | 健康数据看板 + 记录            |
| `/schedule` | 日程安排   | 周视图（默认），Tab 切换日/月  |
| `/memo`     | 备忘录     | 左右分栏：列表 + 详情          |
| `/weather`  | 天气查询   | 实时天气 + 7天预报             |
| `/settings` | 系统设置   | API KEY 配置 + 偏好 + 数据管理 |

### 8.3 AI 对话面板

- 固定左侧 320px，始终可见
- 聊天消息展示（用户消息靠右，AI 回复靠左）
- 底部输入框 + 发送按钮
- AI 操作结果用卡片展示（如"✅ 已记录 30 元支出"）
- 未配置 API KEY 时显示配置引导链接

### 8.4 设置页面

```
┌─────────────────────────────────────────────────┐
│  ⚙️ 设置                                         │
│                                                  │
│  ┌─ AI 助手配置 ───────────────────────────────┐ │
│  │  DeepSeek API KEY                           │ │
│  │  ┌─────────────────────────────────────┐    │ │
│  │  │ sk-•••••••••••••••••••••••••  [👁] │    │ │
│  │  └─────────────────────────────────────┘    │ │
│  │  [🔗 如何获取？]  状态: ✅ 已连接 / ❌ 未配置 │ │
│  │  [测试连接]  [保存]                          │ │
│  └──────────────────────────────────────────────┘ │
│                                                  │
│  ┌─ 偏好设置 ──────────────────────────────────┐ │
│  │  默认城市  [北京 ___________] [🔍搜索]      │ │
│  └──────────────────────────────────────────────┘ │
│                                                  │
│  ┌─ 数据管理 ──────────────────────────────────┐ │
│  │  [📥 导出所有数据 (JSON)]                    │ │
│  │  [🗑 清空所有数据] (需二次确认)              │ │
│  └──────────────────────────────────────────────┘ │
│                                                  │
│  ┌─ 关于 ──────────────────────────────────────┐ │
│  │  个人助手 v1.0  | 天气: Open-Meteo | AI: DeepSeek │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 8.5 技术实现

| 层         | 技术                | 说明                                       |
| ---------- | ------------------- | ------------------------------------------ |
| 模板引擎   | Jinja2              | `{% extends "base.html" %}` 复用布局     |
| 样式       | 原生 CSS            | 单文件 `style.css`，CSS 变量做主题色     |
| 交互       | 原生 JS (Fetch API) | 每模块独立 JS 文件，`fetch()` 调后端路由 |
| 图表       | Chart.js (CDN)      | 仅用于体重趋势和财务月统计                 |
| AI 对话    | `ai-chat.js`      | `POST /ai/chat`，支持一次性/流式返回     |
| 浏览器通知 | Notification API    | 日程即将到来提醒                           |

---

## 9. 接口路由设计

### 9.1 统一响应格式

**成功响应：**

```json
{"code": 200, "message": "ok", "data": {...}}
```

**错误响应：**

```json
{"code": 400, "message": "金额必须大于 0", "data": null}
```

**HTTP 状态码规范：**

| 状态码 | 含义           | 示例场景                   |
| ------ | -------------- | -------------------------- |
| 200    | 成功           | 查询/更新成功              |
| 201    | 创建成功       | 新增记录                   |
| 400    | 参数校验失败   | 金额为空/格式错误          |
| 404    | 资源不存在     | 记录 id 不存在             |
| 422    | 业务逻辑错误   | 起床时间早于入睡时间       |
| 500    | 服务器内部错误 | 数据库异常                 |
| 503    | 外部服务不可用 | 天气 API/DeepSeek API 超时 |

### 9.2 收支记账 `/finance`

| 方法   | 路由                             | 说明                                                 |
| ------ | -------------------------------- | ---------------------------------------------------- |
| GET    | `/finance`                     | 记账页面 (HTML)                                      |
| GET    | `/finance/api/categories`      | 分类列表                                             |
| POST   | `/finance/api/categories`      | 新增分类                                             |
| PUT    | `/finance/api/categories/<id>` | 修改分类                                             |
| DELETE | `/finance/api/categories/<id>` | 删除分类                                             |
| GET    | `/finance/api/records`         | 账单列表 `?type=&date_from=&date_to=&category_id=` |
| POST   | `/finance/api/records`         | 新增账单                                             |
| PUT    | `/finance/api/records/<id>`    | 修改账单                                             |
| DELETE | `/finance/api/records/<id>`    | 删除账单                                             |
| GET    | `/finance/api/summary`         | 月统计 `?year=&month=`                             |
| GET    | `/finance/api/trend`           | 收支趋势 `?year=&month=`                           |

### 9.3 健康管理 `/health`

| 方法   | 路由                          | 说明                |
| ------ | ----------------------------- | ------------------- |
| GET    | `/health`                   | 健康页面 (HTML)     |
| GET    | `/health/api/dashboard`     | 今日看板            |
| POST   | `/health/api/weight`        | 记录体重            |
| GET    | `/health/api/weight`        | 体重列表 `?days=` |
| DELETE | `/health/api/weight/<id>`   | 删除体重记录        |
| POST   | `/health/api/exercise`      | 记录运动            |
| GET    | `/health/api/exercise`      | 运动列表 `?days=` |
| DELETE | `/health/api/exercise/<id>` | 删除运动记录        |
| POST   | `/health/api/water`         | 记录饮水            |
| GET    | `/health/api/water`         | 饮水列表 `?date=` |
| DELETE | `/health/api/water/<id>`    | 删除饮水记录        |
| POST   | `/health/api/sleep`         | 记录睡眠            |
| GET    | `/health/api/sleep`         | 睡眠列表 `?days=` |
| DELETE | `/health/api/sleep/<id>`    | 删除睡眠记录        |

### 9.4 日程安排 `/schedule`

| 方法   | 路由                                   | 说明                                |
| ------ | -------------------------------------- | ----------------------------------- |
| GET    | `/schedule`                          | 日程页面 (HTML)                     |
| GET    | `/schedule/api/events`               | 日程列表 `?date=&view=&category=` |
| POST   | `/schedule/api/events`               | 新建日程                            |
| PUT    | `/schedule/api/events/<id>`          | 修改日程                            |
| PUT    | `/schedule/api/events/<id>/complete` | 标记完成                            |
| DELETE | `/schedule/api/events/<id>`          | 删除日程                            |
| GET    | `/schedule/api/events/upcoming`      | 即将到来 `?hours=`                |

### 9.5 备忘录 `/memo`

| 方法   | 路由                         | 说明                                  |
| ------ | ---------------------------- | ------------------------------------- |
| GET    | `/memo`                    | 备忘录页面 (HTML)                     |
| GET    | `/memo/api/notes`          | 笔记列表 `?category=&tag=&keyword=` |
| GET    | `/memo/api/notes/<id>`     | 笔记详情                              |
| POST   | `/memo/api/notes`          | 新建笔记                              |
| PUT    | `/memo/api/notes/<id>`     | 修改笔记                              |
| PUT    | `/memo/api/notes/<id>/pin` | 切换置顶                              |
| DELETE | `/memo/api/notes/<id>`     | 删除笔记                              |

### 9.6 天气查询 `/weather`

| 方法 | 路由                        | 说明                      |
| ---- | --------------------------- | ------------------------- |
| GET  | `/weather`                | 天气页面 (HTML)           |
| GET  | `/weather/api/now`        | 实时天气 `?city=`       |
| GET  | `/weather/api/forecast`   | 天气预报 `?city=&days=` |
| GET  | `/weather/api/life-index` | 生活指数 `?city=`       |
| GET  | `/weather/api/search`     | 城市搜索 `?keyword=`    |

### 9.7 AI 助手 `/ai`

| 方法 | 路由                    | 说明                                             |
| ---- | ----------------------- | ------------------------------------------------ |
| POST | `/ai/chat`            | AI 对话 `{"message": "...", "history": [...]}` |
| POST | `/ai/test-connection` | 测试 DeepSeek 连接 `{"api_key": "..."}`        |

### 9.8 系统设置 `/settings`

| 方法 | 路由                     | 说明                                            |
| ---- | ------------------------ | ----------------------------------------------- |
| GET  | `/settings`            | 设置页面 (HTML)                                 |
| GET  | `/settings/api/config` | 获取所有配置                                    |
| PUT  | `/settings/api/config` | 保存指定配置 `{"key": "...", "value": "..."}` |

---

## 10. 非功能性需求

### 10.1 性能

- 页面首次加载时间 < 2 秒（本地运行，无 CDN 延迟）
- API 响应时间 < 500ms（本地 SQLite 查询）
- Chart.js 从 CDN 加载，不阻塞页面渲染（async 加载）

### 10.2 安全

- DeepSeek API KEY 存储在本地 SQLite，不经过任何第三方服务器
- 无天气 API KEY 需要保护（Open-Meteo 免费无需认证）
- 前端输入做基本 XSS 防护（Jinja2 默认转义）
- SQL 查询使用参数化，防止注入

### 10.3 可用性

- 设置页面提供 API KEY 获取指引链接
- 测试连接按钮即时验证 API KEY 有效性
- AI 对话失败不影响各模块手动操作
- 数据导出为 JSON 格式，可读、可备份

### 10.4 可维护性

- 每个功能模块 4 个文件（`__init__.py`, `routes.py`, `service.py`, `models.py`），结构统一
- Service 方法命名遵循 `verb_noun` 规范
- 路由方法遵循 RESTful 命名
- 所有外部 API 调用封装在独立 Client 类中，替换 API 服务商只需修改一个文件

### 10.5 部署

- 依赖：Python 3.11+，`pip install -r requirements.txt`
- 启动：`python run.py`，默认监听 `http://127.0.0.1:5000`
- 数据库：首次启动自动创建 SQLite 文件，无需手动建表
- 配置：用户启动后在设置页面填写 DeepSeek API KEY；天气无需额外配置

---

> **文档结束**
> 本文档覆盖了个人助手程序的完整产品需求，包括总体架构、数据库设计、5 个功能模块 + AI 助手的详细接口定义、前端设计、路由设计和非功能性需求。实施时以本文档为基准。
