import os

from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_required

from cromwell_frontend import config
from cromwell_frontend.db_models import WorkflowDefinition, db
from cromwell_frontend.page_data import WorkflowDefinitionEntry, WorkflowDefinitionList
from cromwell_frontend.util import handle_exception_browser
from cromwell_frontend.exceptions import NotFoundException

workflow_definitions = Blueprint('workflow_definitions', __name__, url_prefix='/workflow_definitions')


@workflow_definitions.route('/')
@login_required
def list_workflow_definitions():
    return render_template('workflow_definition_list.html', page_data=WorkflowDefinitionList('Workflow Definitions'))


@workflow_definitions.route('/create', methods=['GET', 'POST'])
@login_required
def create_workflow_definition():
    try:
        if request.method == 'POST':
            workflow_definition = WorkflowDefinition(
                name=request.form.get('name'),
                description=request.form.get('description'),
                relative_filename=request.form.get('relative_path'),
                file_contents=request.form.get('definition'))
            db.session.add(workflow_definition)
            db.session.commit()
            return redirect(url_for('workflow_definitions.view_workflow_definition',
                                    relative_path=workflow_definition.relative_filename))
        else:
            count = WorkflowDefinition.query.count()
            filename = f'workflow{count}.wdl'
            while config.WORKFLOW_DEFINITION_DIR.joinpath(filename).exists():
                count += 1
                filename = f'workflow{count}.wdl'
            workflow_definition = WorkflowDefinition(relative_filename=str(filename), name=str(filename))
            return render_template('workflow_definition_entry.html', page_data=WorkflowDefinitionEntry('Create workflow definition', workflow_definition))
    except Exception as e:
        return handle_exception_browser(e)


@workflow_definitions.route('/<relative_path>', methods=['GET', 'POST', 'DELETE'])
@login_required
def view_workflow_definition(relative_path):
    try:
        workflow_definition = WorkflowDefinition.query.filter_by(relative_filename=relative_path).first()
        if workflow_definition is None:
            raise NotFoundException(f'No workflow with path {relative_path} exists!')
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            relative_filename = request.form.get('relative_path')
            file_contents = request.form.get('definition')
            if workflow_definition is None:
                workflow_definition = WorkflowDefinition(
                    relative_filename=relative_filename,
                    name=name,
                    description=description
                )
                workflow_definition.file_contents = file_contents
                db.session.add(workflow_definition)
            else:
                workflow_definition.name = name
                workflow_definition.description = description
                workflow_definition.relative_filename = relative_filename
                workflow_definition.file_contents = file_contents
            db.session.commit()
        elif request.method == 'DELETE':
            db.session.delete(workflow_definition)
            db.session.commit()
        else:
            if workflow_definition is None:
                count = WorkflowDefinition.query.count()
                filename = f'workflow{count}.wdl'
                while os.path.exists(os.path.join(config.WORKFLOW_DEFINITION_DIR, filename)):
                    count += 1
                    filename = f'workflow{count}.wdl'
                workflow_definition = WorkflowDefinition(relative_filename=filename)
        return render_template('workflow_definition_entry.html',
                               page_data=WorkflowDefinitionEntry(workflow_definition.name, workflow_definition))
    except Exception as e:
        return handle_exception_browser(e)
