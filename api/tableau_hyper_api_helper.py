import pandas as pd
import numpy as np
from datetime import datetime

import pantab
import tableauhyperapi
import logging
from my_console_app import file_paths

HYPER_HELPER_LOGGER = logging.getLogger('TableauHyperAPIHelper')

HYPER_PARAMETERS = {
    # Limits the number of Hyper event log files to two.
    "log_file_max_count": "2",
    # Limits the size of Hyper event log files to 100 megabytes.
    "log_file_size_limit": "100M",
    # Change Default Log File Path
    'log_dir': file_paths.LOG_DIR,
    # Change domain sockets dir
    #'domain_socket_dir' : file_paths.HYPER_TMP_DIR
}

class TableauHyperAPIHelper:
    """Shared Helper Class for Tableau Hyper API
    """

    # declare class variables
    hyper_connection: tableauhyperapi.Connection = None
    hyper_process: tableauhyperapi.HyperProcess = None

    def __init__(self, *args, **kwargs):
        """
        HyperAPIHelper is used for reading data and writing output to Hyper Files
        Please use the methods for_read_only and for_writing_to_output for instantiation.
        Args:
            *args:
            **kwargs:
        """
        # TODO: Hyper Log Settings should be configured here, to honor the settings from configuration file (log files should go to log directory)

        self.hyper = TableauHyperAPIHelper.get_hyper_process()

        #parse kwargs
        self.file_path = kwargs.get('hyper_file_path')
        self.create_writeable_connection = kwargs.get('create_writeable_connection')

        if self.create_writeable_connection:
            HYPER_HELPER_LOGGER.debug(f'Creating Writeable Connection to Hyper File: {self.file_path}')
            self.hyper_connection = tableauhyperapi.Connection(endpoint=self.hyper.endpoint, database=self.file_path,
                                                           create_mode=tableauhyperapi.CreateMode.CREATE_IF_NOT_EXISTS)
        else:
            HYPER_HELPER_LOGGER.debug(f'Creating Read-Only Connection to Hyper File: {self.file_path}')
            self.hyper_connection = tableauhyperapi.Connection(endpoint=self.hyper.endpoint, database=self.file_path,
                                                               create_mode=tableauhyperapi.CreateMode.NONE)

        self.tables = self.get_table_names()

    def __del__(self):
        self.close_hyper_connection()

    @classmethod
    def for_read_only(cls, _hyper_file_path):
        return cls(create_writeable_connection=False, hyper_file_path=_hyper_file_path)

    @classmethod
    def for_writing_to_output(cls, _hyper_file_path):
        return cls(create_writeable_connection=True, hyper_file_path=_hyper_file_path)

    @classmethod
    def get_hyper_process(cls):
        if cls.hyper_process is None:
            cls.hyper_process = tableauhyperapi.HyperProcess(telemetry=tableauhyperapi.Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters=HYPER_PARAMETERS)
        return cls.hyper_process

    @classmethod
    def close_hyper_process(cls):
        if cls.hyper_process is not None:
            cls.hyper_process.shutdown()

    def close_hyper_connection(self):
        if self.hyper_connection != None:
            self.hyper_connection.close()


    def get_table_names(self, schema="Extract"):

        listOfTables = []

        table_names = self.hyper_connection.catalog.get_table_names(schema=schema)
        for table in table_names:
            table_name = table.name.__str__().replace('"','')
            listOfTables.append(table_name)

        return listOfTables

    def table_exists(self, table_name):
        exists = False

        for tn in self.tables:
            if table_name == tn:
                exists = True

        return exists

    def create_hyper_schema(self, _schema_name="Extract"):
        self.hyper_connection.catalog.get_schema_names()
        self.hyper_connection.catalog.create_schema(_schema_name)

    def create_hyper_table(self, _dataframe, _table_name, _schema_name="Extract"):
        """Creates a hyper extract table (without data)

        Args:
            _dataframe:  (pd.DataFrame): Panda Data Frame
            _table_name:
            _schema_name:

        Returns:
            bool: indicating success/failure

        """

        if _dataframe.empty:
            raise ValueError('Data Frame is Empty')
            return

        HYPER_HELPER_LOGGER.debug(f"Starting writing output table: {_table_name}")

        self.create_hyper_schema("Extract")
        output_table = tableauhyperapi.TableDefinition(tableauhyperapi.TableName(_schema_name, _table_name))

        # iterate through data frame and add table definition columns
        column_dict = dict(_dataframe.dtypes)
        for colname, coltype in column_dict.items():
            output_table.add_column(colname, self.translate_df_type_to_hyper_type(coltype))

        #create hyper table for output
        self.hyper_connection.catalog.create_table(output_table)

        HYPER_HELPER_LOGGER.debug(f"Completed creating hyper table: {_table_name}")

    def write_dataframe(self, _dataframe, _hyper_file_name, _table_name, _table_mode='a'):
        pantab.frame_to_hyper(_dataframe, _hyper_file_name, table=_table_name, table_mode=_table_mode, hyper_process=self.hyper_process)

    def refresh_hyper_dataset(self, _dataframe, _table_name):
        default_table_name = tableauhyperapi.TableName("Extract", "Extract")

        sql_command = f"DELETE FROM {default_table_name}"
        HYPER_HELPER_LOGGER.debug(f'Executing SQL Command: {sql_command}')
        row_count = self.hyper_connection.execute_command(sql_command)
        action_log = f"Successfully trimmed hyper extract. Deleted {row_count} rows of data."
        HYPER_HELPER_LOGGER.info(action_log)

        self.insert_rows(_dataframe, _table_name)

        self.close_hyper_connection()
        return True



