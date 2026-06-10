import json
from .deepseek_client import DeepSeekClient

AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_finance_record",
            "description": "记录一笔收入或支出",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["income", "expense"]},
                    "amount": {"type": "number", "description": "金额"},
                    "category": {"type": "string", "description": "分类名"},
                    "date": {"type": "string", "description": "日期 YYYY-MM-DD"},
                    "note": {"type": "string", "description": "备注"}
                },
                "required": ["type", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_finance",
            "description": "查询收支记录或统计",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {"type": "string",
                        "enum": ["recent", "monthly_summary", "by_category", "trend"]},
                    "year": {"type": "integer"}, "month": {"type": "integer"},
                    "days": {"type": "integer"}
                },
                "required": ["query_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_health",
            "description": "记录健康数据：体重(kg)、运动(分钟)、饮水(ml)、睡眠(起止时间)",
            "parameters": {
                "type": "object",
                "properties": {
                    "health_type": {"type": "string",
                        "enum": ["weight", "exercise", "water", "sleep"]},
                    "value": {"type": "number"}, "duration": {"type": "integer"},
                    "date": {"type": "string"}, "note": {"type": "string"},
                    "start_time": {"type": "string"}, "end_time": {"type": "string"},
                    "quality": {"type": "integer"}, "amount": {"type": "integer"},
                    "type": {"type": "string"}
                },
                "required": ["health_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_health",
            "description": "查询健康数据看板或统计",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {"type": "string",
                        "enum": ["dashboard", "weight_trend", "sleep_stats", "exercise_stats"]},
                    "days": {"type": "integer"}
                },
                "required": ["query_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_schedule",
            "description": "管理日程：创建、查询、完成、删除",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                        "enum": ["create", "query", "update", "complete", "delete"]},
                    "title": {"type": "string"}, "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "category": {"type": "string", "enum": ["工作", "个人", "紧急"]},
                    "date": {"type": "string"}, "event_id": {"type": "integer"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_memo",
            "description": "管理备忘录：创建、查询、搜索、删除笔记",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                        "enum": ["create", "query", "search", "update", "delete"]},
                    "title": {"type": "string"}, "content": {"type": "string"},
                    "keyword": {"type": "string"}, "note_id": {"type": "integer"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_weather",
            "description": "查询天气：实时天气、天气预报、生活指数",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "type": {"type": "string", "enum": ["now", "forecast", "life_index"]},
                    "days": {"type": "integer", "default": 7}
                },
                "required": ["city"]
            }
        }
    }
]

SYSTEM_PROMPT = """你是个人助手，帮助管理记账、健康、日程、备忘录和天气查询。

IMPORTANT RULES:
1. 用户说"收入X元"、"支出X元"、"花了X元"、"赚了X元"等——必须调用 add_finance_record，不要文字总结
2. 用户说"记录体重"、"运动"、"喝水"、"睡眠"——必须调用 record_health
3. 用户说"添加日程"、"安排"、"提醒我"——必须调用 manage_schedule
4. 用户说"记笔记"、"备忘录"、"写下来"——必须调用 manage_memo
5. 用户说"天气"、"多少度"——必须调用 query_weather
6. 用户说"查账"、"花了多少"、"收入多少"、"统计"——调用 query_finance
7. 禁止凭空总结——每次操作请求都必须调用工具执行，即使同样的请求连续出现多次
8. 执行完工具后，用简洁中文确认结果

可执行的操作：
- 记账：添加/查询收支记录（add_finance_record / query_finance）
- 健康：记录/查询体重、运动、饮水、睡眠（record_health / query_health）
- 日程：创建/查询/修改/完成日程（manage_schedule）
- 备忘录：创建/查询/搜索笔记（manage_memo）
- 天气：查询实时天气、预报、生活指数（query_weather）

回复风格：简洁、友好。当用户要求执行操作时，调用对应的工具函数。
如果用户询问无关话题，礼貌地说明你只能帮助个人助手相关的事务。"""

# Maps tool_name to the refresh event the frontend should listen for
TOOL_REFRESH_MAP = {
    "add_finance_record": "finance",
    "query_finance": None,
    "record_health": "health",
    "query_health": None,
    "manage_schedule": "schedule",
    "manage_memo": "memo",
    "query_weather": None,
}


class AIEngine:
    def __init__(self, api_key, tool_executor):
        self.client = DeepSeekClient(api_key)
        self.executor = tool_executor

    def chat(self, user_message, history=None, city=None):
        from datetime import date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        sys_prompt = SYSTEM_PROMPT + (
            "\n\n=== 时间信息 ===\n"
            "当前日期: " + today.isoformat() + " (" + self._weekday_cn(today) + ")\n"
            "昨天: " + yesterday.isoformat() + "\n"
            "本周一: " + week_start.isoformat() + "\n"
            "本月1日: " + month_start.isoformat() + "\n"
            "用户说今天/明天/昨天/本周/本月时，请据此计算日期(YYYY-MM-DD格式)。"
        )
        if city:
            sys_prompt += "\n\n用户默认城市: " + city + "。查天气时如果用户未指定城市，使用此城市。"

        messages = [{"role": "system", "content": sys_prompt}]
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
                tool_call_id = tc.get("id", "")
                params = json.loads(tc["function"]["arguments"])
                tool_result = self.executor.execute(tool_name, params)
                reply = self._format_reply(tool_name, params, tool_result)
                return {
                    "reply": reply,
                    "tool_called": tool_name,
                    "tool_call_id": tool_call_id,
                    "tool_calls": msg["tool_calls"],
                    "tool_result": tool_result,
                    "refresh": TOOL_REFRESH_MAP.get(tool_name)
                }

            return {
                "reply": msg.get("content", ""),
                "tool_called": None,
                "tool_call_id": None,
                "tool_calls": None,
                "tool_result": None,
                "refresh": None
            }
        except Exception as e:
            return {
                "reply": f"AI 服务暂不可用: {str(e)}",
                "tool_called": None,
                "tool_call_id": None,
                "tool_calls": None,
                "tool_result": None,
                "refresh": None
            }

    @staticmethod
    def _weekday_cn(d):
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return days[d.weekday()]

    def _format_reply(self, tool_name, params, result):
        if tool_name == "add_finance_record":
            t = "收入" if params.get("type") == "income" else "支出"
            note = params.get('note', '')
            tail = f"（{note}）" if note else ""
            return f"已记录一笔{t}：¥{params.get('amount', 0):.2f} {tail}".rstrip()

        if tool_name == "query_finance":
            qt = params.get("query_type", "")
            if qt == "monthly_summary":
                s = result
                bal = s.get('balance', 0)
                mood = "不错，有结余 👍" if bal > 0 else ("收支持平" if bal == 0 else "超支了，需注意 💡")
                cats = s.get('by_category', [])
                detail = ""
                if cats:
                    detail = " | ".join(f"{c['name']} ¥{c['amount']:.0f}" for c in cats[:5])
                return f"本月统计：收入 ¥{s.get('total_income',0):.2f}，支出 ¥{s.get('total_expense',0):.2f}，结余 ¥{bal:.2f}。{mood}\n支出分类：{detail}"
            if qt == "trend":
                if isinstance(result, list) and result:
                    lines = [f"{d['date']}：+¥{d['income']:.0f} / -¥{d['expense']:.0f}" for d in result[:7]]
                    return "最近每日流水：\n" + "\n".join(lines)
                return "暂无趋势数据"
            if isinstance(result, list):
                if not result:
                    return "暂无收支记录"
                lines = [f"{r['date']} {r['category_name']} {r['type']=='income' and '+' or '-'}¥{r['amount']:.2f} {r.get('note','')}" for r in result[:10]]
                extra = f"\n……共 {len(result)} 条" if len(result) > 10 else ""
                return "最近记录：\n" + "\n".join(lines) + extra
            return f"查询完成"

        if tool_name == "record_health":
            ht = params.get("health_type", "")
            if ht == "weight":
                return f"体重已记录：{params.get('value', '--')} kg"
            if ht == "exercise":
                return f"运动已记录：{params.get('type','')} {params.get('duration',0)} 分钟"
            if ht == "water":
                return f"饮水已记录：{params.get('amount', 0)} ml"
            if ht == "sleep":
                return f"睡眠已记录：{params.get('start_time','')} 至 {params.get('end_time','')}，质量 {params.get('quality',3)}/5"
            return "健康数据已记录"

        if tool_name == "query_health":
            qt = params.get("query_type", "")
            if qt == "dashboard":
                w = result.get('weight')
                weight_str = f"{w} kg" if w else "暂无记录"
                return f"健康概览：体重 {weight_str} | 今日饮水 {result.get('water_total',0)} ml | 今日运动 {result.get('exercise_today',0)} 分钟"
            if qt == "weight_trend" and isinstance(result, list):
                if not result: return "暂无体重记录"
                lines = [f"{d['date']}：{d['weight']} kg" for d in result[-7:]]
                latest = result[0] if result else {}
                return f"最近体重趋势（当前 {latest.get('weight','--')} kg）：\n" + "\n".join(lines)
            if qt == "sleep_stats":
                return f"睡眠统计：平均质量 {result.get('avg_quality','--')}/5"
            return "已查询"

        if tool_name == "manage_schedule":
            act = params.get("action", "")
            if act == "create":
                return f"日程已添加：{params.get('title','')}（{params.get('start_time','')}）"
            if act == "complete":
                return f"日程「{params.get('title','')}」已标记完成 ✅"
            if act == "delete":
                return f"日程已删除"
            if act == "query" and isinstance(result, list):
                if not result: return "暂无日程安排"
                lines = [f"• {e['start_time']} {e['title']} {'✅' if e.get('is_completed') else '⏳'}" for e in result[:8]]
                return "日程列表：\n" + "\n".join(lines)
            return "日程操作完成"

        if tool_name == "manage_memo":
            act = params.get("action", "")
            if act == "create":
                return f"笔记已创建：{params.get('title','')}"
            if act == "search":
                if isinstance(result, list):
                    if not result: return f"未找到包含「{params.get('keyword','')}」的笔记"
                    lines = [f"• {n['title']}" for n in result[:5]]
                    return f"搜索「{params.get('keyword','')}」找到 {len(result)} 篇：\n" + "\n".join(lines)
            if act == "delete":
                return "笔记已删除"
            if act == "query" and isinstance(result, list):
                if not result: return "暂无笔记"
                lines = [f"{'📌' if n.get('is_pinned') else '•'} {n['title']}" for n in result[:8]]
                return f"共 {len(result)} 篇笔记：\n" + "\n".join(lines)
            return "笔记操作完成"

        if tool_name == "query_weather":
            if isinstance(result, dict):
                return f"{result.get('city','')} 当前天气：{result.get('text','')}，气温 {result.get('temp','')}°C，体感 {result.get('feels_like','')}°C，湿度 {result.get('humidity','')}%"
            return "已查询天气"

        return f"操作完成"
