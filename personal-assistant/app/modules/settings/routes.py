from flask import Blueprint, request, jsonify, render_template, g
from app.database import get_db
from .service import SettingsService

bp = Blueprint('settings', __name__, url_prefix='/settings')


def _svc():
    if 'db' not in g:
        g.db = get_db()
    return SettingsService(g.db)


@bp.route('/')
def page():
    return render_template('settings/index.html')


@bp.route('/api/config', methods=['GET', 'PUT'])
def config():
    if request.method == 'GET':
        return jsonify({"code": 200, "message": "ok", "data": _svc().get_all()})
    body = request.get_json()
    key = body.get('key', '')
    value = body.get('value', '')
    if not key:
        return jsonify({"code": 400, "message": "配置键不能为空", "data": None}), 400
    _svc().set(key, value)
    return jsonify({"code": 200, "message": "保存成功", "data": {"key": key, "value": value}})


@bp.route('/api/detect-city')
def detect_city():
    """Detect user city via IP geolocation (ip-api.com, free, no key needed)."""
    import requests
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Use client IP or fallback to the public API
        client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        if not client_ip:
            client_ip = request.remote_addr
        # ip-api.com free tier: 45 req/min, no API key
        resp = requests.get(f'http://ip-api.com/json/{client_ip}?lang=zh-CN',
                            timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == 'success':
            city = data.get('city', '')
            region = data.get('regionName', '')
            country = data.get('country', '')
            return jsonify({
                "code": 200, "message": "ok",
                "data": {"city": city, "region": region, "country": country,
                         "display": f"{city}，{region}，{country}"}
            })
    except Exception as e:
        logger.warning(f"IP城市定位失败: {e}")
    return jsonify({"code": 503, "message": "定位失败", "data": None})
