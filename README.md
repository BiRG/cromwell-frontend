# Cromwell-Frontend
A web frontend for the [Cromwell](https://github.com/broadinstitute/Cromwell)
workflow executor.

## Features
### PAM Authentication
Any user which can log into the host can log into the service with the 
same username and password they use to authenticate to the host. Access 
can be restricted only to a particular POSIX group. Administrator access 
is given to users in the `admin` or `sudo` group, or another specified group.

### Workflow Definition Editor
This service allows users to create and edit [WDL](http://www.openwdl.org/)
workflow definitions from the browser. 

![workflow definition editor screnshot](.readme_images/workflow_definition_editor.png)

Workflows are validated using womtool on saving.

![workflow validation screenshot](.readme_images/validation.png)

### Workflow Execution Control
![workflow list screenshot](.readme_images/workflow_list.png)

Users may submit and control workflows with inputs, options and labels specified in
YAML format.

![workflow submission screenshot](.readme_images/workflow_submission.png)

![workflow progress screenshot](.readme_images/workflow_progress.png)



## Requirements
The python packages in `requirements.txt`, a DBAPI driver for your database
of choice and a web server (see below)

### Cromwell in Server Mode
Cromwell should be running in server mode, with a
[database](https://cromwell.readthedocs.io/en/stable/Configuring/#database)
to persist workflow information. You can use a different database on the
same engine for this front end. The Cromwell documentation includes
instructions for MySQL (which also work for MariaDB) and PostgreSQL.

### Web Server
`cromwell_frontend/app.py` contains a Flask application, which you can
serve with the flask development server, gunicorn, or uwsgi (see 
`uwsgi.ini`). The `start.sh` scripts serves the page via uwsgi with the
configuration options in `uwsgi.ini`, which "mounts" the application at 
`/cromwell`.

#### Using the uwsgi protocol
You can serve this service over a socket using the uwsgi protocol
instead of serving over a port. You can then serve this service over a
proxy server using
[Apache](https://uwsgi-docs.readthedocs.io/en/latest/Apache.html),
[Nginx](https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html) or
[Lighttpd](https://uwsgi-docs.readthedocs.io/en/latest/Lighttpd.html).
See `uwsgi_socket.ini` for an example configuration. You should probably
configure your firewall to only allow access to the uwsgi port from the
proxy.

### DBAPI Driver
This project uses SQLAlchemy and requires a DBAPI driver that SQLAlchemy
supprots to talk to your database. See [the SQLAlchemy documentation](https://docs.sqlalchemy.org/en/13/core/engines.html)
for more information.

### Virtualenvs
If you're using the `start.sh` script, you can pass additional arguments
to `uwsgi`. To use a virtualenv: `./start.sh -H /path/to/venv`.

## Configuration
`config.py` contains configuration options. You will probably need to 
change at least `DB_URI` to match your Cromwell configuration. You can 
also change any of the values in config.py by setting environment variables.

The following variables can be changed:

#### `HOST_IP`
The address to broadcast the service on. If set to `'0.0.0.0'`, the
service will be broadcast publicly. If set to `'127.0.0.1'`, the service
will be accessible only to the host.

#### `CROMWELL_URL`
The full URL where the Cromwell API can be reached. By default this is
`'http://localhost:8000'` 

#### `WORKFLOW_DEFINITION_DIR`
Directory in which to store workflow definitions.

#### `SECRET`
A secret key used to encrypt authorization tokens.

#### `BRAND`
A string which will be placed in the navbar.

#### `BOOTSTRAP_CSS_URL`
The url for the `bootstrap.min.css` file which contains styles for the
[Bootstrap](https://getbootstrap.com/) framework used by this service.
The default is the [Flatly theme](https://bootswatch.com/flatly/) from
[Bootswatch](https://bootswatch.com).

#### `LOG_FILE`
The location of the log file. The default is `error.log` in this
directory.

#### `WOMTOOL_JAR`
The location of `womtool-xx.jar`

#### `CODEMIRROR_THEME_CSS`
The URL of an additional theme for the
[CodeMirror](https://codemirror.net/) code editor. Additional themes can
be found [here](https://cdnjs.com/libraries/codemirror). Theme CSS files
are found in the `theme` directory (for example,
`https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.48.4/theme/idea.min.css`)
A demo of the various themes can be found
[here](https://codemirror.net/demo/theme.html)

#### `CODEMIRROR_THEME_NAME`
The name of the theme contained in `CODEMIRROR_THEME_CSS` (for example,
`'idea'` in the example given above.

#### `AUTHORIZED_GROUPS`
A list of POSIX groups a user must be a member of at least one of to
login to the service. In `config.py` this is a list of
`grp.struct_group`. In an environment variable, they are specified as a
list of groups separated by commas (*e.g.* `'cromwell,jobserver'`). By
default, all users are allowed to login to the service.

#### `ADMIN_GROUPS`
A list of POSIX groups a user must be a member of at least one of to
have administrator access to the service (the ability to edit records
owned by all users). In `config.py` this is a list of
`grp.struct_group`. In an environment variable the groups are specified
as a list of group names separated by commas (*e.g.*
`'administrator,manaager'`. By default, users in `sudo` and `admin` have
administrator access on the service.

#### `DB_URI`
The connection string for a SQL database. The full URI has the format
`'dialect+driver://user:password@host:port/database'`. See the
[SQLAlchemy documentation](https://docs.sqlalchemy.org/en/13/core/engines.html)
for more information.

