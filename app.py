from flask import Flask
from db import engine, Base
from config import Config
from models.employee import Employee
from models.vacation_total import VacationTotal
from models.vacation_used import VacationUsed

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Base.metadata.create_all(bind=engine)

    
    # blueprints
    from routes.admin import admin_bp
    from routes.employee import employee_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(employee_bp, url_prefix="/employee")

    @app.route("/")
    def index():
        return {"message": "Vacation Tracker API is running"}, 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0")
