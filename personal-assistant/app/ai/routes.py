from flask import request, jsonify, g
from . import bp
from app.database import get_db
from app.modules.finance.service import FinanceService
from app.modules.health.service import HealthService
from app.modules.schedule.service import ScheduleService
from app.modules.memo.service import MemoService
from app.modules.weather.service import WeatherService
from app.modules.settings.service import SettingsService
from app.ai.engine import AIEngine
from app.ai.tool_executor import ToolExecutor
def _get_engine():
    db = get_db()
    settings = SettingsService(db)
    api_key = settings.get("deepseek_api_key")
    if not api_key:
        return None
    executor = ToolExecutor(
        FinanceService(db), HealthService(db), ScheduleService(db),
        MemoService(db), WeatherService()
    )
    return AIEngine(api_key, executor)


@bp.route('/chat', methods=['POST'])
def chat():
    engine = _get_engine()
    if not engine:
        return jsonify({
            "code": 400, "message": "请先在设置中配置 DeepSeek API KEY", "data": None
        }), 400
    data = request.get_json()
    result = engine.chat(data.get("message", ""), data.get("history"))
    return jsonify({"code": 200, "message": "ok", "data": result})


@bp.route('/test-connection', methods=['POST'])
def test_connection():
    from app.ai.deepseek_client import DeepSeekClient
    api_key = request.get_json().get("api_key", "")
    if not api_key:
        return jsonify({"code": 400, "message": "API KEY 不能为空", "data": {"ok": False}}), 400
    try:
        client = DeepSeekClient(api_key, timeout=10)
        client.chat_completion([{"role": "user", "content": "hi"}], model="deepseek-chat")
        return jsonify({"code": 200, "message": "连接成功", "data": {"ok": True}})
    except Exception as e:
        return jsonify({"code": 503, "message": str(e), "data": {"ok": False}})
