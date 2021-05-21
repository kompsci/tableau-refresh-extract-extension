import argparse
import os
import time

import pantab
import yaml
import logging
import sys
import googlemaps
import pandas as pd

sys.path.append(".")

import file_paths
from refresh_extract import tableau_rest_api_helper, utilities as utils

MAIN_LOGGER = logging.getLogger()

def main():

    parser = argparse.ArgumentParser(description='Tableau Extract Refresher for Google Places.')
    parser.add_argument('--config-file', '-c', required=False, default=f'{file_paths.CONFIG_DIR}/config.yaml',
                        help='configuration file for application')
    parser.add_argument('--server', '-s', required=False, help='Tableau Server Host URL')
    parser.add_argument('--site', '-t', required=False, help='Tableau Site ID')
    parser.add_argument('--username', '-u', required=False, help='Tableau Username')
    parser.add_argument('--password', '-p', required=False, help='Tableau Password')
    parser.add_argument('--access-token', '-x', required=False, help='Tableau Personal Access Token Id')
    parser.add_argument('--token-secret', '-y', required=False, help='Tableau Token Secret')
    parser.add_argument('--query-text', '-q', required=True, help='Google Places Search Query String')
    args = parser.parse_args()

    # Read configuration file
    try_env_vars = False

    try:
        with open(args.config_file) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
            # print(config)
    except Exception as e:
        print(file_paths.CONFIG_DIR)
        try_env_vars = True

    if try_env_vars:
        print('No configuration file, trying environment variables...')
        config = {}
        config['logging_level'] = 'INFO'
        config['server_url'] = os.getenv('TABLEAU_SERVER_URL')
        config['site_id'] = os.getenv('TABLEAU_SITE_ID')
        config['username'] = os.getenv('TABLEAU_USERNAME')
        config['password'] = os.getenv('TABLEAU_PASSWORD')
        config['access_token_id'] = os.getenv('TABLEAU_ACCESS_TOKEN_ID')
        config['access_token_secret'] = os.getenv('TABLEAU_ACCESS_TOKEN_SECRET')
        config['google_maps_api_key'] = os.getenv('GOOGLE_MAPS_API_ID')
        config['google_maps_api_secret'] = os.getenv('GOOGLE_MAPS_API_SECRET')
        config['target_datasource_name'] = os.getenv('TABLEAU_TARGET_DATASOURCE_NAME')
        config['target_project_name'] = os.getenv('TABLEAU_TARGET_PROJECT_NAME')


    if not config['server_url']:
        sys.exit("Program terminated - Configuration values could not be identified...")

    # check directories and create if not present
    utils.check_and_create_dir(file_paths.DATA_DIR)
    utils.check_and_create_dir(file_paths.LOG_DIR)
    utils.check_and_create_dir(file_paths.DATA_STAGING_DIR)

    # clean Data Staging directory
    utils.clean_directory(file_paths.DATA_STAGING_DIR)

    # logging
    console_logging_level = config["logging_level"]
    if not console_logging_level:
        console_logging_level = "INFO"
    else:
        console_logging_level = console_logging_level.upper()
    setup_logging(f'{file_paths.LOG_DIR}/{file_paths.LOG_FILE_NAME}', console_logging_level)

    ## Create an instance for the Source side
    tab_rest_api_helper = initialize_rest_api_helper(config, 'tab_rest_1', console_logging_level)

    execute_refresh(tab_rest_api_helper, config, args.query_text)


def embedded_start(query_text, socketio):
    # Read configuration file

    with open(f'{file_paths.CONFIG_DIR}/config.yaml') as file:
        config = yaml.load(file)

    # check directories and create if not present
    utils.check_and_create_dir(file_paths.DATA_DIR)
    utils.check_and_create_dir(file_paths.LOG_DIR)
    utils.check_and_create_dir(file_paths.DATA_STAGING_DIR)

    # clean Data Staging directory
    utils.clean_directory(file_paths.DATA_STAGING_DIR)

    # logging
    console_logging_level = config["logging_level"]
    if not console_logging_level:
        console_logging_level = "INFO"
    else:
        console_logging_level = console_logging_level.upper()
    setup_logging(f'{file_paths.LOG_DIR}/{file_paths.LOG_FILE_NAME}', console_logging_level)

    ## Create an instance for the Source side
    tab_rest_api_helper = initialize_rest_api_helper(config, 'tab_rest_1', console_logging_level)

    execute_refresh(tab_rest_api_helper, config, query_text, socketio)


def execute_refresh(rest_helper, config, query_text, socketio=None):

    TABLE_NAME = 'google_places'

    # get data
    MAIN_LOGGER.info(f'Refreshing Google Places Extract Based on Query: [{query_text}]...')
    if socketio:
        socketio.emit('push-message', f'Refreshing Extract Data Based on <br/> Query: [{query_text}]...', broadcast=True)
        socketio.emit('push-message', f'Querying Google Places API...', broadcast=True)
    extract_data_df = get_google_places_dataframe(config, query_text)

   # create hyper extract and publish
    hyper_file_path = os.path.join(file_paths.DATA_STAGING_DIR,f'GooglePlacesData.hyper')

    if socketio:
        socketio.emit('push-message', f'Creating New Hyper File...', broadcast=True)
    pantab.frame_to_hyper(extract_data_df, hyper_file_path, table=TABLE_NAME, table_mode='a')

    target_datasource_name = config['target_datasource_name']
    target_project_name = config['target_project_name']
    success = rest_helper.publish_hyper(hyper_file_path, target_datasource_name, target_project_name)
    if socketio:
        socketio.emit('push-message', f'Published Datasource as <br/>"{target_datasource_name}"...', broadcast=True)

    MAIN_LOGGER.info(f'Call to publish {target_datasource_name} datasource returned {success}')

    MAIN_LOGGER.info(f'Task Execution Completed')
    if socketio:
        socketio.emit('push-message', f'Extract Task Completed', broadcast=True)



def get_google_places_dataframe(config, querytext):

    gmaps = googlemaps.Client(config['google_maps_api_secret'])
    data = list()
    response = gmaps.places(query=querytext)
    data.extend(response['results'])
    while 'next_page_token' in response:
        time.sleep(2)  #delay is mandatory - API bug
        response = gmaps.places(query=querytext, page_token=response['next_page_token'])
        data.extend(response['results'])

    df = pd.json_normalize(data)
    df = df.drop(columns=['photos', 'types'])
    df['query_text'] = querytext
    extract_data_df = df.fillna(value={'opening_hours.open_now': False, 'permanently_closed': False, 'price_level' : 0.00})
    return extract_data_df


def initialize_rest_api_helper(cfg, instance_name, logging_level):
    username = cfg["username"]
    password = cfg["password"]
    access_token = cfg["access_token_id"]
    token_secret = cfg["access_token_secret"]
    server_url = cfg["server_url"]
    site_id = cfg["site_id"] if cfg["site_id"] is not None else ""
    # determine authentication method
    useUsername = True if (username and password) else False
    useAccessToken = True if (access_token and token_secret) and not useUsername else False
    if (cfg and server_url and (useAccessToken or useUsername)):
        if useAccessToken:
            MAIN_LOGGER.info(f'Authenticating with access token id: {access_token}')
            rest_helper = tableau_rest_api_helper.TableauRestAPIHelper(server_url,
                                                                       site_id,
                                                                       instance_name=instance_name,
                                                                       access_token=access_token,
                                                                       token_secret=token_secret,
                                                                       logging_level=logging_level,
                                                                       http_debug=False)

        if useUsername:
            MAIN_LOGGER.info(f'Authenticating with username: {username}')
            rest_helper = tableau_rest_api_helper.TableauRestAPIHelper(server_url,
                                                                       site_id,
                                                                       instance_name=instance_name,
                                                                       username=username,
                                                                       password=password,
                                                                       logging_level=logging_level,
                                                                       http_debug=False)

    else:
        MAIN_LOGGER.error("Authentication Details Missing From Config File")
        sys.exit("Program terminated - Execution Unsuccessful")

    rest_helper.list_server_info()
    return rest_helper


def setup_logging(log_file_name, console_logging_level):
    '''Configure console logging handler and file logging handler'''

    # create file handler
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # fh = RotatingFileHandler(log_file_name, maxBytes=8000000, backupCount=10)  # roll at ~8MB
    fh = logging.FileHandler(log_file_name, 'w+')
    fh.setFormatter(fh_formatter)

    fh.setLevel(logging.DEBUG)

    # create console handler
    ch_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    # ch_formatter = logging.Formatter('# %(asctime)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(ch_formatter)
    ch.setLevel(console_logging_level)

    MAIN_LOGGER = logging.getLogger()
    MAIN_LOGGER.setLevel(console_logging_level)
    MAIN_LOGGER.addHandler(fh)
    MAIN_LOGGER.addHandler(ch)

    utils.log_app_start()
    MAIN_LOGGER.info(
        f'Console Logging Level is set to {console_logging_level}. Log File Logging Level is always set to DEBUG')


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print(f"Unhandled exception: exc_info=({exc_type}, exc_value={exc_value}, exc_traceback={exc_traceback}")

# MAIN ENTRY POINT

sys.excepthook = handle_unhandled_exception

if __name__ == "__main__":
    main()
