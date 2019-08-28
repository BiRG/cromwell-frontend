from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from .login_manager import login_manager, authenticate_user
from .db_models import db
from .page_data import PageData
from . import config
from .blueprints.api import api
from .blueprints.workflows import workflows
from .blueprints.workflow_definitions import workflow_definitions
from .blueprints.cromwell_api import cromwell_api
from cromwell_frontend.exceptions import LoginError

app = Flask(__name__)
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

app.permanent_session_lifetime = 86400
app.jinja_env.globals.update(BRAND=config.BRAND)
app.jinja_env.globals.update(BOOTSTRAP_CSS_URL=config.BOOTSTRAP_CSS_URL)
app.jinja_env.globals.update(current_user=current_user)
app.jinja_env.globals.update(config=config)


def format_datetime(value, kind='date'):
    try:
        if kind == 'date':
            return value.strftime('%d %b %y %H:%M')
        elif kind == 'timestamp':
            return value.timestamp()
        else:
            return ''
    except AttributeError:
        return ''


def make_valid_tag(value):
    if isinstance(value, str):
        for c in ' !"#$%&\'()*+,./:;<=>?@[\]^`{|}~':
            value = value.replace(c, '')
    return value


app.jinja_env.filters['datetime'] = format_datetime
app.jinja_env.filters['make_valid_tag'] = make_valid_tag
app.secret_key = config.SECRET


app.register_blueprint(api)
app.register_blueprint(workflows)
app.register_blueprint(workflow_definitions)
app.register_blueprint(cromwell_api)


@app.route('/')
@login_required
def home():
    return render_template('home.html', page_data=PageData('Cromwell Frontend'))


@app.route('/login', methods=['GET', 'POST'])
def login(msg=None, error=None):
    try:
        if request.method == 'POST':
            user = authenticate_user(request)
            redirect_url = request.args.get('next') if request.args.get('next') is not None else url_for('home')
            login_user(user)
            return redirect(redirect_url)
    except(ValueError, LoginError) as e:
        return render_template('login.html', page_data=PageData('Login'), error=str(e))
    return render_template('login.html', page_data=PageData('Login'), msg=msg, error=error)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == '__main__':
    app.run(host=config.HOST_IP, port=8080)
