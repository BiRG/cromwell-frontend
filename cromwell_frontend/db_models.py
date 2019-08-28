import shutil

import sqlalchemy as sa
from flask_login import UserMixin
from flask_sqlalchemy import Model, SQLAlchemy, event
import simplepam
import grp
import pwd
import subprocess
import json
import pathlib

from cromwell_frontend.exceptions import AuthException
from . import config


class Base(Model):
    __abstract__ = True
    created_on = sa.Column(sa.DateTime, default=sa.func.now())
    updated_on = sa.Column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())


db = SQLAlchemy(model_class=Base)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    username = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    id = db.synonym('username')

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def check_password(self, password):
        return simplepam.authenticate(self.username, password)

    @property
    def groups(self):
        return [group for group in grp.getgrall() if self.username in group.gr_mem]

    @property
    def pwd_entry(self):
        return pwd.getpwnam(self.username)

    @property
    def uid(self):
        return pwd.getpwnam(self.username).pw_uid

    @property
    def gid(self):
        return pwd.getpwnam(self.username).pw_gid

    @property
    def name(self):
        return pwd.getpwnam(self.username).pw_gecos

    @property
    def primary_group(self):
        return grp.getgrgid(self.gid)

    def in_group(self, group):
        if isinstance(group, grp.struct_group):
            return self.username in group.gr_mem
        elif isinstance(group, str):
            return self.username in grp.getgrnam(group).gr_mem
        elif isinstance(group, int):
            return self.username in grp.getgrgid(group).gr_mem
        else:
            raise ValueError(f'Cannot interpret group {group}. group should be string group name, integer gid, '
                             f'or grp.struct_group')

    @property
    def admin(self):
        return any([self.username in group.gr_mem for group in config.ADMIN_GROUPS])

    def to_dict(self):
        return {
            'username': self.username,
            'primary_group': self.primary_group,
            'name': self.name,
            'groups': self.groups
        }


class WorkflowDefinition(db.Model):
    __tablename__ = 'workflow_definition'
    relative_filename = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    id = db.synonym('relative_filename')
    name = db.Column(db.String)
    description = db.Column(db.String)
    owner_id = db.Column(db.String, db.ForeignKey('user.username'))
    owner = db.relationship(User, foreign_keys=[owner_id])

    @property
    def absolute_filename(self):
        return config.WORKFLOW_DEFINITION_DIR.joinpath(self.relative_filename)

    @absolute_filename.setter
    def absolute_filename(self, absolute_path):
        self.relative_filename = str(pathlib.Path(absolute_path).relative_to(config.WORKFLOW_DEFINITION_DIR))

    @property
    def file_exists(self):
        try:
            return config.WORKFLOW_DEFINITION_DIR.joinpath(self.relative_filename).is_file()
        except:
            return False

    @property
    def file_contents(self):
        try:
            return self.absolute_filename.read_text('utf-8')
        except FileNotFoundError:
            return ''

    @file_contents.setter
    def file_contents(self, contents):
        self.absolute_filename.write_text(contents)

    @property
    def inputs(self):
        if self.file_exists:
            try:
                return json.loads(subprocess.run(['java', '-jar', config.WOMTOOL_JAR, 'inputs',
                                                  self.absolute_filename.resolve()],
                                                  stdout=subprocess.PIPE).stdout)
            except json.JSONDecodeError:
                return {}
        return {}

    @property
    def valid(self):
        if self.file_exists:
            try:
                return not subprocess.run(
                    ['java', '-jar', config.WOMTOOL_JAR, 'validate', self.absolute_filename.resolve()],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE).returncode
            except:
                return False
        else:
            return False

    @property
    def errors(self):
        if self.file_exists:
            try:
                return subprocess.run(
                    ['java', '-jar', config.WOMTOOL_JAR, 'validate', self.absolute_filename.resolve()],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ).stderr.decode('utf-8')
            except:
                return ''
        else:
            return ''

    @staticmethod
    def delete_file(mapper, connection, target):
        try:
            target.absolute_filename.unlink()
        except FileNotFoundError:
            pass

    @staticmethod
    def synchronize_filename(target, value, oldvalue, initiator):
        if value != oldvalue and target.file_exists:
            shutil.move(str(config.WORKFLOW_DEFINITION_DIR.joinpath(oldvalue)),
                        str(config.WORKFLOW_DEFINITION_DIR.joinpath(value)))

    def to_dict(self):
        return {
            'relative_filename': self.relative_filename,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id
        }

    def update(self, data, current_user: User):
        for key in ['name', 'description', 'relative_filename', 'owner_id']:
            if self.owner is current_user or current_user.admin:
                setattr(self, key, data['key'])
            else:
                raise AuthException(f'User {current_user.username} cannot update workflow definition {self.relative_filename}')


event.listen(WorkflowDefinition, 'after_delete', WorkflowDefinition.delete_file)
event.listen(WorkflowDefinition.relative_filename, 'set', WorkflowDefinition.synchronize_filename)
