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
                    "query_type": {"type": "string", "enum": ["recent", "monthly_summary", "by_category", "trend"]},
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
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
                    "health_type": {"type": "string", "enum": ["weight", "exercise", "water", "sleep"]},
                    "value": {"type": "number", "description": "数值"},
                    "duration": {"type": "integer", "description": "运动时长(分钟)"},
                    "date": {"type": "string"},
                    "note": {"type": "string"}
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
                    "query_type": {"type": "string", "enum": ["dashboard", "weight_trend", "sleep_stats", "exercise_stats"]},
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
                    "action": {"type": "string", "enum": ["create", "query", "update", "complete", "delete"]},
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "category": {"type": "string", "enum": ["工作", "个人", "紧急"]},
                    "date": {"type": "string"},
                    "event_id": {"type": "integer"}
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
                    "action": {"type": "string", "enum": ["create", "query", "search", "update", "delete"]},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "keyword": {"type": "string"},
                    "note_id": {"type": "integer"}
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
                    "city": {"type": "string", "description": "城市名"},
                    "type": {"type": "string", "enum": ["now", "forecast", "life_index"]},
                    "days": {"type": "integer", "default": 7}
                },
                "required": ["city"]
            }
        }
    }
]

SYSTEM_PROMPT = """你是个人助手，帮助管理记账、健康、日程、备忘录和天气查询。
可执行的操作：
- 记账：添加/查询收支记录
- 健康：记录/查询体重、运动、饮水、睡眠
- 日程：创建/查询/修改/完成日程
- 备忘录：创建/查询/搜索笔记
- 天气：查询实时天气、预报、生活指数

回复风格：简洁、友好。当用户要求执行操作时，调用对应的工具函数。
如果用户询问无关话题，礼貌地说明你只能帮助个人助手相关的事务。"""


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
                return {
                    "reply": f"✅ {tool_name} 执行成功",
                    "tool_called": tool_name,
                    "tool_result": tool_result
                }

            return {
                "reply": msg.get("content", ""),
                "tool_called": None,
                "tool_result": None
            }
        except Exception as e:
            return {
                "reply": f"AI 服务暂时不可用: {str(e)}",
                "tool_called": None,
                "tool_result": None
            }
