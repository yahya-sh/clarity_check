from flask import Flask
from flask_wtf import CSRFProtect


app = Flask(__name__, template_folder='../templates', static_folder='../static')
csrf = CSRFProtect(app)
app.config.from_pyfile('settings.py')
