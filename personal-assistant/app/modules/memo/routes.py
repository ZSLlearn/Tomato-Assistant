from flask import Blueprint, request, jsonify, render_template, g
from app.database import get_db
from .service import MemoService

bp = Blueprint('memo', __name__, url_prefix='/memo')


def _svc():
    if 'db' not in g:
        g.db = get_db()
    return MemoService(g.db)


@bp.route('/')
def page():
    return render_template('memo/index.html')


@bp.route('/api/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'GET':
        data = _svc().list_notes(
            category=request.args.get('category'),
            tag=request.args.get('tag'),
            keyword=request.args.get('keyword'),
            is_pinned=request.args.get('is_pinned', type=lambda x: x == 'true' if x else None)
        )
        return jsonify({"code": 200, "message": "ok", "data": data})
    body = request.get_json()
    try:
        rec = _svc().create_note(body.get('title', ''), body.get('content', ''),
                                 body.get('category', ''), body.get('tags', ''))
        return jsonify({"code": 201, "message": "ok", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/notes/<int:nid>', methods=['GET', 'PUT', 'DELETE'])
def note_detail(nid):
    if request.method == 'GET':
        try:
            return jsonify({"code": 200, "message": "ok", "data": _svc().get_note(nid)})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    if request.method == 'PUT':
        body = request.get_json()
        try:
            rec = _svc().update_note(nid, **body)
            return jsonify({"code": 200, "message": "ok", "data": rec})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    _svc().delete_note(nid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


@bp.route('/api/notes/<int:nid>/pin', methods=['PUT'])
def toggle_pin(nid):
    try:
        rec = _svc().toggle_pin(nid)
        return jsonify({"code": 200, "message": "ok", "data": rec})
    except ValueError as e:
        return jsonify({"code": 404, "message": str(e), "data": None}), 404
