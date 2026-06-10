from flask import Blueprint, request, jsonify, render_template
from .service import WeatherService

bp = Blueprint('weather', __name__, url_prefix='/weather')

_svc = WeatherService()


@bp.route('/')
def page():
    return render_template('weather/index.html')


@bp.route('/api/now')
def now():
    city = request.args.get('city', '')
    try:
        return jsonify({"code": 200, "message": "ok", "data": _svc.get_real_time(city)})
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 503, "message": f"天气服务暂不可用: {str(e)}", "data": None}), 503


@bp.route('/api/forecast')
def forecast():
    city = request.args.get('city', '')
    days = request.args.get('days', 7, type=int)
    try:
        return jsonify({"code": 200, "message": "ok", "data": _svc.get_forecast(city, days)})
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 503, "message": f"天气服务暂不可用: {str(e)}", "data": None}), 503


@bp.route('/api/life-index')
def life_index():
    city = request.args.get('city', '')
    try:
        return jsonify({"code": 200, "message": "ok", "data": _svc.get_life_index(city)})
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 503, "message": f"天气服务暂不可用: {str(e)}", "data": None}), 503


@bp.route('/api/search')
def search_city():
    keyword = request.args.get('keyword', '')
    try:
        return jsonify({"code": 200, "message": "ok", "data": _svc.search_city(keyword)})
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 503, "message": f"天气服务暂不可用: {str(e)}", "data": None}), 503
