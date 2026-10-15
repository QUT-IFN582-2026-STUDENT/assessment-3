import os

import flask
from flask_bootstrap import Bootstrap5

from .db_campaign import close_db

def create_app():
    app = flask.Flask(__name__)
    app.debug = True
    app.secret_key = os.environ.get('SECRET_KEY', 'BetterSecretNeeded123')

    # MySQL connection settings (read by get_db() in db_campaign.py).
    app.config.update(
        DB_HOST=os.environ.get('DB_HOST', '127.0.0.1'),
        DB_PORT=int(os.environ.get('DB_PORT', 3306)),
        DB_USER=os.environ.get('DB_USER', 'root'),
        DB_PASSWORD=os.environ.get('DB_PASSWORD', '1234'),
        DB_NAME=os.environ.get('DB_NAME', 'fundraising_db'),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  
    )

    bootstrap = Bootstrap5(app)

    # close the database connection at the end of every request
    app.teardown_appcontext(close_db)

    # importing modules here to avoid circular references, register blueprints of routes
    from . import views
    app.register_blueprint(views.bp)

    # Return the correct HTTP status code along with each error page
    @app.errorhandler(404)
    def not_found(e):
        return flask.render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return flask.render_template("500.html"), 500

    return app