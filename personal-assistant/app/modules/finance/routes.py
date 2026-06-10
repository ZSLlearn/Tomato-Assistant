from flask import Blueprint, request, jsonify, render_template, g
from app.database import get_db
from .service import FinanceService

bp = Blueprint('finance', __name__, url_prefix='/finance')


def _svc():
    if 'db' not in g:
        g.db = get_db()
    return FinanceService(g.db)


@bp.route('/')
def page():
    return render_template('finance/index.html')


# === 分类 ===

@bp.route('/api/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'GET':
        cats = _svc().list_categories(request.args.get('type'))
        return jsonify({"code": 200, "message": "ok", "data": cats})
    data = request.get_json()
    errs = _validate_category(data)
    if errs:
        return jsonify({"code": 400, "message": "; ".join(errs), "data": None}), 400
    try:
        cat = _svc().create_category(data['name'], data['type'], data.get('icon', ''))
        return jsonify({"code": 201, "message": "创建成功", "data": cat}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/categories/<int:cid>', methods=['PUT', 'DELETE'])
def category_detail(cid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            cat = _svc().update_category(cid, **data)
            return jsonify({"code": 200, "message": "ok", "data": cat})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    _svc().delete_category(cid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


# === 账单 ===

@bp.route('/api/records', methods=['GET', 'POST'])
def records():
    if request.method == 'GET':
        recs = _svc().list_records(
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
            category_id=request.args.get('category_id', type=int),
            type=request.args.get('type')
        )
        return jsonify({"code": 200, "message": "ok", "data": recs})
    data = request.get_json()
    errs = _validate_record(data)
    if errs:
        return jsonify({"code": 400, "message": "; ".join(errs), "data": None}), 400
    try:
        rec = _svc().add_record(**data)
        return jsonify({"code": 201, "message": "创建成功", "data": rec}), 201
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400


@bp.route('/api/records/<int:rid>', methods=['PUT', 'DELETE'])
def record_detail(rid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            rec = _svc().update_record(rid, **data)
            return jsonify({"code": 200, "message": "ok", "data": rec})
        except ValueError as e:
            return jsonify({"code": 404, "message": str(e), "data": None}), 404
    _svc().delete_record(rid)
    return jsonify({"code": 200, "message": "删除成功", "data": None})


# === 统计 ===

@bp.route('/api/summary')
def summary():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({
        "code": 200, "message": "ok",
        "data": _svc().get_monthly_summary(year, month)
    })


@bp.route('/api/trend')
def trend():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({
        "code": 200, "message": "ok",
        "data": _svc().get_trend(year, month)
    })


# === 校验函数 ===

def _validate_category(data):
    errs = []
    if not data.get('name'):
        errs.append("分类名不能为空")
    if data.get('type') not in ('income', 'expense'):
        errs.append("类型必须是 income 或 expense")
    return errs


def _validate_record(data):
    errs = []
    if data.get('type') not in ('income', 'expense'):
        errs.append("类型必须是 income 或 expense")
    if not data.get('amount') or data['amount'] <= 0:
        errs.append("金额必须大于0")
    if not data.get('date'):
        errs.append("日期不能为空")
    return errs
