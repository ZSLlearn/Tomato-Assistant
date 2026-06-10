from flask import Blueprint, request, jsonify, render_template, g
from app.database import get_db
from .service import ScheduleService

bp = Blueprint('schedule', __name__, url_prefix='/schedule')


def _svc():
    if 'db' not in g:
        g.db = get_db()
    return ScheduleService(g.db)


@bp.route('/')
def page():
    return render_template('schedule/index.html')


@bp.route('/api/events', methods=['GET', 'POST'])
def events():
    if request.method == 'GET':
        data = _svc().list_events(
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
            category=request.args.get('category'),
            is_completed=request.args.get('is_completed', type=lambda x: x == 'true' if x else None)
        )
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().create_event(
            body['title'], body.get('start_time', ''), body.get('end_time', ''),
            body.get('description', ''), body.get('category', '个人'),
            body.get('priority', 2))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/events/<int:eid>', methods=['PUT', 'DELETE'])
def event_detail(eid):
    if request.method == 'PUT':
        body = request.get_json()
        try:
            rec = _svc().update_event(eid, **body)
            return jsonify({"code": 200, "message": "ok", "data": rec})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    _svc().delete_event(eid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


@bp.route('/api/events/<int:eid>/complete', methods=['PUT'])
def complete_event(eid):
    try:
        rec = _svc().mark_completed(eid)
        return jsonify({"code": 200, "message": "ok", "data": rec})
    except ValueError as e:
        return jsonify({"code": 404, "message": str(e), "data": None}), 404


@bp.route('/api/events/upcoming')
def upcoming():
    hours = request.args.get('hours', 24, type=int)
    return jsonify({"code": 200, "message": "ok", "data": _svc().get_upcoming_events(hours)})
