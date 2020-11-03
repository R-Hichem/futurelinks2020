from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import pymysql

app = Flask(__name__)
UPLOAD_FOLDER = 'futurelinks/uploadedNets/'
UPLOAD_FOLDER_CSV = 'futurelinks/uploadedCsv/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_CSV'] = UPLOAD_FOLDER_CSV
app.config['SECRET_KEY'] = '3d6f45a5fc12445dbac2f59c3b6c7cb1'
app.config['CORS_HEADERS'] = 'Content-Type'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
connect_string = 'mysql+pymysql://b74d0f09dd1574:3c5f697a@eu-cdbr-west-03.cleardb.net/heroku_d0271aab022de6f'
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string 

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from futurelinks import routes