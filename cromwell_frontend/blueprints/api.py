from flask import request, Blueprint, jsonify, redirect, url_for
from flask_login import login_required, current_user

from cromwell_frontend.db_models import WorkflowDefinition, db
from cromwell_frontend.exceptions import NotFoundException, AuthException
from cromwell_frontend.login_manager import authenticate_user, get_jwt
from cromwell_frontend.util import handle_exception
from cromwell_frontend.workflow import Workflow

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/unauthorized')
def unauthorized():
    return jsonify({'message': 'Not authenticated.'}), 401


@api.route('/authenticate', methods=['POST'])
def jwt_authenticate():
    try:
        credentials = request.get_json(force=True)
        authenticate_user(request)
        token = get_jwt(credentials['username'], credentials['password'])
        return jsonify({'token': str(token)}), 200
    except Exception as e:
        return jsonify({'message': f'authentication failed: {e}'}), 403


@api.route('/workflow_definitions', methods=['GET', 'POST'])
@login_required
def list_workflow_definitions():
    try:
        if request.method == 'POST':
            data = request.get_json(force=True)
            workflow_definition = WorkflowDefinition(relative_filename=data['relative_filename'],
                                                     name=data['name'],
                                                     description=data['description'],
                                                     owner=current_user)
            db.session.add(workflow_definition)
            db.session.commit()
            return redirect(url_for('api.get_workflow_definition',
                                    relative_filename=workflow_definition.relative_filename))
        else:
            return jsonify([definition.to_dict for definition in WorkflowDefinition.query.all()])
    except Exception as e:
        return handle_exception(e)


@api.route('/workflow_definitions/<relative_filename>', methods=['GET', 'POST', 'DELETE'])
@login_required
def get_workflow_definition(relative_filename):
    try:
        workflow_definition = WorkflowDefinition.query.filter_by(relative_filename=relative_filename).first()
        if workflow_definition is None:
            raise NotFoundException(f'No workflow with relative filename {relative_filename} exists!')
        if request.method == 'POST':
            data = request.get_json(force=True)
            workflow_definition.update(data, current_user)
            db.session.commit()
        if request.method == 'DELETE':
            if current_user is workflow_definition.owner or current_user.admin:
                db.session.delete(workflow_definition)
                db.session.commit()
                return jsonify({'message': f'Workflow definition {workflow_definition.relative_filename} deleted'})
            else:
                raise AuthException(f'User {current_user.username} cannot delete {workflow_definition.relative_filename}')
        return jsonify(workflow_definition.to_dict())
    except Exception as e:
        return handle_exception(e)


@api.route('/workflow_chart/<workflow_id>', methods=['GET'])
@login_required
def get_workflow_chart_data(workflow_id):
    try:
        workflow = Workflow(workflow_id)
        return jsonify(workflow.get_chart_metadata())
    except Exception as e:
        return handle_exception(e)


@api.route('/workflows/<workflow_id>/release_hold', methods=['POST'])
@login_required
def release_workflow_hold(workflow_id):
    try:
        workflow = Workflow(workflow_id)
        if current_user == workflow.owner or current_user.admin:
            return jsonify(workflow.resume())
        else:
            raise AuthException(f'User {current_user.id} cannot release hold on {workflow_id}')
    except Exception as e:
        return handle_exception(e)


@api.route('/workflows/<workflow_id>/cancel', methods=['POST'])
@login_required
def cancel_workflow(workflow_id):
    try:
        workflow = Workflow(workflow_id)
        if current_user == workflow.owner or current_user.admin:
            return jsonify(workflow.cancel())
        else:
            raise AuthException(f'User {current_user.id} cannot release hold on {workflow_id}')
    except Exception as e:
        return handle_exception(e)
