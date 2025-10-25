from flask import Flask, redirect, url_for
import os
from dotenv import load_dotenv
from core.db import db


def create_app() -> Flask:
    load_dotenv()
    app = Flask(
        __name__,
        template_folder="core/templates",
        static_folder="core/static",
    )

    app.config["SECRET_KEY"] = "dev-secret-change-me"

    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db = os.getenv("MYSQL_DB")

    # Enforce MySQL usage only
    if not (mysql_user and mysql_password and mysql_db):
        raise RuntimeError(
            "MySQL environment variables are required: MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        from core import models  # noqa: F401
        db.create_all()

    from core.routes import core_bp
    from core.cli import register_cli

    register_cli(app)

    @app.errorhandler(404)
    def not_found(_):
        return redirect(url_for("core.home"))

    app.register_blueprint(core_bp)

    return app


app = create_app()


if __name__ == "__main__":
    # For development only
    app.run(host="127.0.0.1", port=5000, debug=True)


