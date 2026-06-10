# 个人助手程序 — 产品需求文档 (PRD)

> **版本**: v1.1
> **日期**: 2026-06-11
> **状态**: 已实施

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

| 模块 | 核心功能 | 细分功能 |
|------|---------|---------|
| 💰 收支记账 | 记录收入/支出，分类管理，统计分析 | 支出/收入切换、快捷金额、按类型筛选分类、月度统计、收支趋势 |
| ❤️ 健康管理 | 多维度健康数据记录与看板 | 体重趋势折线图、运动统计柱状图、饮水快捷记录、睡眠质量折线图、统计面板 |
| 📅 日程安排 | 日程 CRUD，多视图，提醒 | 快捷时长（+15min/+1h等）、分类（工作/个人/紧急）、优先级、完成/撤销 |
| 📝 备忘录笔记 | 笔记管理，搜索，自动保存 | 创建/编辑/删除、Markdown、分类标签、置顶、全文搜索、1.5秒自动保存 |
| 🌤️ 天气查询 | 实时天气，预报，生活指数 | 当前天气、7天预报、城市搜索、IP自动定位 |
| 🤖 AI 助手 | 多对话管理、自然语言操作各模块 | Function Calling、对话持久化、多对话切换/重命名/删除、城市感知、日期感知 |

### 1.4 设计原则

- **高内聚低耦合**: 5 个功能模块互不依赖，各自独立，仅 AI 引擎可跨模块调用
- **可测试性优先**: Service 层纯 Python 逻辑，剥离 Web 框架依赖，方便白盒/黑盒测试
- **简单部署**: 单进程 Python 应用，SQLite 零配置数据库，`python run.py` 即可启动
- **数据所有权**: 用户数据 100% 本地 SQLite 存储，不上传任何第三方

---

## 2. 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| **后端框架** | Flask | 3.x | 轻量、同步模型利于测试、内置 test_client |
| **数据库** | SQLite | 3.x | 零配置、文件级存储、测试可切内存库 |
| **前端** | Jinja2 + 原生 JS + 原生 CSS | — | 无构建工具链，极简，匹配"简单程序"定位 |
| **图表** | Chart.js (CDN) | 4.x | 体重/运动/饮水/睡眠趋势图、财务统计图 |
| **AI 服务** | DeepSeek API (Chat Completions) | v1 | 用户自行配置 API KEY，支持 Function Calling |
| **天气服务** | Open-Meteo API | — | 完全免费，无需注册/API KEY，全球天气数据 |
| **IP 定位** | ip-api.com | — | 免费，无需注册，45次/分钟，用于自动识别城市 |
| **语言** | Python | 3.11+ | AI/API 调用生态最佳 |

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
│   SQLite + 原生 SQL                               │
│   每个模块定义自己的表 + AI 对话/消息表             │
├─────────────────────────────────────────────────┤
│                   外部依赖                        │
│   DeepSeek API  ·  Open-Meteo  ·  ip-api.com     │
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
├── config.py                    # 集中配置（数据库路径等）
├── requirements.txt             # Flask, requests, pytest, pytest-cov
│
├── app/
│   ├── __init__.py              # Flask 工厂函数 create_app() + 首页路由
│   ├── database.py              # SQLite 初始化 + 12 张表创建
│   │
│   ├── modules/                 # 6 个功能模块 — 每个互不依赖
│   │   ├── finance/             # 收支记账
│   │   │   ├── __init__.py      # Blueprint('finance', __name__, url_prefix='/finance')
│   │   │   ├── routes.py        # /finance/* 路由（RESTful API）
│   │   │   ├── service.py       # 记账业务逻辑（分类校验、月度统计）
│   │   │   └── models.py        # 表结构文档
│   │   ├── health/              # 健康管理（结构同上）
│   │   ├── schedule/            # 日程安排（结构同上）
│   │   ├── memo/                # 备忘录笔记（结构同上）
│   │   ├── weather/             # 天气查询
│   │   │   ├── hefeng_client.py # Open-Meteo API 封装（WeatherClient）
│   │   │   ├── service.py       # 天气业务（缓存、WMO 天气码映射）
│   │   │   └── routes.py        # /weather/* 路由
│   │   └── settings/            # 系统设置
│   │       ├── service.py       # 配置读写
│   │       └── routes.py        # /settings/* 路由 + IP定位
│   │
│   ├── ai/                      # AI 助手模块
│   │   ├── __init__.py          # Blueprint('ai', __name__, url_prefix='/ai')
│   │   ├── routes.py            # 对话管理 + /ai/chat + /ai/conversations
│   │   ├── engine.py            # AI 引擎（系统提示词、日期注入、城市注入、回复格式化）
│   │   ├── deepseek_client.py   # DeepSeek API 封装
│   │   └── tool_executor.py     # 操作执行器（含分类自动创建）
│   │
│   ├── templates/               # 前端模板（Jinja2）
│   │   ├── base.html            # 公共布局（导航栏 + AI 对话面板 + 对话管理）
│   │   ├── index.html           # 首页仪表盘（多模块概览卡片）
│   │   ├── finance/             # 记账模块页面
│   │   ├── health/              # 健康模块页面（含图表区域）
│   │   ├── schedule/            # 日程模块页面
│   │   ├── memo/                # 备忘录模块页面
│   │   ├── weather/             # 天气模块页面
│   │   └── settings/            # 设置页面（API KEY + 城市定位 + 关于）
│   │
│   └── static/                  # 静态资源
│       ├── css/
│       │   └── style.css         # 全局样式（设计系统：Tokens + 布局 + 组件）
│       └── js/
│           ├── common.js        # 公共函数（api、toast、ai-refresh 全局监听）
│           ├── ai-chat.js       # AI 对话（多对话管理、消息渲染、typing动画）
│           ├── finance.js       # 记账交互（类型切换、快捷金额、回车提交）
│           ├── health.js        # 健康交互（Tab切换、Chart.js图表、统计面板）
│           ├── schedule.js      # 日程交互（时长快捷、自动结束时间）
│           ├── memo.js          # 备忘录交互（自动保存、置顶切换、搜索）
│           └── weather.js       # 天气交互（实时+预报、默认城市）
│
└── tests/                       # 测试目录（97 个测试用例）
    ├── conftest.py              # pytest 夹具（temp文件库 + 内存库）
    ├── unit/                    # 白盒测试（6 个文件）
    └── integration/             # 集成测试（1 个文件）
```

---

## 5. 数据库设计

### 5.1 设计原则

- 每个模块独立的表，无跨模块外键关联
- 所有表使用自增 `id` 作主键
- 时间字段统一用 ISO 8601 字符串存储（SQLite 无原生 datetime 类型）
- 软删除（`is_deleted`）代替物理删除（部分表）

### 5.2 收支记账表

**分类表 `finance_categories`**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| name | TEXT | NOT NULL | 分类名（餐饮、交通、工资…） |
| type | TEXT | NOT NULL, CHECK(type IN ('income','expense')) | 收入/支出 |
| icon | TEXT | DEFAULT '' | 图标 emoji |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |

**账单表 `finance_records`**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| category_id | INTEGER | NOT NULL | 关联 `finance_categories.id` |
| type | TEXT | NOT NULL, CHECK(type IN ('income','expense')) | 收入/支出 |
| amount | REAL | NOT NULL, CHECK(amount > 0) | 金额 |
| date | TEXT | NOT NULL | 日期 "YYYY-MM-DD" |
| note | TEXT | DEFAULT '' | 备注 |
| created_at | TEXT | NOT NULL | 创建时间戳 |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |

> **已实现校验**: Service 层校验分类 type 与记录 type 匹配，防止用收入分类记支出

### 5.3 健康管理表

**体重 `health_weight`**: id, weight(REAL>0), date, note
**运动 `health_exercise`**: id, type, duration(INT>0), calories(REAL>=0), date, note
**饮水 `health_water`**: id, amount(INT>0), date
**睡眠 `health_sleep`**: id, start_time, end_time, quality(INT 1-5), date

> **已实现校验**: 睡眠时间支持多种格式（HH:MM、YYYY-MM-DD HH:MM、ISO），智能判断跨夜睡眠

### 5.4 日程安排表

**`schedule_events`**: id, title, description, start_time, end_time, category(CHECK 工作/个人/紧急), priority(1-3), is_completed, is_deleted

### 5.5 备忘录笔记表

**`memo_notes`**: id, title(NOT NULL), content, category, tags, is_pinned, created_at, updated_at

> **已实现校验**: 更新时不允许空标题

### 5.6 系统配置表

**`system_config`**: id, key(UNIQUE), value —— 存储 DeepSeek API KEY、默认城市等

### 5.7 AI 对话表

**`ai_conversations`**: id, title(DEFAULT '新对话'), created_at, updated_at

**`ai_messages`**: id, conversation_id(FK), role(CHECK user/assistant/system), content, tool_called(JSON), tool_result(JSON), created_at

### 5.8 总计 13 张表

```
finance_categories ←── finance_records (category_id)

health_weight / health_exercise / health_water / health_sleep (独立)

schedule_events / memo_notes / system_config (独立)

ai_conversations ←── ai_messages (conversation_id)
```

---

## 6. 功能模块详细设计

### 6.1 收支记账 `FinanceService`

```python
class FinanceService:
    def create_category(name, type, icon="") -> dict
    def list_categories(type=None) -> list[dict]
    def update_category(category_id, **kwargs) -> dict
    def delete_category(category_id) -> bool

    def add_record(category_id, type, amount, date, note="") -> dict
        # 校验: amount>0, type in (income,expense), category存在且类型匹配
    def list_records(date_from=None, date_to=None, category_id=None, type=None) -> list[dict]
    def update_record(record_id, **kwargs) -> dict
    def delete_record(record_id) -> bool

    def get_monthly_summary(year, month) -> dict
        # 返回: {total_income, total_expense, balance, by_category: [{name, amount, percent}]}
    def get_trend(year, month) -> list[dict]
        # 返回: [{date, income, expense}]
```

**前端交互**: 支出/收入大按钮切换、¥10-500 快捷金额、按类型自动筛选分类、回车提交

### 6.2 健康管理 `HealthService`

```python
class HealthService:
    # 体重
    def record_weight(weight, date, note="") -> dict
    def list_weight(date_from=None, date_to=None) -> list[dict]
    def get_weight_trend(days=30) -> list[dict]
    def delete_weight(record_id) -> bool

    # 运动
    def record_exercise(type, duration, calories=0, date="", note="") -> dict
    def list_exercise(date_from=None, date_to=None) -> list[dict]
    def get_exercise_stats(days=30) -> dict
    def delete_exercise(record_id) -> bool

    # 饮水
    def record_water(amount, date) -> dict
    def list_water(date_from=None, date_to=None) -> list[dict]
    def get_daily_water(date) -> int
    def delete_water(record_id) -> bool

    # 睡眠
    def record_sleep(start_time, end_time, quality=3, date="") -> dict
        # 校验: quality 1-5, 智能判断跨夜睡眠合法性
    def list_sleep(date_from=None, date_to=None) -> list[dict]
    def get_sleep_stats(days=7) -> dict
    def delete_sleep(record_id) -> bool

    # 看板
    def get_dashboard() -> dict
```

**前端交互**: Tab 切换（体重/运动/饮水/睡眠）、Chart.js 趋势图、统计面板（平均/最高/最低/总计）、快捷值填充

### 6.3 日程安排 `ScheduleService`

```python
class ScheduleService:
    def create_event(title, start_time, end_time="", description="",
                     category="个人", priority=2) -> dict
    def list_events(date_from=None, date_to=None, category=None, is_completed=None) -> list[dict]
    def get_events_by_date(date) -> list[dict]
    def update_event(event_id, **kwargs) -> dict
    def mark_completed(event_id) -> dict    # 切换完成状态
    def delete_event(event_id) -> bool
    def get_upcoming_events(hours=24) -> list[dict]
```

**前端交互**: +15min/+30min/+1h/+2h 时长快捷按钮、自动设置结束时间、回车提交

### 6.4 备忘录笔记 `MemoService`

```python
class MemoService:
    def create_note(title, content="", category="", tags="") -> dict
    def get_note(note_id) -> dict
    def list_notes(category=None, tag=None, keyword=None, is_pinned=None) -> list[dict]
    def update_note(note_id, **kwargs) -> dict    # 自动更新 updated_at
    def toggle_pin(note_id) -> dict
    def delete_note(note_id) -> bool
    def search(keyword) -> list[dict]
```

**前端交互**: 新建笔记按钮、1.5秒自动保存（debounce）、置顶切换、搜索实时过滤、双击删除确认

### 6.5 天气查询 `WeatherService`

```python
class WeatherService:
    def __init__(): ...              # 无需 API KEY
    def search_city(keyword) -> list[dict]
    def get_real_time(city) -> dict  # {city, temp, feels_like, text, icon, humidity, wind_dir, wind_speed}
    def get_forecast(city, days=7) -> list[dict]
    def get_life_index(city) -> dict
```

**数据源**: Open-Meteo（免费，WMO 天气码映射为中文 + emoji）
**前端交互**: 自动加载默认城市、回车搜索、实时天气卡片 + 7天预报

### 6.6 系统设置 `SettingsService`

```python
class SettingsService:
    def get(key, default=None) -> str | None
    def set(key, value) -> None
    def get_all() -> dict
```

**设置页面功能**: DeepSeek API KEY 配置（显示/隐藏、测试连接）、默认城市（手动输入 + 📍 IP自动定位）、关于信息

---

## 7. AI 助手设计

### 7.1 整体流程

```
用户输入 "帮我记一笔午饭 30 元"
        │
        ▼
┌──────────────────┐
│  DeepSeek API    │  发送对话 + 可用工具列表 (Function Calling)
│  (Chat Completions)│  含: 系统提示词(日期+城市+规则)
└──────┬───────────┘
       │ 返回 tool_call JSON
       ▼
┌──────────────────┐
│  tool_executor   │  根据 tool_name 调用对应模块 Service
│  操作执行器       │  含 _resolve_category 自动创建/匹配分类
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  保存消息到 DB    │  用户消息 → 助手回复（含 tool_calls） → tool 结果
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  返回 + 触发刷新  │  AI 回复 + refresh 事件 → 前端自动更新对应模块
└──────────────────┘
```

### 7.2 AI 工具定义（Function Calling，7 个工具）

| 工具名 | 用途 | 关键参数 |
|--------|------|---------|
| `add_finance_record` | 添加收支记录 | type, amount, category, date, note |
| `query_finance` | 查询收支统计 | query_type, year, month |
| `record_health` | 记录健康数据 | health_type, value/duration/amount/start_time/end_time |
| `query_health` | 查询健康看板/趋势 | query_type, days |
| `manage_schedule` | 管理日程 | action(create/query/complete/delete), title, start_time |
| `manage_memo` | 管理备忘录 | action(create/query/search/delete), title, content, keyword |
| `query_weather` | 查询天气 | city, type(now/forecast/life_index) |

### 7.3 系统提示词增强

每次对话动态注入:
- **当前日期 + 星期**: "当前日期: 2026-06-11 (周三)"
- **参考日期**: 昨天、本周一、本月1日（辅助理解本周/本月）
- **默认城市**: 从设置读取，查天气时自动使用
- **强制规则**: 禁止凭空总结、连续重复请求每次都必须调用工具

### 7.4 对话管理

- **多对话**: 支持创建/切换/重命名/删除多个对话
- **持久化**: 对话和消息存 SQLite，刷新不丢失
- **历史回传**: 构建完整 tool_call 链（assistant tool_calls + tool result）回传给 DeepSeek
- **消息去重**: 构建历史时不包含当前消息，由 engine 追加，避免重复

### 7.5 数据刷新机制

AI 操作成功后返回 `refresh` 字段（finance/health/schedule/memo），前端 `common.js` 全局监听 `ai-refresh` 事件，自动调用对应模块的刷新函数。模块 JS 也有独立监听器。

### 7.6 API KEY 配置

| API | 配置者 | 存储 | 说明 |
|-----|--------|------|------|
| DeepSeek API KEY | 用户 | SQLite `system_config` | 设置页面配置，支持测试连接 |
| Open-Meteo | 无需 | — | 完全免费 |
| ip-api.com | 无需 | — | 完全免费，IP城市定位 |

---

## 8. 前端设计

### 8.1 整体布局

- **顶部导航栏**: SVG 图标 + 文字，当前页高亮
- **左侧 AI 面板** (312px): 对话选择器 + 重命名/删除按钮 + 消息区 + 输入框
- **右侧主内容区**: 各模块页面，独立渲染

### 8.2 页面路由

| URL | 页面 | 说明 |
|-----|------|------|
| `/` | 首页仪表盘 | 本月结余/体重/日程/笔记概览卡片 |
| `/finance` | 收支记账 | 类型切换 + 快捷金额 + 列表 |
| `/health` | 健康管理 | Tab + Chart.js 图表 + 统计面板 |
| `/schedule` | 日程安排 | 时长快捷 + 列表 |
| `/memo` | 备忘录 | 搜索 + 列表/详情左右分栏 + 自动保存 |
| `/weather` | 天气查询 | 搜索 + 实时天气卡片 + 7天预报 |
| `/settings` | 系统设置 | API KEY + 📍定位 + 偏好 |

### 8.3 AI 对话面板

- 对话选择器（下拉菜单）+ ✎重命名 + ✕删除 + ➕新建
- 消息渲染：用户消息（绿色靠右）、AI 回复（深色靠左）
- 工具标签：中文映射（💰 记账、📅 日程等）
- 消息格式化：金额高亮（金色）、温度高亮（蓝色）、Markdown **粗体**、换行
- 打字动画：三个跳动圆点
- 空状态：快捷指令标签（💰 记账、🏃 运动、📅 日程、🌤 天气）
- 回车发送、Shift+Enter 换行

### 8.4 设计系统 (CSS Tokens)

- 主色调：墨绿 `#3d7a5c`（accent）
- 背景：暖白 `#faf9f7`，卡片 `#ffffff`
- 文字：墨黑 `#1c1917`，辅助 `#78716c`
- AI 面板：深灰 `#1e1b1a`，气泡 `#3b3735`，文字 `#e8e5e3`
- 字体：标题 Noto Serif SC，正文 PingFang SC / Microsoft YaHei

---

## 9. 接口路由设计

### 9.1 统一响应格式

```json
{"code": 200, "message": "ok", "data": {...}}
{"code": 400, "message": "错误描述", "data": null}
```

### 9.2 收支记账 `/finance`

GET/POST `/api/categories`, PUT/DELETE `/api/categories/<id>`
GET/POST `/api/records`, PUT/DELETE `/api/records/<id>`
GET `/api/summary?year=&month=`, GET `/api/trend?year=&month=`

### 9.3 健康管理 `/health`

GET `/api/dashboard`
POST/GET `/api/weight|exercise|water|sleep`, DELETE `/<id>`
GET `/api/weight/trend?days=`, `/api/exercise/stats?days=`, `/api/sleep/stats?days=`

### 9.4 日程安排 `/schedule`

GET/POST `/api/events`, PUT/DELETE `/api/events/<id>`
PUT `/api/events/<id>/complete`, GET `/api/events/upcoming?hours=`

### 9.5 备忘录 `/memo`

GET/POST `/api/notes`, GET/PUT/DELETE `/api/notes/<id>`
PUT `/api/notes/<id>/pin`

### 9.6 天气查询 `/weather`

GET `/api/now?city=`, `/api/forecast?city=&days=`, `/api/life-index?city=`, `/api/search?keyword=`

### 9.7 AI 助手 `/ai`

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/ai/conversations` | 对话列表 |
| POST | `/ai/conversations` | 新建对话 |
| GET | `/ai/conversations/<id>` | 对话详情（含消息） |
| PUT | `/ai/conversations/<id>` | 重命名对话 |
| DELETE | `/ai/conversations/<id>` | 删除对话及消息 |
| POST | `/ai/chat` | 发送消息 `{message, conversation_id}` |
| POST | `/ai/test-connection` | 测试 DeepSeek 连接 |

### 9.8 系统设置 `/settings`

GET/PUT `/api/config`
GET `/api/detect-city` —— 通过 ip-api.com 根据客户端 IP 定位城市

---

## 10. 非功能性需求

### 10.1 性能

- 页面首次加载 < 2s（本地运行）
- API 响应 < 500ms（本地 SQLite）
- Chart.js CDN 异步加载

### 10.2 安全

- DeepSeek API KEY 存本地 SQLite，不经过第三方
- Jinja2 默认 XSS 转义
- SQL 参数化查询防注入
- 无天气/定位 API KEY 泄露风险

### 10.3 可用性

- 设置页 API KEY 测试连接即时验证
- AI 对话失败不影响手动操作
- IP 自动定位城市（设置页 📍 按钮）
- 空状态引导（首次使用提示）

### 10.4 可维护性

- 每模块 4 文件统一结构
- Service 方法遵循 `verb_noun` 命名
- RESTful 路由规范
- 外部 API 封装独立 Client 类
- 97 个测试用例，pytest 一键运行

### 10.5 部署

```bash
pip install -r requirements.txt
python run.py
# 访问 http://127.0.0.1:5000
# 设置页填写 DeepSeek API KEY 即可使用 AI
```

---

> **文档结束**
