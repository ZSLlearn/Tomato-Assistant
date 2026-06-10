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
