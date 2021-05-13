import errno
import logging
import os
import shutil
import typing
import zipfile
from datetime import datetime
from os.path import basename, normpath
from pathlib import Path
from tableauserverclient import ServerResponseError

LOGGER = logging.getLogger()

TableauFileListObject = typing.NamedTuple('TableauFileListObject', [('tableau_archive_file_name', str),
                                                                    ('extracted_dir', str),
                                                                    ('list_file_paths', str)])


def silent_remove(file_path):
    """Remove file if exists

    Args:
        file_path (str): Path to File

    """
    try:
        LOGGER.debug(f'Silently Removing {file_path}')
        os.remove(file_path)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


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


def extract_zip_archive(zip_file_path):
    """Unzips a zip file. Zip File DOES NOT need to have .zip extension.

    Args:
        zip_file_path ():

    Returns:
        Path to Extracted Directory
    """

    containing_dir, zip_filename = os.path.split(zip_file_path)
    file_without_extension = Path(zip_filename).stem
    extract_dir = os.path.join(containing_dir, file_without_extension)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        zip_ref.close()

    return extract_dir


def package_tableau_archive(source_dir: str, dest_dir: str):
    """Create a packaged Tableau Datasource (TDSX) or Workbook File (TWBX)
        This utility automatically determines the extension based on the contents of the file

    Args:
        source_dir (str): Path to the parent directory that contains the files
            to create the packaged datasource or workbook.
        dest_dir (str): Path to the parent directory that will store
            the packaged datasource or workbook file (tdsx or twbx file)

    Returns:
        path to packaged archive file

    """

    # get package_name
    package_name = basename(normpath(source_dir))

    path_to_zip_file = os.path.join(dest_dir, f"{package_name}.zip")
    zip_runner = zipfile.ZipFile(path_to_zip_file, "w", zipfile.ZIP_DEFLATED)
    abs_source = os.path.abspath(source_dir)

    is_tdsx = False
    for dirname, _, files in os.walk(source_dir):
        for filename in files:
            if 'tds' in filename:
                is_tdsx = True
            if filename != ".gitkeep":
                abs_name = os.path.abspath(os.path.join(dirname, filename))
                arc_name = abs_name[len(abs_source) + 1:]
                zip_runner.write(abs_name, arc_name)

    zip_runner.close()

    if is_tdsx:
        path_to_dest_file = os.path.join(dest_dir, f"{package_name}.tdsx")
        os.rename(path_to_zip_file, path_to_dest_file)
    else:
        path_to_dest_file = os.path.join(dest_dir, f"{package_name}.twbx")
        os.rename(path_to_zip_file, path_to_dest_file)

    LOGGER.info(f'Packaged "{source_dir}" as "{path_to_dest_file}"')

    return path_to_dest_file


def find_all_files_by_extension(directory_path, extension):
    """Finds All Files within a directory path matching the extension

    Args:
        directory_path (str): Directory Path
        extension (str): Extension to look for

    Returns:
        List of File Paths

    """
    file_paths = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))
    return file_paths


def get_now_as_string():
    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    return dt_string


def get_formatted_error(msg: str, e: ServerResponseError):
    return f'{msg} || Error Code {e.code} | {e.summary} | {e.detail}'


def confirm_value(name, value):
    if value is None:
        raise TypeError(f"{name} is a required value. It cannot be equal to None.")
    return value


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


# region REGION: Hyper Utils

def unzip_and_find_files(file_store_dir, filename, file_extension=".hyper"):
    """
    For a given directory and filename, extract zip file and return a record containing
    the filename, extracted directory and list of file paths within the
    extracted directory identifying files according to file extension

    Args:
        file_extension:
        file_store_dir:
        filename:

    Returns:
        TableauFileListObject named tuple

    """
    zip_file_path = os.path.join(file_store_dir, filename)
    dest_dir = extract_zip_archive(zip_file_path)
    hyper_files = find_all_files_by_extension(dest_dir, file_extension)
    record = TableauFileListObject(filename, dest_dir, hyper_files)
    return record


def process_hyper_files(file_store_dir):
    """
    For a given directory
        1) Unzip All TWBX and TDSX archives
        3) Return a list of all .hyper files located in the archives. This is a list of file paths

    Args:
        file_store_dir:

    Returns:
        List of file paths to all .hyper files within the config.file_store_dir
    """
    hyper_file_list_objects = []

    for filename in os.listdir(file_store_dir):
        file_path = os.path.join(file_store_dir, filename)
        if os.path.isdir(file_path):
            # skip directories
            continue
        if ".twbx" in filename:
            d = unzip_and_find_files(file_store_dir, filename, ".hyper")
            hyper_file_list_objects.append(d)
        elif ".tdsx" in filename:
            d = unzip_and_find_files(file_store_dir, filename, ".hyper")
            hyper_file_list_objects.append(d)
        else:
            # ignore files non-tableau-datasource files
            pass

    return hyper_file_list_objects

# endregion
