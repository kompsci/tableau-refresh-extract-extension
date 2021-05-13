# global variables
import os

HYPER_TMP_DIR = os.path.abspath("./tmp")
CONFIG_DIR = os.path.abspath("./config")
DATA_DIR = os.path.abspath("./data")
DATA_STAGING_DIR = os.path.abspath("./data/staging")
LOG_DIR = os.path.abspath("./logs")
LOG_FILE_NAME = 'app.log'

AUDIT_DIR = os.path.abspath("./data/audit")
AUDIT_HYPER_FILE_NAME = "ActionAudit.hyper"

EMAIL_TEMPLATE = os.path.abspath("../utils/email_template.html")

