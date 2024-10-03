"""
main.

Supporting code for the SCR class.
Designed to help execution from various environments.

@author: chogarth

"""

import logging
import argparse
import sys
from io import StringIO as StringBuffer
import warnings
from .scr.scr import SCR

logger = logging.getLogger(__name__)


def main():
    """The functionality called from the command line."""


parser = argparse.ArgumentParser(
    prog="Samplicity",
    description="Python calculation of the SAM non-life SCR.",
    epilog="Text at the bottom of help",
)

parser.add_argument(
    "ms_access_file",
    metavar="acces_file",
    type=str,
    nargs=1,
    help="location of the MS Access database",
)
parser.add_argument(
    "import_table",
    metavar="import_table",
    type=str,
    nargs=1,
    help="name of table defining the imports",
)


def run_excel(
    import_file: str,
    risk_free_rates: str,
    symmetric_adjustment: str,
    export_file: str,
    log_detail: str = None,
    process_id: int = None,
) -> bool:
    """Simplify the CMD call, where data is populated in Excel."""

    # Set the logging configuration
    message_format = (
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s() - %(message)s"
    )
    # Thsi will capture teh logs to a string variable
    log_capture_string = StringBuffer()
    ch = logging.StreamHandler(log_capture_string)

    logger.debug("Function start")
    sam_scr = SCR()
    sam_scr.f_import_data(
        metadata_file="",
        risk_free_rates=risk_free_rates,
        symmetric_adjustment=symmetric_adjustment,
        data_file=import_file,
        connection_string=None,
        import_table=None,
        export_table=None,
        log_detail=log_detail,
    )
    sam_scr.f_calculate()
    sam_scr.f_export_results(export_file, process_id=process_id)

    return True


def run_ms_access(
    ms_access_file: str,
    import_table: str,
    export_table: str,
    risk_free_rates: str,
    symmetric_adjustment: str,
    run_id,
    valuation_id,
    valuation_date,
    log_detail: str = None,
):
    """Simplify the CMD call, where data is populated in a database."""

    logger.debug("Function start")
    # Create a connection string here, MS Access specific.
    conn_string = (
        'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="'
        + ms_access_file
        + '";'
    )

    dict_param = {"pRun": run_id, "pValuation": valuation_id, "pDate": valuation_date}

    sam_scr = scr.SCR()
    sam_scr.f_import_data(
        metadata_file="",
        risk_free_rates=risk_free_rates,
        symmetric_adjustment=symmetric_adjustment,
        data_file=None,
        result_export=None,
        conn_string=conn_string,
        import_table=import_table,
        export_table=export_table,
        dict_param=dict_param,
        log_detail=log_detail,
    )
    sam_scr.f_calculate()
    sam_scr.f_export_results(
        export_file=None, process_id=run_id, conn_string=conn_string
    )

    return True


"""
Testing code

This code is used to test the module that we are creating.

"""


def test_runs(stop_at=None, export=True):
    def custom_warning_handler(
        message, category, filename, lineno, file=None, line=None
    ):
        logging.warning(f"DeprecatedWarning: {message}", stack_info=False)

    # Register the custom warning handler
    warnings.showwarning = custom_warning_handler

    # Set the logging configuration
    message_format = (
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s() - %(message)s"
    )
    # Thsi will capture teh logs to a string variable
    log_capture_string = StringBuffer()
    ch = logging.StreamHandler(log_capture_string)

    # Specify the fromat that will be capture din the string varibale
    formatter = logging.Formatter(message_format)
    ch.setFormatter(formatter)

    # We need to remvoe all the handler before we can use basicCOnfig
    # BasicConfig only adds handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.DEBUG, format=message_format, filename="log2", filemode="w"
    )

    logger = logging.getLogger(__name__)

    logger.addHandler(ch)

    # The import file
    # This will contian all of our imputs and out metadata
    import_file = "C:/Work/sam_scr/input/sam_input.xlsm"

    risk_free_rates = (
        "C:/Work/sam_scr/input/12 SAM - Risk Free Rates  (30 December 2022).xlsx"
    )
    symmetric_adjustment = "C:/Work/sam_scr/input/12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx"

    # The file where we will be exporting all of our outputs to.
    # The output is for
    export_file = "C:/Work/sam_scr/input/sam_input.xlsm"

    sam_scr = SCR()
    sam_scr.f_import_data(
        metadata_file="",
        risk_free_rates=risk_free_rates,
        symmetric_adjustment=symmetric_adjustment,
        data_file=import_file,
        result_export=True,
        conn_string=None,
        import_table=None,
        export_table=None,
    )

    sam_scr.f_calculate(stop_at)

    if export:
        sam_scr.f_export_results(export_file)

    ### Pull the contents back into a string and close the stream
    log_contents = log_capture_string.getvalue()
    log_capture_string.close()

    return sam_scr


if __name__ == "__main__":
    import sys

    sys.path.append("c:/git_hub/sam_scr/src/")

    input_folder = "C:/git_hub/sam_scr/.input/"

    def custom_warning_handler(
        message, category, filename, lineno, file=None, line=None
    ):
        logging.warning(f"DeprecatedWarning: {message}", stack_info=False)

    # Register the custom warning handler
    warnings.showwarning = custom_warning_handler

    # Set the logging configuration
    message_format = (
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s() - %(message)s"
    )
    # Thsi will capture teh logs to a string variable
    # log_capture_string = StringBuffer()
    # ch = logging.StreamHandler(log_capture_string)
    fh = logging.FileHandler("c:/git_hub/sam_scr/sam.log")
    # Specify the fromat that will be capture din the string varibale
    # formatter = logging.Formatter(message_format)
    # ch.setFormatter(formatter)

    # We need to remvoe all the handler before we can use basicCOnfig
    # BasicConfig only adds handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.DEBUG,
        format=message_format,
        filename="c:/git_hub/sam_scr/sam.log",
        filemode="w",
    )

    logger = logging.getLogger(__name__)

    # logger.addHandler(fh)

    # The import file
    # This will contian all of our imputs and out metadata
    import_file = input_folder + "sam_input.xlsm"

    risk_free_rates = input_folder + "12 SAM - Risk Free Rates  (30 December 2022).xlsx"
    symmetric_adjustment = (
        input_folder + "12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx"
    )

    # The file where we will be exporting all of our outputs to.
    # The output is for
    export_file = input_folder + "sam_input.xlsm"

    sam_scr = SCR()
    sam_scr.f_import_data(
        metadata_file="",
        risk_free_rates=risk_free_rates,
        symmetric_adjustment=symmetric_adjustment,
        data_file=import_file,
        result_export=True,
        conn_string=None,
        import_table=None,
        export_table=None,
    )

    sam_scr.f_calculate()
    export = True

    if export:
        sam_scr.f_export_results(export_file)
