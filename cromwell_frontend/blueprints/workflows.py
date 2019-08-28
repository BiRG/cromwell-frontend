from flask import Blueprint, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import redirect

from cromwell_frontend.db_models import WorkflowDefinition
from cromwell_frontend.page_data import PageData, WorkflowEntry, WorkflowSubmissionData, WorkflowList
from cromwell_frontend.util import handle_exception_browser
from cromwell_frontend.workflow import get_workflow, start_workflow

workflows = Blueprint('workflows', __name__, url_prefix='/workflows')


@workflows.route('/')
@login_required
def list_workflows():
    try:
        return render_template('workflow_list.html', page_data=WorkflowList('Workflows'))
    except Exception as e:
        return handle_exception_browser(e)


@workflows.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_workflow():
    try:
        workflow_definition_id = request.args.get('workflow_definition')
        workflow_definition = WorkflowDefinition.query.filter_by(relative_filename=workflow_definition_id).first()
        if request.method == 'POST':
            dependencies = request.files.get('dependencies')
            source = request.form.get('source')
            on_hold = request.form.get('on_hold') == 'on'
            inputs = request.form.get('inputs')
            options = request.form.get('options')
            workflow_type_version = request.form.get('workflow_type_version')
            labels = request.form.get('labels')
            workflow = start_workflow(source, on_hold, inputs, options, workflow_type_version, labels, dependencies)
            return redirect(url_for('workflows.view_workflow', workflow_id=workflow.id))
        return render_template('workflow_submission.html',
                               page_data=WorkflowSubmissionData('Submit Workflow', workflow_definition))
    except Exception as e:
        return handle_exception_browser(e)


@workflows.route('/<workflow_id>', methods=['GET'])
@login_required
def view_workflow(workflow_id):
    try:
        workflow = get_workflow(workflow_id)
        # check actions
        return render_template('workflow_entry.html', page_data=WorkflowEntry(f'Workflow {workflow_id}', workflow))
    except Exception as e:
        return handle_exception_browser(e)

