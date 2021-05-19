"""
Tableau REST API Helper
Makes use of Tableau Server Client Python library to interface with Tableau REST API
Manages state - initiates one REST API connection per instance of the class
"""
import logging
import os
from http.client import HTTPConnection
import tableauserverclient as TSC
from tableauserverclient import ServerResponseError

from refresh_extract import utilities as utils


class TableauRestAPIHelper:
    """API Helper Class for the Tableau REST API via the Tableau Server Client library

    Args:
        _server_url: Tableau Server URL
        _site_content_url: Site Namespace URL
        username (kwarg): Specify username for authentication
        password (kwarg): Specify password for authentication
        access_token (kwarg): Specify access token ID for authentication
        token_secret (kwarg): Specify token secret for token
        http-debug (kwarg): True for verbose HTTPConnection logging of request/response

    """

    def __init__(self, _server_url, _site_content_url='', **kwargs):

        # instance name
        instance_name = kwargs.get("instance_name", self.__hash__())

        # configure logging
        self.logger = logging.getLogger(f'{self.__class__.__name__} (Instance: {instance_name})')

        http_verbose_debug = kwargs.get("http_debug", False)
        self.__set_secondary_logging(http_verbose_debug)

        # grab authentication details
        self.server_url = _server_url
        self.site_content_url = _site_content_url

        if kwargs.get("username"):
            self.use_auth_token = False
            self.username_or_application_id = kwargs["username"]
            self.secret = kwargs["password"]
        else:
            self.use_auth_token = True
            self.username_or_application_id = kwargs["access_token"]
            self.secret = kwargs["token_secret"]

        #state variables
        self.all_workbooks = None
        self.all_datasources = None
        self.all_views = None
        self.all_projects = None
        self.all_users = None
        self.all_flows = None
        self.all_tasks = None

        self.__create_session_and_signin()

    def __del__(self):
        try:
            if self.tsclient and self.tsclient.is_signed_in():
                #print(self.tsclient.auth_token)
                self._signout()
        except:
            pass


    # region ----Public Methods-----

    def list_server_info(self):
        # Server info and methods
        server_info = self.tsclient.server_info.get()
        server_version = server_info.product_version
        api_version = server_info.rest_api_version
        build_version = server_info.build_number
        info = "SERVER INFO: Rest API Endpoint {} Server Version {} with API Version {}, build {}".format(
            self.server_url, server_version, api_version, build_version)
        self.logger.info(info)

    def list_workbooks(self):
        workbooks, pagination_item = self.tsclient.workbooks.get()
        for workbook in workbooks:
            self.logger.info(f"Workbook Name: {workbook.name} Workbook LUID: {workbook.id}")

    def list_projects(self):
        projects, pagination_item = self.tsclient.projects.get()
        for project in projects:
            self.logger.info(f"Project Name: {project.name} Project LUID: {project.id}")


    def download_datasource(self, datasource_name, download_dir, project_name=None, _include_extract=False, _cleanup_after=True):
        '''Downloads Tableau Published Datasource

        Args:
            datasource_name (str): Name of Datasource
            download_dir (str): Directory where Datasource is located
            _include_extract (bool): Include Data Extract
            _cleanup_after (bool): Remove .TDSX File Once operation completed
        Returns:
            Path to TDS File
        '''


        staging_dir = os.path.abspath(download_dir)

        try:
            # Get luid of the datasource
            datasource_item = self.__get_datasource_item(datasource_name, project_name)
            self.logger.info(f'Downloading Datasource Name : {datasource_name} | Datasource LUID: {datasource_item.id}')
        except LookupError as e:
            self.logger.error(e)
            return False

        # download via TSC
        try:
            path_to_downloaded_file = self.tsclient.datasources.download(datasource_item.id, staging_dir,
                                                                   include_extract=_include_extract)
        except ServerResponseError as e:
            self.logger.error(utils.get_formatted_error('Unable to Download Datasource', e))

        self.logger.info(f'Downloaded Datasource "{datasource_name}" to "{path_to_downloaded_file}')



        action_log = 'Downloaded Tableau Published Datasource File and Extracted TDS File'

        return path_to_downloaded_file

    def publish_hyper(self, source_hyper_file_path, dest_datasource_name, dest_project_name, overwrite=True):

        '''Publish Single File Hyper as Datasource to Tableau Server

        Args:
            source_hyper_file_path (str): File path to Hyper file
            dest_datasource_name (str): Destination Datasource Name
            dest_project_name (str): Destination Project Name
            overwrite (bool): (Optional) Overwite Datasource?

        Returns:
            True if the command is successful.

        '''

        # Check Method Parameters

        if overwrite:
            mode = TSC.Server.PublishMode.Overwrite
        else:
            mode = TSC.Server.PublishMode.CreateNew

        try:
            # Get Project LUID
            project_luid = self.__get_project_luid(dest_project_name)
        except LookupError as e:
            self.logger.error(e)
            return False


        # Create Dest Datasource Item
        dest_datasource_item = TSC.DatasourceItem(name=dest_datasource_name, project_id=project_luid)

        self.logger.info(f'Publishing datasource "{source_hyper_file_path}" as "{dest_datasource_name}" to Tableau Server')

        # call the publish method with the datasource item
        try:
            published_ds_item = self.tsclient.datasources.publish(dest_datasource_item, source_hyper_file_path, mode)
        except ServerResponseError as e:
            self.logger.error(utils.get_formatted_error('Unable to Publish Datasource', e))
            return False
        except Exception as e:
            self.logger.exception(e)
            return False


        action_msg = f'Published Hyper File as Datasource "{published_ds_item.name}" to Project "{dest_project_name}"'


        self.logger.info(action_msg)

        return True


    # endregion

    #region ----Private Class Methods-----


    def __set_secondary_logging(self, http_debug=False):
        tsc_logger = logging.getLogger('tableau')
        requests_log = logging.getLogger("requests.packages.urllib3")

        if (self.logger.level >= logging.DEBUG):
            tsc_logger.setLevel(self.logger.level)
            requests_log.setLevel(self.logger.level)
        else:
            tsc_logger.setLevel(logging.ERROR)
            requests_log.setLevel(logging.ERROR)


        if http_debug:
            HTTPConnection.debuglevel = 1
        else:
            HTTPConnection.debuglevel = 0

    def __create_session_and_signin(self):

        if self.use_auth_token:
            tableau_auth = TSC.PersonalAccessTokenAuth(self.username_or_application_id, self.secret,
                                                       self.site_content_url)
            self.tsclient = TSC.Server(self.server_url, use_server_version=True)
            self.tsclient.auth.sign_in(tableau_auth)
        else:
            tableau_auth = TSC.TableauAuth(self.username_or_application_id, self.secret, self.site_content_url)
            self.tsclient = TSC.Server(self.server_url, use_server_version=True)
            self.tsclient.auth.sign_in(tableau_auth)

        # enforce that the REST API version matches the server version
        self.tsclient.use_server_version()
        #self.tsclient.version = "3.4"

        if (self.__get_restapi_token()):
            self.logger.debug("Authenticated and obtained REST API Token...")

    def _signout(self):
        try:
            self.logger.debug("Signing out of TS session...")
            self.tsclient.auth.sign_out()
        except:
            self.logger.debug("Unable to signout of TS session...")

    def __get_restapi_token(self):
        return self.tsclient.auth_token

    def __make_filter(self, **kwargs):
        options = TSC.RequestOptions()
        for item, value in kwargs.items():
            name = getattr(TSC.RequestOptions.Field, item)
            options.filter.add(TSC.Filter(name, TSC.RequestOptions.Operator.Equals, value))
        return options

    def __get_workbook_by_name_filter(self, name):
        request_filter = self.__make_filter(Name=name)
        workbooks, _ = self.tsclient.workbooks.get(request_filter)
        try:
            assert len(workbooks) == 1
            return workbooks.pop()
        except AssertionError:
            raise LookupError(f'Workbook with the specified name was not found: {name}')


    def __get_datasource_by_name_filter(self, name):
        request_filter = self.__make_filter(Name=name)
        datasources, _ = self.tsclient.datasources.get(request_filter)
        try:
            assert len(datasources) == 1
            return datasources.pop()
        except AssertionError:
            raise LookupError(f'Datasource with the specified name was not found: {name}')

    def __get_schedule_by_name(self,name):
        schedules = [x for x in TSC.Pager(self.tsclient.schedules) if x.name == name]
        try:
            assert len(schedules) == 1
            return schedules.pop()
        except AssertionError:
            raise LookupError(f'Schedule with the specified name was not found: {name}')


    def __get_project_luid(self, project_name):
        luid = None

        if not self.all_projects:
            self.all_projects = list(TSC.Pager(self.tsclient.projects))

        for pj in self.all_projects:
            if pj.name == project_name:
                luid = pj.id
        if luid:
            return luid
        else:
            raise LookupError(f'Project with the specified name was not found: {project_name}')

    def __get_job_item(self, job_id):
        return self.tsclient.jobs.get_by_id(job_id)

    def __get_user_item(self, user_name):
        item = None

        if not self.all_users:
            self.all_users = list(TSC.Pager(self.tsclient.users))

        for user in self.all_users:
            if user.name == user_name:
                item = user

        if item:
            return item
        else:
            raise LookupError(f'User with the specified name was not found: {user_name}')

    def __get_workbook_item(self, workbook_name, project_name=None):
        workbook_item = None
        items_list = list()

        if not self.all_workbooks:
            self.all_workbooks = list(TSC.Pager(self.tsclient.workbooks))

        for wb in self.all_workbooks:
            if project_name:
                if wb.project_name == project_name and wb.name == workbook_name:
                    workbook_item = wb
            else:
                if wb.name == workbook_name:
                    workbook_item = wb
                    items_list.append(wb)

        if len(items_list) > 1:
            raise LookupError(f'More than one workbook matched to: {workbook_name}. Please specify Project Name for Distinct Match')

        if workbook_item:
            return workbook_item
        else:
            raise LookupError(f'Workbook with the specified name was not found: {workbook_name}')


    def __get_datasource_item(self, datasource_name, project_name=None):
        item = None
        items_list = list()


        if not self.all_datasources:
            self.all_datasources = list(TSC.Pager(self.tsclient.datasources))

        for ds in self.all_datasources:
            if project_name:
                if ds.project_name == project_name and ds.name == datasource_name:
                    item = ds
            else:
                if ds.name == datasource_name:
                    item = ds
                    items_list.append(ds)

        if len(items_list) > 1:
            raise LookupError(f'More than one datasource matched to: {datasource_name}. Please specify Project Name for Distinct Match')

        if item:
            return item
        else:
            raise LookupError(f'Datasource with the specified name was not found: {datasource_name}')

    def __get_view_item(self, view_name, workbook_name, project_name=None):

        if not self.all_views:
            self.all_views = list(TSC.Pager(self.tsclient.views))

        if self.all_views  and len(self.all_views )>0:
            if workbook_name:
                workbook_item = self.__get_workbook_item(workbook_name, project_name)
                for view_item in self.all_views :
                    if workbook_item.id == view_item.workbook_id and view_item.name == view_name:
                        return view_item
            else:
                return None
        else:
            raise LookupError('View with the specified name was not found. {view_name}')

    def __get_flow_item(self, flow_name, project_name=None):
        item = None
        items_list = list()

        if not self.all_flows:
            self.all_flows = list(TSC.Pager(self.tsclient.flows))

        for fl in self.all_flows:
            if project_name:
                if fl.project_name == project_name and fl.name == flow_name:
                    item = fl
            else:
                if fl.name == flow_name:
                    item = fl
                    items_list.append(fl)

        if len(items_list) > 1:
            raise LookupError(f'More than one flow matched to: {flow_name}. Please specify Project Name for Distinct Match')

        if item:
            return item
        else:
            raise LookupError(f'Prep Flow with the specified name was not found: {flow_name}')

    def get_flow_task_items(self):
        item = None
        items_list = list()


        if not self.all_tasks:
            self.all_tasks, pagination_item = self.tsclient.tasks.get_flow_tasks()
            self.logger.debug(f'There are {pagination_item.total_available} runFlow tasks on site')
            print([task.id for task in self.all_tasks])

        for tsk in self.all_tasks:
            items_list.append(tsk)

        if item:
            return item
        else:
            raise LookupError(f'Task List could not be queried')

    #endregion













