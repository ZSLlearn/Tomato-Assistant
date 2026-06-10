import json
from datetime import datetime
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


def _db():
    """Get shared per-request database connection."""
    if 'db' not in g:
        g.db = get_db()
    return g.db


def _get_engine():
    db = _db()
    settings = SettingsService(db)
    api_key = settings.get("deepseek_api_key")
    if not api_key:
        return None
    executor = ToolExecutor(
        FinanceService(db), HealthService(db), ScheduleService(db),
        MemoService(db), WeatherService()
    )
    return AIEngine(api_key, executor)


def _save_message(conversation_id, role, content, tool_called=None, tool_result=None):
    db = _db()
    db.execute(
        "INSERT INTO ai_messages (conversation_id, role, content, tool_called, tool_result, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (conversation_id, role, content,
         json.dumps(tool_called, ensure_ascii=False) if tool_called else None,
         json.dumps(tool_result, ensure_ascii=False) if tool_result else None,
         datetime.now().isoformat())
    )
    db.execute(
        "UPDATE ai_conversations SET updated_at=? WHERE id=?",
        (datetime.now().isoformat(), conversation_id)
    )
    db.commit()


def _build_history(conversation_id):
    """Build DeepSeek-format history with tool call chains."""
    db = _db()
    rows = db.execute(
        "SELECT * FROM ai_messages WHERE conversation_id=? ORDER BY id ASC",
        (conversation_id,)
    ).fetchall()
    history = []
    for r in rows:
        role = r["role"]
        content = r["content"]
        if role == "user":
            history.append({"role": "user", "content": content})
        elif role == "assistant":
            tc = r["tool_called"]
            tr = r["tool_result"]
            if tc and tr:
                tc_data = json.loads(tc) if isinstance(tc, str) else tc
                tr_data = json.loads(tr) if isinstance(tr, str) else tr
                if isinstance(tc_data, list):
                    history.append({
                        "role": "assistant",
                        "content": content,  # keep the reply text for context
                        "tool_calls": tc_data
                    })
                    tool_call_id = tc_data[0].get("id", "call_stored")
                    # Keep tool result concise
                    hist_result = {"success": True}
                    if isinstance(tr_data, dict):
                        for k in ("id", "amount", "type", "date", "title", "weight",
                                   "duration", "quality", "temp", "text"):
                            if k in tr_data:
                                hist_result[k] = tr_data[k]
                        hist_result["city"] = tr_data.get("city", "")
                    history.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(hist_result, ensure_ascii=False)
                    })
                    continue
            history.append({"role": "assistant", "content": content})
    return history


# === Conversations ===

@bp.route('/conversations', methods=['GET', 'POST'])
def conversations():
    db = _db()
    if request.method == 'GET':
        rows = db.execute(
            "SELECT * FROM ai_conversations ORDER BY updated_at DESC"
        ).fetchall()
        return jsonify({"code": 200, "message": "ok", "data": [dict(r) for r in rows]})

    now = datetime.now().isoformat()
    cur = db.execute(
        "INSERT INTO ai_conversations (title, created_at, updated_at) VALUES ('新对话', ?, ?)",
        (now, now)
    )
    db.commit()
    conv = {"id": cur.lastrowid, "title": "新对话", "created_at": now, "updated_at": now}
    return jsonify({"code": 201, "message": "ok", "data": conv}), 201


@bp.route('/conversations/<int:cid>', methods=['GET', 'DELETE', 'PUT'])
def conversation_detail(cid):
    db = _db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM ai_messages WHERE conversation_id=?", (cid,))
        db.execute("DELETE FROM ai_conversations WHERE id=?", (cid,))
        db.commit()
        return jsonify({"code": 200, "message": "已删除", "data": None})

    if request.method == 'PUT':
        data = request.get_json()
        title = data.get("title", "").strip()
        if title:
            db.execute("UPDATE ai_conversations SET title=?, updated_at=? WHERE id=?",
                       (title, datetime.now().isoformat(), cid))
            db.commit()

    row = db.execute("SELECT * FROM ai_conversations WHERE id=?", (cid,)).fetchone()
    if not row:
        return jsonify({"code": 404, "message": "对话不存在", "data": None}), 404
    msgs = db.execute(
        "SELECT * FROM ai_messages WHERE conversation_id=? ORDER BY id ASC", (cid,)
    ).fetchall()
    return jsonify({
        "code": 200, "message": "ok",
        "data": {
            "conversation": dict(row),
            "messages": [dict(m) for m in msgs]
        }
    })


# === Chat ===

@bp.route('/chat', methods=['POST'])
def chat():
    engine = _get_engine()
    if not engine:
        return jsonify({
            "code": 400, "message": "请先在设置中配置 DeepSeek API KEY", "data": None
        }), 400

    data = request.get_json()
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"code": 400, "message": "消息不能为空", "data": None}), 400

    db = _db()

    # Create conversation if needed
    if not conversation_id:
        now = datetime.now().isoformat()
        cur = db.execute(
            "INSERT INTO ai_conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
            (user_message[:30], now, now)
        )
        db.commit()
        conversation_id = cur.lastrowid

    # Build history BEFORE saving current message (avoid sending it twice)
    history = _build_history(conversation_id)

    # Save user message
    _save_message(conversation_id, "user", user_message)

    # Get default city
    settings_svc = SettingsService(db)
    default_city = settings_svc.get("default_city", "北京")

    # Call AI — engine appends user_message as new last message
    result = engine.chat(user_message, history, city=default_city)

    # Save AI response with tool call data
    tool_called_data = result.get("tool_calls") or result.get("tool_called")
    _save_message(conversation_id, "assistant", result["reply"],
                  tool_called_data, result.get("tool_result"))

    result["conversation_id"] = conversation_id
    return jsonify({"code": 200, "message": "ok", "data": result})


# === Test Connection ===

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
