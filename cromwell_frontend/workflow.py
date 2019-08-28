import json

from flask import url_for
from flask_login import current_user
from ruamel.yaml import YAML
from datetime import datetime
from io import StringIO
from typing import List, Dict, Any

import requests
from cromwell_frontend.exceptions import NotFoundException, AuthException
from .config import CROMWELL_URL
from .db_models import User


class Workflow:
    def __init__(self, workflow_id):
        self.id = workflow_id
        self.owner_id = None
        self.owner = None
        self.submission = datetime.utcfromtimestamp(0)
        self.start = datetime.utcfromtimestamp(0)
        self.end = datetime.utcfromtimestamp(0)
        self.status = None
        self.logs = {}
        try:
            self.refresh()
        except NotFoundException:
            self.active = False

    @property
    def chart_metadata_url(self):
        include_keys = ['start', 'end', 'executionStatus', 'executionEvents', 'subWorkflowMetadata']
        return (f'{url_for("cromwell_api.proxy")}/workflows/v1/{self.id}/metadata?expandSubWorkflows=true'
                f'&includeKeys={"&includeKeys=".join(include_keys)}')

    @property
    def abort_url(self):
        return url_for('api.cancel_workflow', workflow_id=self.id)

    @property
    def release_hold_url(self):
        return url_for('api.release_workflow_hold', workflow_id=self.id)

    def refresh(self):
        label_response = requests.get(f'{CROMWELL_URL}/api/workflows/v1/{self.id}/labels')
        if label_response.status_code == 404 or label_response.status_code == 400:
            raise NotFoundException(f'No job with id {self.id} found on jobserver.')
        label_response.raise_for_status()
        label_data = label_response.json()['labels']
        job_response = requests.get(f'{CROMWELL_URL}/api/workflows/v1/query?id={self.id}')
        job_data = job_response.json()['results'][0] if len(job_response.json()['results']) else {}
        job_data.update(label_data)
        self.owner_id = job_data['owner_id'] if 'owner_id' in job_data else None
        self.owner = User.query.filter_by(id=job_data['owner_id']).first() if 'owner_id' in job_data else None
        self.submission = datetime.strptime(job_data['submission'],
                                            '%Y-%m-%dT%H:%M:%S.%fZ') if 'submission' in job_data else None
        self.start = datetime.strptime(job_data['start'], '%Y-%m-%dT%H:%M:%S.%fZ') if 'start' in job_data else None
        self.end = datetime.strptime(job_data['end'], '%Y-%m-%dT%H:%M:%S.%fZ') if 'end' in job_data else None
        self.status = job_data['status'] if 'status' in job_data else None
        self.active = True

    def get_flattened_logs(self):
        self.get_logs()
        try:
            return {
                f'{key}.{inner_key}': inner_value
                for key, value in self.logs.items()
                for inner_key, inner_value in value.items()
            }
        except Exception:
            return {}

    def cancel(self):
        response = requests.post(f'{CROMWELL_URL}/api/workflows/v1/{self.id}/abort')
        return response.json()

    def resume(self):
        response = requests.post(f'{CROMWELL_URL}/api/workflows/v1/{self.id}/releaseHold')
        return response.json()

    def get_chart_metadata(self):
        include_keys = ['start', 'end', 'executionStatus', 'executionEvents', 'subWorkflowMetadata']
        url = f'{CROMWELL_URL}/api/workflows/v1/{self.id}/metadata' \
              f'?expandSubWorkflows=true&includeKeys={"&includeKeys=".join(include_keys)}'
        response = requests.get(url)
        return response.json()

    def get_logs(self):
        log_response = requests.get(f'{CROMWELL_URL}/api/workflows/v1/{self.id}/logs')
        try:
            self.logs = {
                key: {'stderr': open(value[0]['stderr']).read(), 'stdout': open(value[0]['stdout']).read()}
                for key, value in log_response.json()['calls'].items()}
        except:
            self.logs = log_response.json()


def get_workflows() -> List[Workflow]:
    """
    Get the jobs list from the Cromwell job server.
    :return:
    """
    url = f'{CROMWELL_URL}/api/workflows/v1/query'
    response = requests.get(url)
    response.raise_for_status()
    job_data = response.json()['results'] if 'results' in response.json() else []
    for entry in job_data:
        label_res = requests.get(f'{CROMWELL_URL}/api/workflows/v1/{entry["id"]}/labels')
        entry.update(label_res.json()['labels'])
    return [Workflow(entry['id']) for entry in job_data]


def get_workflow(workflow_id: str) -> Workflow:
    """
    Get information about a job running on the Cromwell job server.
    :param workflow_id:
    :return:
    """
    return Workflow(workflow_id)  # can throw not found


def start_workflow(source, on_hold, inputs, options=None, workflow_type_version=None, labels=None, dependencies=None):
    """
    Start a workflow exeuction on the Cromwell server
    :param source: Workflow as YAML string
    :param on_hold: Whether to start job in "on hold" status
    :param inputs: Inputs in YAML format, converted to JSON on submission
    :param options: Workflow options in YAML format, converted to JSON on submission
    :param workflow_type_version: Version of workflow type, which is either 'draft-2' or '1.0' because only WDL is supported
    :param labels: Workflow execution labels in YAML format, converted to JSON on submission
    :param dependencies: Contents of a zip file containing other dependencies
    :return:
    """
    options = options or {}
    labels = labels or {}
    labels['owner_id'] = current_user.id
    workflow_type_version = workflow_type_version or '1.0'
    yaml = YAML()
    inputs = yaml.load(inputs)
    files = {
        'workflowSource': StringIO(source),
        'workflowInputs': StringIO(json.dumps(inputs)),
        'labels': json.dumps(labels),
        'workflowOnHold': on_hold,
        'workflowOptions': json.dumps(options)
    }
    if dependencies is not None:
        files['workflowDependencies'] = dependencies
    files['workflowSource'].seek(0)
    files['workflowInputs'].seek(0)
    params = {'workflowType': 'WDL', 'workflowTypeVersion': workflow_type_version}
    url = f'{CROMWELL_URL}/api/workflows/v1'
    res = requests.post(url,
                        data=params,
                        files=files)
    res_text = ''
    try:
        res_text = res.text
        res.raise_for_status()
        return Workflow(res.json()['id'])
    except Exception:
        raise RuntimeError(f'Invalid response from job server. Is the server running? \n Response: {res_text}')


def cancel_workflow(user: User, workflow: Workflow) -> Dict[str, Any]:
    """
    Abort a running job on the Cromwell job server.
    :param user:
    :param workflow:
    :return:
    """
    workflow.refresh()
    if workflow.owner == user or user.admin:
        return workflow.cancel()
    raise AuthException(f'User {user.email} is not authorized to cancel job {workflow.id}')


def resume_workflow(user: User, workflow: Workflow) -> Dict[str, Any]:
    """
    Release the hold on a job on the Cromwell job server.
    :param user:
    :param workflow:
    :return:
    """
    workflow.refresh()
    if workflow.owner == user or user.admin:
        return workflow.resume()
    raise AuthException(f'User {user.email} is not authorized to resume job {workflow.id}')


def get_chart_metadata(workflow: Workflow) -> str:
    """
    Get a string containing a javascript object used to draw the Gannt chart for a job's timing
    :param workflow:
    :return:
    """
    workflow.refresh()
    return workflow.get_chart_metadata()


