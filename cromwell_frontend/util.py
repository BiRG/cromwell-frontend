import traceback

from flask import render_template, redirect, url_for, request, jsonify
import datetime

from .exceptions import NotFoundException, AuthException, LoginError
from .page_data import PageData
from .config import LOG_FILE


def handle_exception_browser(e):
    print('handle_exception_browser')
    if isinstance(e, NotFoundException):
        log_exception(404, e)
        error_msg = str(e)
        error_title = '404 Not Found'
        return render_template('error.html', page_data=PageData('404 Not Found'), fa_type='fa-question-circle', alert_class='alert-warning', error_msg=error_msg, error_title=error_title), 404
    if isinstance(e, AuthException):
        log_exception(403, e)
        error_msg = str(e)
        error_title = '403 Forbidden'
        return render_template('error.html', page_data=PageData('403 Forbidden'), fa_type='fa-ban', alert_class='alert-secondary', error_msg=error_msg, error_title=error_title), 403
    if isinstance(e, LoginError):
        return redirect(url_for('login', next=request.url))
    error_msg = str(e)
    if error_msg.lower() == 'not logged in':
        return redirect(url_for('login'))
    tb = traceback.format_exc()
    error_title = '500 Internal Server Error'
    log_exception(500, e, tb)
    return render_template('error.html', fa_type='fa-exclamation-circle', alert_class='alert-danger', tb=tb, error_msg=error_msg,
                           error_title=error_title, page_data=PageData('500 Internal Server Error')), 500


def handle_exception(e):
    if isinstance(e, NotFoundException):
        log_exception(404, e)
        return jsonify({'message': str(e)}), 404
    if isinstance(e, AuthException):
        log_exception(403, e)
        return jsonify({'message': str(e)}), 403
    if isinstance(e, LoginError):
        log_exception(401, e)
        return jsonify({'message': str(e)}), 401
    tb = traceback.format_exc()
    log_exception(500, e, tb)
    return jsonify({'message': str(e), 'traceback': tb}), 500


def log_exception(status, e, tb=""):
    with LOG_FILE.open('a') as log_file:
        log_file.write(f'\n{datetime.datetime.now().replace(microsecond=0).isoformat(" ")} [{status}]: {str(e)}\n')
        if tb:
            log_file.write(f'Traceback: \n{tb}\n')
