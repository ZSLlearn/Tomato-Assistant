from flask import Blueprint, request, jsonify, render_template, g
from app.database import get_db
from .service import HealthService

bp = Blueprint('health', __name__, url_prefix='/health')


def _svc():
    if 'db' not in g:
        g.db = get_db()
    return HealthService(g.db)


@bp.route('/')
def page():
    return render_template('health/index.html')


@bp.route('/api/dashboard')
def dashboard():
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_dashboard()})


# === 体重 ===

@bp.route('/api/weight', methods=['GET', 'POST'])
def weight_list():
    if request.method == 'GET':
        data = _svc().list_weight(request.args.get('date_from'), request.args.get('date_to'))
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().record_weight(body['weight'], body.get('date', ''), body.get('note', ''))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/weight/<int:rid>', methods=['DELETE'])
def weight_detail(rid):
    _svc().delete_weight(rid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


@bp.route('/api/weight/trend')
def weight_trend():
    days = request.args.get('days', 30, type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_weight_trend(days)})


# === 运动 ===

@bp.route('/api/exercise', methods=['GET', 'POST'])
def exercise_list():
    if request.method == 'GET':
        data = _svc().list_exercise(request.args.get('date_from'), request.args.get('date_to'))
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().record_exercise(body['type'], body['duration'],
                                     body.get('calories', 0), body.get('date', ''),
                                     body.get('note', ''))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/exercise/<int:rid>', methods=['DELETE'])
def exercise_detail(rid):
    _svc().delete_exercise(rid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


@bp.route('/api/exercise/stats')
def exercise_stats():
    days = request.args.get('days', 30, type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_exercise_stats(days)})


# === 饮水 ===

@bp.route('/api/water', methods=['GET', 'POST'])
def water_list():
    if request.method == 'GET':
        data = _svc().list_water(request.args.get('date_from'), request.args.get('date_to'))
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().record_water(body['amount'], body.get('date', ''))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/water/<int:rid>', methods=['DELETE'])
def water_detail(rid):
    _svc().delete_water(rid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


# === 睡眠 ===

@bp.route('/api/sleep', methods=['GET', 'POST'])
def sleep_list():
    if request.method == 'GET':
        data = _svc().list_sleep(request.args.get('date_from'), request.args.get('date_to'))
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().record_sleep(body['start_time'], body['end_time'],
                                  body.get('quality', 3), body.get('date', ''))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 422, "message": str(e), "data": None}), 422


@bp.route('/api/sleep/<int:rid>', methods=['DELETE'])
def sleep_detail(rid):
    _svc().delete_sleep(rid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


@bp.route('/api/sleep/stats')
def sleep_stats():
    days = request.args.get('days', 7, type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_sleep_stats(days)})
