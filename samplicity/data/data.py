import xlwings as xw
import pandas as pd
import datetime
import numpy as np


from typing import Optional, Dict, Any

# Used to store and read our metadata
import pickle

from .odbc import f_odbc_import, f_odbc_export
from .excel import f_excel_import_data, f_excel_export, f_excel_import_pa_data

# from .data_models import validate_data_models
from .data_validation import validate_data

from ..helper import log_decorator

# Storing our metadat with our package
import os

# Allows us to read and write data to a database
import pyodbc
import urllib
import sqlalchemy

# import duckdb as db

import logging

logger = logging.getLogger(__name__)


class Data:
    """
    A class perform the data import (and export) routines for the SCR class.

    Limitations
    -----------
    - The class makes use of the xlwings library.
    - However, other libraries may be better.
    - Should investigate if xlsxwriter is not a faster & more robust
    - Current implementation is that a workbook is opened multiple times.
    - xlwings makes it a little easier with the 'expand' option.

    Attributes
    ----------
    scr : SCR class
        the main SCR calling class.
    output : dictionary
        a dictionary of all output values that are generated by the class.
    doc_data : dictionary
        a df documenting the data that can be extracted from the Data class.
    data_checks : daatframe
        a dataframe of checks that are performed, currently not used.


    Methods
    -------
    __init__:
        Creates the various dictionaries that will be used by the class.
    f_check_integrity:
        Creates the different combinations for diversification calculations.
    f_data_checks:
        Aggregates the different components of the SCR.
    f_odbc_table_import:
        Imports the data used by the class.
    f_odbc_import:
        Performs the necessary SCR calculations, using the supporting classes.
    f_odbc_export:
        supporting f_export_results to export data to an ODBC database.
    f_excel_import_range:
        function to import an Excel range.
    f_excel_import_data:
        function to import data from Excel.
    f_excel_import_pa_data:
        a function to imort the PA workbooks.
    f_excel_export:
        supporting f_export_results to export data to an Excel worksheet.
    f_import:
        function to import data into the class.
    f_export_results:
        exports results of the SCR class to Excel or ODBC.
    f_data:
        Retrieves data from the class.
    """

    @log_decorator
    def __init__(self, sam_scr):
        # logger.debug("Function start")

        self.scr = sam_scr
        """ A reference to the main SCR class. """

        self.output = {}
        """ The output values of the class."""

        self.output["data_validation"] = pd.DataFrame(
            columns=["data_check", "check_result", "description", "value"]
        )
        """ A dataframe of checks that are performed, currently not used. """

    @log_decorator
    def f_import_data(
        self,
        risk_free_rates: str,
        symmetric_adjustment: str,
        data_file: Optional[str] = None,
        conn_string: Optional[str] = None,
        import_table: Optional[str] = None,
        export_table: Optional[str] = None,
        dict_param: Optional[Dict[str, Any]] = None,
        log_detail: Optional[str] = None,
        metadata_file: Optional[str] = None,
        validate_data: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """Import data for the package.

        Args:
            metadata_file (str): The file path of the metadata file.
            risk_free_rates (float): The risk-free rates.
            symmetric_adjustment (float): The symmetric adjustment.
            data_file (str, optional): The file path of the data file. Defaults to None.
            conn_string (str, optional): The connection string for database import. Defaults to None.
            import_table (str, optional): The table name for database import. Defaults to None.
            export_table (str, optional): The table name for database export. Defaults to None.
            dict_param (dict, optional): Additional parameters for database import. Defaults to None.
            log_detail (str, optional): The detail at which the calculations will be logged. Defaults to None.

        Returns:
            dict: The imported data and metadata.

        """
        # logger.debug("Function start")

        # Get the detail at which the calculations will be logged
        # For each module this will detrmine the detail
        # Need to still code this
        self.output["log_detail"] = log_detail

        # Here we differentiate between the Excel and database import functions
        if data_file == None:
            # The database import
            self.output["data"] = f_odbc_import(conn_string, import_table, dict_param)
        else:
            # The Excel import
            self.output["data"] = f_excel_import_data(data_file, "data")

            # Need a definition of the results that should be exported.
            wb = xw.Book(data_file)
            df = (
                wb.sheets("result_exports")
                .range("result_exports")
                .options(pd.DataFrame, header=1, index=False, expand="table")
                .value
            )
            # Seems odd but we use the data dictionary to store the data
            # We ill later sotre the timestamp of the export
            self.output["result_export"] = {}
            self.output["result_export"]["data"] = df
            wb.close()

        # DATA CORRECTIONS
        # This will need to move to it's own modeul
        # These are data conversion where data may have bene imported at object when it should
        #  be another datatype
        cols = [
            "gross_p",
            "gross_p_last",
            "gross_p_last_24",
            "gross_fp_existing",
            "gross_fp_future",
            "gross_claim",
            "gross_other",
            "net_p",
            "net_p_last",
            "net_p_last_24",
            "net_fp_existing",
            "net_fp_future",
            "net_claim",
            "net_other",
        ]
        self.output["data"]["prem_res"][cols] = self.output["data"]["prem_res"][
            cols
        ].astype(float)
        self.output["data"]["prem_res"][cols] = self.output["data"]["prem_res"][
            cols
        ].fillna(0)

        # We convert the divisions to numbers. This is done
        # to save significant time on the merging process that happens later.

        # From here on the same import process is followed.

        # We will generally import the meatdata from a pickle
        if metadata_file == None:
            folder_location = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            self.output["metadata"] = pickle.load(
                open(folder_location + "\\metadata\\metadata.p", "rb")
            )
            self.output["metadata"]["timestamp"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.output["metadata"]["file"] = "metadata.p"
        else:
            # The function populates the file and timestamp parameters
            self.output["metadata"] = f_excel_import_data(metadata_file, "metadata")

        # The PA Data is always imported from the Excel files.
        # The data is provided in Excel format every month
        self.output["pa_data"] = f_excel_import_pa_data(
            risk_free_rates, symmetric_adjustment
        )

        # TODO: Add additional validation to our data.
        # Now we need to validate our imported data against our data models
        # This tries to ensure that the data we use is correct
        # res = validate_data_models(self)

        # Run the data validation on the imported data
        # Metadata is validated separately.
        # We ahve left this off for now, Excel data is really difficult to validate
        if validate_data:
            self.output["data"] = validate_data(self.output["data"].copy())

        # Return the data in case someone wants to use the data
        return self.output

    def f_export_results(self, export_file=None, process_id=None, conn_string=None):
        """Export package results to Excel/database"""
        # logger.debug("Function start")
        self.scr.output_errors.append(f"Data Hi")
        # The mapping of the data we wish to export
        # The format for the Excel and dtaabse connection will differ
        result_set = self.output["result_export"]["data"]

        self.output["result_export"]["timestamp"] = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if export_file == None:
            f_odbc_export(result_set, conn_string, process_id)
            self.output["result_export"]["file"] = conn_string
        else:
            f_excel_export(self.scr, result_set, export_file, process_id)
            self.output["result_export"]["file"] = export_file

    def f_data(self, data="info", sub_data="info", df=None):
        """Extract data from DATA class."""

        try:
            # Just some cleaning of our inputs to ensure no errors occur
            data = data.lower().strip()
            if sub_data != None:
                sub_data = sub_data.lower().strip()

            if data == "info":
                df = self.doc_data
            elif sub_data in ("file", "timestamp"):
                df = pd.DataFrame([self.output[data]], columns=[sub_data], index=[data])

            # For the DATA class we need to shorten the base inputs
            # We overide the normal process here

            elif sub_data in self.output["data"]["base_inputs"].index.values:
                df = self.output["data"]["base_inputs"].loc[sub_data, ["base_inputs"]]
                return df
            elif sub_data == None:
                df = self.output[data]
            else:
                df = self.output[data][sub_data]
        except:
            logger.critical(f"Error: {data} - {sub_data}")
            raise ValueError(f"cannot find {data} - {sub_data}")
        else:
            if isinstance(df, pd.DataFrame):
                df = df.copy(deep=True)
            return df

    def _f_pickle_metadata(metadata_file: str) -> str:
        """
        Pickle the metadata for faster future access and to prevent accidental changes.

        This function reads metadata from an Excel file and saves it as a pickle file.
        The pickled metadata can be loaded more quickly in subsequent runs, improving
        performance. It also serves as a safeguard against accidental modifications to
        the metadata.

        :param metadata_file: Path to the metadata Excel file.
        :type metadata_file: str

        :return: Path to the created pickle file
        :rtype: str

        :raises FileNotFoundError: If the specified Excel file doesn't exist.
        :raises PermissionError: If there's no write permission for the pickle file location.

        .. note::
        The pickle file will be created in the same directory as the input Excel file.

        .. warning::
        Ensure that the metadata Excel file is up-to-date before pickling. Once pickled,
        any changes to the Excel file won't be reflected until this function is run again.

        Example:
            >>> pickle_path = f_pickle_metadata("path/to/metadata.xlsx")
            >>> print(pickle_path)
            path/to/metadata.p
        """
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        metadata = f_excel_import_data(metadata_file, "metadata")
        
        pickle_path = os.path.join(os.path.dirname(metadata_file), "metadata.p")
        
        with open(pickle_path, "wb") as f:
            pickle.dump(metadata, f)

        return pickle_path
