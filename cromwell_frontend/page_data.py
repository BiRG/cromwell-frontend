from flask import url_for
from flask_login import current_user
import ruamel.yaml as yaml

from .db_models import WorkflowDefinition, User
from .workflow import Workflow, get_workflows


class PageData:
    def __init__(self, title):
        self.title = title
        self.current_user = current_user


class WorkflowList(PageData):
    def __init__(self, title):
        super().__init__(title)
        self.workflows = get_workflows()


class WorkflowDefinitionList(PageData):
    def __init__(self, title):
        super().__init__(title)
        self.workflow_definitions = [workflow for workflow in WorkflowDefinition.query.all()]


class WorkflowEntry(PageData):
    def __init__(self, title, workflow):
        super().__init__(title)
        self.workflow = workflow
        self.chart_url = url_for('api.get_workflow_chart_data', workflow_id=workflow.id)


class WorkflowDefinitionEntry(PageData):
    def __init__(self, title, workflow_definition):
        super().__init__(title)
        self.workflow_definition = workflow_definition


class WorkflowSubmissionData(PageData):
    def __init__(self, title, workflow_definition: WorkflowDefinition):
        super().__init__(title)
        try:
            self.relative_filename = workflow_definition.relative_filename
            self.workflow_source = workflow_definition.file_contents
            with yaml.StringIO() as stream:
                yaml.dump(workflow_definition.inputs, stream, default_flow_style=False)
                self.inputs = stream.getvalue()
        except AttributeError:
            self.inputs = ''
            self.relative_filename = ''
            self.workflow_source = ''
