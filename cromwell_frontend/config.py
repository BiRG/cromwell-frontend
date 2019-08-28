"""
  Edit values to change your configuration
  Environment variables with the same name override these options.
  You can edit this file manually, or create a .sh file with exports and source it before running

  A note on database configuration:
  The full connection string has the format 'dialect+driver://user:password@host:port/database'.
  See (https://docs.sqlalchemy.org/en/13/core/engines.html) for more details.

  If you followed the Cromwell documentation for setting up persistent storage, you most likely set up a MySQL or
  PostgreSQL database.
"""

import os
from pathlib import Path
import grp
from typing import Optional, List

HOST_IP: str = '0.0.0.0'  # 0.0.0.0 to broadcast publicly, 127.0.0.1 for loopback (this machine only)
CROMWELL_URL: str = 'http://localhost:8000'  # address where the Cromwell API can be reached.
WORKFLOW_DEFINITION_DIR: Path = Path('/home/cromwell/workflows')  # address to store workflow definitions managed by this service
SECRET: str = 'KIZXUxGPusmR48vD8Eni5KcfJX91iDju'
BRAND: str = 'localhost'
BOOTSTRAP_CSS_URL: str = 'https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/flatly/bootstrap.min.css'
LOG_FILE: Path = (Path(__file__).parent.parent / 'error.log').resolve()
WOMTOOL_JAR: str = '/usr/local/bin/womtool-45.jar'
CODEMIRROR_THEME_CSS: str = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.48.4/theme/idea.min.css'  # you can also always select 'default'
CODEMIRROR_THEME_NAME: str = 'default'
AUTHORIZED_GROUPS: Optional[grp.struct_group] = None  # PAM groups users must be in at least one of to use this service.
ADMIN_GROUPS: Optional[List[grp.struct_group]] = [grp.getgrnam('admin'), grp.getgrnam('sudo')]
DB_URI: str = 'postgresql+psycopg2://cromwell:7u8oqadixrxmIhfgKWXDTDPz0AJVxCJX@localhost:5432/cromwell_frontend'

# Overwrite options above if environment variable exists
HOST_IP = os.environ['HOST_IP'] if 'HOST_IP' in os.environ else HOST_IP
CROMWELL_URL = os.environ['CROMWELL_URL'] if 'CROMWELL_URL' in os.environ else CROMWELL_URL
WORKFLOW_DEFINITION_DIR = Path(os.environ['WORKFLOW_DEFINITION_DIR']) \
    if 'WORKFLOW_DEFINITION_DIR' in os.environ else WORKFLOW_DEFINITION_DIR
SECRET = os.environ['SECRET'] if 'SECRET' in os.environ else SECRET
BRAND = os.environ['BRAND'] if 'BRAND' in os.environ else BRAND
BOOTSTRAP_CSS_URL = os.environ['BOOTSTRAP_CSS_URL'] if 'BOOTSTRAP_CSS_URL' in os.environ else BOOTSTRAP_CSS_URL
LOG_FILE = Path(os.environ['LOG_FILE']) if 'LOG_FILE' in os.environ else LOG_FILE
WOMTOOL_JAR = os.environ['WOMTOOL_JAR'] if 'WOMTOOL_JAR' in os.environ else WOMTOOL_JAR
CODEMIRROR_THEME_CSS = os.environ['CODEMIRROR_THEME_CSS'] if 'CODEMIRROR_THEME_CSS' in os.environ else CODEMIRROR_THEME_CSS
CODEMIRROR_THEME_NAME = os.environ['CODEMIRROR_THEME_NAME'] if 'CODEMIRROR_THEME_NAME' in os.environ else CODEMIRROR_THEME_NAME
AUTHORIZED_GROUPS = [grp.getgrnam(group) for group in os.environ['AUTHORIZED_GROUPS'].split(',')] if 'AUTHORIZED_GROUPS' in os.environ else AUTHORIZED_GROUPS
ADMIN_GROUPS = [grp.getgrnam(group) for group in os.environ['ADMIN_GROUPS'].split(',')] if 'ADMIN_GROUPS' in os.environ else AUTHORIZED_GROUPS
DB_URI = os.environ['DB_URI'] if 'DB_URI' in os.environ else DB_URI
