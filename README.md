# Cromwell-Frontend
A web frontend for the [Cromwell](https://github.com/broadinstitute/Cromwell)
workflow executor.

## Features
* Authentication with local user accounts.
* Edit WDL workflow definitions.
* Submit and manage workflows on Cromwell server.

## Requirements and Configuration
The python packages in `requirements.txt`, the DBAPI driver for your database
of choice and a web server (see below)

### Web Server
`cromwell_frontend/app.py` contains a Flask application, which you can
serve with the flask development server, gunicorn, or uwsgi (see 
`uwsgi.ini`). The `start.sh` scripts serves the page via uwsgi with the
configuration options in `uwsgi.ini`, which "mounts" the application at 
`/cromwell`.

### DBAPI Driver
This project uses SQLAlchemy and requires a DBAPI driver that SQLAlchemy
supprots to talk to your database. See [this link](https://docs.sqlalchemy.org/en/13/core/engines.html)
for more information.

### Virtualenvs
If you're using the `start.sh` script, you can pass additional arguments
to `uwsgi`. To use a virtualenv: `./start.sh -H /path/to/venv`.

### `config.py`
`config.py` contains configuration options. You will probably need to 
change at least `DB_URI` to match your Cromwell configuration.

