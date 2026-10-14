from flask import Flask, render_template, session
from flask_bootstrap import Bootstrap5
from flask_mysqldb import MySQL
mysql = MySQL()



#create a function that creates a web application
# a web server will run this web application
def create_app():
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'BetterSecretNeeded123'
    # MySQL configurations
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'password01'
    app.config['MYSQL_DB'] = 'fundraising_db'
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql.init_app(app)

    bootstrap = Bootstrap5(app)
    
    #importing modules here to avoid circular references, register blueprints of routes
    from . import views
    app.register_blueprint(views.bp)
    @app.errorhandler(404) 
    # inbuilt function which takes error as parameter 
    def not_found(e): 
      return render_template("404.html"),400

    @app.errorhandler(500)
    def internal_error(e):
      return render_template("500.html"),500

    from . import session

    return app