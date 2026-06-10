from flask import Flask, render_template
from app.database import init_db


def create_app():
    app = Flask(__name__)
    init_db()

    @app.route('/')
    def index():
        return render_template('index.html')

    from app.modules.finance import bp as finance_bp
    from app.modules.health import bp as health_bp
    from app.modules.schedule import bp as schedule_bp
    from app.modules.memo import bp as memo_bp
    from app.modules.weather import bp as weather_bp
    from app.modules.settings import bp as settings_bp
    from app.ai import bp as ai_bp

    app.register_blueprint(finance_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(memo_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(ai_bp)

    return app
