from flask import request, Blueprint, jsonify
from flask_login import login_required
import requests
from cromwell_frontend.config import CROMWELL_URL
from cromwell_frontend.util import handle_exception

cromwell_api = Blueprint('cromwell_api', __name__, url_prefix='/cromwell_api')


@cromwell_api.route('/', defaults={'path': ''})
@cromwell_api.route('/<path:path>')
@login_required
def proxy(path):
    """
    h/t to user Evan at (https://stackoverflow.com/questions/6656363/proxying-to-another-web-service-with-flask)
    """
    try:
        url = f'{CROMWELL_URL}/api/{path}'
        res = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key not in {'Host', 'Authorization'}},
            data=request.get_data(),
            cookies=request.cookies,  # probably not used by Cromwell, but for completion
            allow_redirects=False
        )
    except requests.exceptions.RequestException as e:
        return handle_exception(e)
    try:
        contents = res.json()
    except ValueError as _:
        return jsonify({}), res.status_code
    return jsonify(contents), res.status_code  # response from Cromwell is always type json
