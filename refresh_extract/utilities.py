import errno
import logging
import os
import shutil
from datetime import datetime
from tableauserverclient import ServerResponseError

LOGGER = logging.getLogger()


def clean_directory(directory_path: str):
    """Remove all files and subdirectories within a parent directory.

    Args:
        directory_path (str): Path to parent directory.

    """
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename != ".gitkeep":

            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def check_and_create_dir(directory_path):
    """Check if directory exists and if it does not then create it.
        This is done by attempting to create the directory and squashing
        the OS error if it already exists

    Args:
        directory_path (str): Path to directory to check

    """
    try:
        os.makedirs(directory_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def get_now_as_string():
    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    return dt_string


def get_formatted_error(msg: str, e: ServerResponseError):
    return f'{msg} || Error Code {e.code} | {e.summary} | {e.detail}'


def log_app_start():
    """Format the log message for start of application."""

    LOGGER.info("")
    LOGGER.info("#######################################")
    LOGGER.info("#                                     #")
    LOGGER.info("#     Tableau Extract Refresher       #")
    LOGGER.info("#                                     #")
    LOGGER.info("#######################################")
    LOGGER.info("")
    LOGGER.info("    Tableau Professional Services  ")
    LOGGER.info("       Run Date: %s", get_now_as_string())
    LOGGER.info("")
    LOGGER.info("#######################################")



