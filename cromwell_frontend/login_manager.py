import datetime

from flask_login import LoginManager
from .db_models import User, db
from cromwell_frontend.exceptions import LoginError
import pwd
import jwt
from . import config

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.blueprint_login_views = {
    'api': 'api.unauthorized'
}


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        try:
            pwd.getpwnam(user.username)
            if config.AUTHORIZED_GROUPS is not None and not any([user_id in group.gr_mem for group in config.AUTHORIZED_GROUPS]):
                return
        except AttributeError:
            return
        # if user exists in PAM, add them to the database
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
    return user


@login_manager.request_loader
def request_loader(req):
    if 'Authorization' in req.headers:
        auth_header = req.headers.get('Authorization')
        # Header should be in format "JWT <>" or "Bearer <>"
        token = auth_header.split(' ')[1]
        # if this is invalid, jwt.decode will throw. So no need to check password
        user_data = jwt.decode(token, config.SECRET, algorithms=['HS256'])
        return User.query.filter_by(id=user_data['username']).first()


def authenticate_user(req):
    username = req.form.get('username')
    password = req.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user is None:
        try:
            pwd.getpwnam(username)
        except AttributeError:
            return
        # if user exists in PAM, add them to the database
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    if user.check_password(password):
        return user
    raise LoginError('Incorrect username/password')


def get_jwt(username, password):
    user = User.query.filter_by(username=username).first()
    if user.check_password(password):
        user_data = {'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}
        return jwt.encode(user_data, config.SECRET, algorithm='HS256').decode('utf-8')
    raise LoginError('Incorrect username/password.')


