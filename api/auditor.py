'''
Decorators and other functions for Auditing
'''
import os
import logging
import typing
import pandas as pd
from tableauserverclient import ServerResponseError

from utils import utilities as utils
from api.tableau_hyper_api_helper import TableauHyperAPIHelper
from my_console_app import file_paths

AUDIT_LOGGER = logging.getLogger('AUDIT')
AUDIT_TABLE_NAME = 'Extract'


OBJECT_TYPE_WORKBOOK = 'TableauWorkbook'
OBJECT_TYPE_DATASOURCE = 'TableauDatasource'
OBJECT_TYPE_VIEW = 'TableauView'
OBJECT_TYPE_HYPER = 'TableauHyperExtract'
OBJECT_TYPE_FLOW = 'TableauPrepFlow'

AuditAction = typing.NamedTuple('AuditAction', [('date', str),
                                                   ('site_content_url', str),
                                                   ('site_luid', str),
                                                   ('project_name', str),
                                                   ('project_luid', str),
                                                   ('object_name', str),
                                                   ('object_luid', str),
                                                   ('object_type', str),
                                                   ('owner_name', str),
                                                   ('owner_luid', str),
                                                   ('file_path', str),
                                                   ('action_type', str),
                                                   ('action_log', str)
                                                   ])


class Auditor():
    _instance = None
    _audit_records_list = None
    _hyper_helper = None
    _audit_dir = file_paths.AUDIT_DIR
    _audit_hyper_file_name = file_paths.AUDIT_HYPER_FILE_NAME

    def __init__(self):
        pass

    def __del__(self):
        TableauHyperAPIHelper.close_hyper_process()

    @classmethod
    def __new__(cls, *args, **kwargs):
        '''Enforce Singleton Pattern'''
        if cls._instance is None:
            AUDIT_LOGGER.debug('Initializing Auditor Instance')
            cls._instance = super(Auditor, cls).__new__(cls)
            cls._audit_records_list = list()
            hyper_file_path = os.path.join(cls._instance._audit_dir, cls._instance._audit_hyper_file_name)
            AUDIT_LOGGER.debug(f'Hyper File Path: {hyper_file_path}')
            cls._hyper_helper = TableauHyperAPIHelper.for_writing_to_output(hyper_file_path)

        return cls._instance

    @classmethod
    def audit_actions(cls, decorated_func):
        def wrapper(*args, **kwargs):
            try:
                AUDIT_LOGGER.debug(f'Auditing action from function: {decorated_func.__name__}')
                retvals = decorated_func(*args, **kwargs)
                if (type(retvals) == tuple):
                    return_val = retvals[0]
                    audit_record = retvals[1]
                    cls.append_to_audit_records(audit_record)
                else:
                    return_val = retvals
                    AUDIT_LOGGER.debug('Functions decorated with @audit_actions must return a tuple.')
                return return_val
            except:
                AUDIT_LOGGER.exception(f'Unable to audit function: {decorated_func.__name__}')
        return wrapper

    @classmethod
    def append_to_audit_records(cls, item):
        cls._audit_records_list.append(item)

    @classmethod
    def get_hyper_helper(cls):
        return cls._hyper_helper

    @classmethod
    def get_audit_records_list(cls):
        return cls._audit_records_list

    def save_audit_records(self):
        # dest_workbook_name = f'{tab_wb_name}-{uuid.uuid4().hex[:8]}'

        AUDIT_LOGGER.info(f'Saving Application Audit Records to {self._audit_hyper_file_name}')
        df = pd.DataFrame(data=Auditor.get_audit_records_list())

        hyper_helper = Auditor.get_hyper_helper()
        hyper_file_path = os.path.join(self._audit_dir, self._audit_hyper_file_name)

        if not df.empty:
            hyper_helper.write_dataframe(df, hyper_file_path, AUDIT_TABLE_NAME)

    def create_workbook_audit_action(self, tsclient, site_content_url, object_luid, file_path=None, action_type=None, action_log=None):

        dt_string = utils.get_now_as_string()

        workbook_item = tsclient.workbooks.get_by_id(object_luid)

        # get owner information
        try:
            user = tsclient.users.get_by_id(workbook_item.owner_id)
            owner_name = user.name
            owner_luid = user.id
        except ServerResponseError:
            # error may happen if user is not allowed to query users
            owner_name = None
            owner_luid = None

        action = AuditAction(date=dt_string,
                                    site_content_url=site_content_url,
                                    site_luid= tsclient.site_id,
                                    project_name=workbook_item.project_name,
                                    project_luid=workbook_item.project_id,
                                    object_name=workbook_item.name,
                                    object_luid=workbook_item.id,
                                    object_type=OBJECT_TYPE_WORKBOOK,
                                    owner_name=owner_name,
                                    owner_luid=owner_luid,
                                    file_path=file_path,
                                    action_type=action_type,
                                    action_log=action_log,
                                    )

        return action


    def create_datasource_audit_action(self, tsclient, site_content_url, object_luid, file_path=None, action_type=None, action_log=None):
        dt_string = utils.get_now_as_string()

        datasource_item = tsclient.datasources.get_by_id(object_luid)

        # get owner information
        try:
            user = tsclient.users.get_by_id(datasource_item.owner_id)
            owner_name = user.name
            owner_luid = user.id
        except ServerResponseError:
            # error may happen if user is not allowed to query users
            owner_name = None
            owner_luid = None

        action = AuditAction(date=dt_string,
                                    site_content_url=site_content_url,
                                    site_luid=tsclient.site_id,
                                    project_name=datasource_item.project_name,
                                    project_luid=datasource_item.project_id,
                                    object_name=datasource_item.name,
                                    object_luid=datasource_item.id,
                                    object_type=OBJECT_TYPE_DATASOURCE,
                                    owner_name=owner_name,
                                    owner_luid=owner_luid,
                                    file_path=file_path,
                                    action_type=action_type,
                                    action_log=action_log,
                                    )

        return action


    def create_view_audit_action(self, tsclient, site_content_url, view_item, file_path=None, action_type=None, action_log=None):

        dt_string = utils.get_now_as_string()

        # get owner information
        user = tsclient.users.get_by_id(view_item.owner_id)

        action = AuditAction(date=dt_string,
                                    site_content_url=site_content_url,
                                    site_luid= tsclient.site_id,
                                    project_name=None,
                                    project_luid=None,
                                    object_name=view_item.name,
                                    object_luid=view_item.id,
                                    object_type=OBJECT_TYPE_VIEW,
                                    owner_name=user.name,
                                    owner_luid=user.id,
                                    file_path=file_path,
                                    action_type=action_type,
                                    action_log=action_log,
                                    )

        return action

    def create_hyper_audit_action(self, file_path=None, action_type=None, action_log=None):
        dt_string = utils.get_now_as_string()


        action = AuditAction(date=dt_string,
                                    site_content_url=None,
                                    site_luid= None,
                                    project_name=None,
                                    project_luid=None,
                                    object_name=None,
                                    object_luid=None,
                                    object_type=OBJECT_TYPE_HYPER,
                                    owner_name=None,
                                    owner_luid=None,
                                    file_path=file_path,
                                    action_type=action_type,
                                    action_log=action_log,
                                    )

        return action

    def create_flow_audit_action(self, tsclient, site_content_url, object_luid, file_path=None, action_type=None, action_log=None):
        dt_string = utils.get_now_as_string()

        flow_item = tsclient.flows.get_by_id(object_luid)

        # get owner information
        try:
            user = tsclient.users.get_by_id(flow_item.owner_id)
            owner_name = user.name
            owner_luid = user.id
        except ServerResponseError:
            # error may happen if user is not allowed to query users
            owner_name = None
            owner_luid = None

        action = AuditAction(date=dt_string,
                                    site_content_url=site_content_url,
                                    site_luid=tsclient.site_id,
                                    project_name=flow_item.project_name,
                                    project_luid=flow_item.project_id,
                                    object_name=flow_item.name,
                                    object_luid=flow_item.id,
                                    object_type=OBJECT_TYPE_FLOW,
                                    owner_name=owner_name,
                                    owner_luid=owner_luid,
                                    file_path=file_path,
                                    action_type=action_type,
                                    action_log=action_log,
                                    )

        return action