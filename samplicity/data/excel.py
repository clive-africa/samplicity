import datetime
import pandas as pd
import xlwings as xw
from numpy import arange
from tqdm import tqdm
from typing import Literal, Union


def f_excel_import_range(
    range_name: str,
    sheet_name: str,
    transformation: Literal["none", "index", "corr", "melt"],
    wb: xw.Book,
) -> Union[pd.DataFrame, None]:
    """
    Import an Excel range from a workbook.

    :param range_name:  The name of the range.
    :type range_name:   str
    :param sheet_name: The name of the worksheet.
    :type sheet_name: str
    :param transformation: The type of transformation to apply to the data. Must be one of : ["none", "index", "corr", "melt"]
    :type transformation: str
    :return:  A Dataframe of results or None if not successful
    :rtype: Union[pd.DataFrame, None]
    :raises ValueError: If an unsupported transformation is provided.

    :Example:

    >>> f_excel_import_range("range_name", "sheet_name", "none", wb)
    """

    try:
        if transformation in ("none", "index", "corr", "melt"):
            # Only use True for the index transformation
            index_val = transformation == "index"
            pd_data = (
                wb.sheets(sheet_name)
                .range(range_name)
                .options(pd.DataFrame, header=1, index=index_val, expand="table")
                .value
            )

            # Can only apply this if we don't apply any transformations
            if transformation == "none":
                pd_data.dropna(how="all", inplace=True)

            # Only apply the transformation if we have a correlation matrix
            if transformation == "corr":
                pd_data.set_index(pd_data.columns, inplace=True)
                pd_data = pd_data.fillna(0)
                pd_data = pd_data.add(pd_data.T)
                pd_data.values[tuple([arange(pd_data.shape[0])]) * 2] = 1

            # Only apply if the melt transformation is applied
            if transformation == "melt":
                col_name = pd_data.columns[1]
                col_name = col_name.split("_", 1)[0]
                pd_data = pd.melt(
                    pd_data,
                    id_vars=pd_data.columns[0],
                    value_name=col_name,
                    var_name="zzz_delete_zzz",
                )
                pd_data.drop(columns=["zzz_delete_zzz"], inplace=True)
                pd_data.dropna(inplace=True)
        else:
            raise ValueError("Invalid transformation type.")
            pd_data = None
    except Exception as e:
        print(f"Error processing range '{range_name}' in sheet '{sheet_name}': {e}")
        pd_data = None

    return pd_data


# All of the ranges we need to import are specified in the EXcel workbook.
# This avoids having to make multiple looping statements in Python
# @log_decorator
def f_excel_import_data(
    import_file: str, dictionary: Literal["metadata", "data"]
) -> dict:
    """
    Imports various Excel ranges into a dictionary.
    This is a helper function to the 'import_metadata' and 'import_data'
    functions.

    :param import_file:  The name of the file to import.
    :type import_file:   str
    :param sheet_name: The dictionary to import. Must be one of : ["metadata", "data"]
    :type sheet_name: str
    :param transformation: The type of transformation to apply to the data. Must be one of : ["none", "index", "corr", "melt"]
    :type transformation: str
    :return:  A dictionary of results.
    :rtype: Union[pd.DataFrame, None]
    :raises ValueError: If an unsupported transformation is provided.

    .. note::
        The ranges to import are assumed to come from a range
        named 'imports' in the work sheet 'imports'. The 'import' range must
        include the columns:
            -'dictionary'
            -'python_variable'
            -'worksheet'
            -'range_name'
            -'transformation'

    :Example:

    >>> f_excel_import_data("c:/samplicity/test_file.xlsx", "data")
    """
    # logger.debug("Function start")

    # print(import_file)
    # We stroe all of the reuslts of our import here.
    # df = dat.output["data_validation"]

    # Will store the output of the function
    data = {}

    data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["file"] = import_file

    with xw.App(visible=False) as app:
        wb = xw.Book(import_file, update_links=False)
        import_data = (
            wb.sheets("imports")
            .range("imports")
            .options(pd.DataFrame, header=1, index=False, expand="table")
            .value
        )

        # Filter the df to only get the specific entries that we require
        import_data.query(f"dictionary == '{dictionary}'", inplace=True)

        with tqdm(total=len(import_data), desc="Importing variables ...") as pbar:
            for index, row in import_data.iterrows():
                pbar.set_description(f"Importing {row.python_variable}")
                try:
                    data[row["python_variable"]] = f_excel_import_range(
                        row["range_name"], row["worksheet"], row["transformation"], wb
                    )
                except:
                    print("Error importing range: " + row["python_variable"])
                pbar.update(1)

            wb.close()
        tqdm._instances.clear()
        pbar.close()

    return data


# @log_decorator
def f_excel_import_pa_data(risk_free_rates, symmetric_adjustment):
    """Import monthly PA files."""

    data = {}
    # Import the risk free rates first
    with xw.App(visible=False) as app:
        wb = xw.Book(risk_free_rates)
        for dat in ("Nominal", "Real"):
            data[dat.lower()] = pd.DataFrame(
                wb.sheets("Bond - " + dat)
                .range("A3")
                .options(expand="table", dates=datetime.date)
                .value,
                columns=["start_date", "end_date", "forward_rate"],
            )

        data["risk_free_rates_time_stamp"] = datetime.datetime.now()
        data["risk_free_rates_file"] = risk_free_rates

        # Now we import the symmetric adjustment
        wb = xw.Book(symmetric_adjustment)
        sa_data = pd.DataFrame(
            wb.sheets[0].range("B4").options(expand="table", dates=datetime.date).value,
            columns=["month", "global", "sa", "other"],
        )
        sa_data = sa_data.loc[
            (len(sa_data) - 1) : (len(sa_data) - 1),
            ["month", "global", "sa", "other"],
        ]
        sa_data.set_index("month", inplace=True)
        data["symmetric_adjustment"] = sa_data

        data["symmetric_adjustment_time_stamp"] = datetime.datetime.now()
        data["symmetric_adjustment_file"] = symmetric_adjustment

        wb.close()

    return data


# @log_decorator
def f_excel_export(sam_scr, result_set, export_file, process_id=None):
    """Export data to an Excel workbook."""
    # logger.debug("Function start")

    if process_id in xw.apps.keys():
        app = xw.apps[process_id]
        wb = app.Books[export_file.split("/")[-1]]
    else:
        wb = xw.Book(export_file, update_links=False)
    with tqdm(total=len(result_set), desc="Exporting output ...") as pbar:
        for row in result_set.itertuples():
            pbar.set_description(f"Exporting {row.range}")
            # logger.debug(f"{row.module} -  {row.data} - {row.sub_data}")
            try:
                df = sam_scr.f_data(row.module, row.data, row.sub_data)
            except:
                logger.critical(
                    f"Entry not found:{row.module}-{row.data}-{row.sub_data}"
                )
                df = pd.DataFrame(
                    data=f"Critical Error: Data not found - {row.module}-{row.data}-{row.sub_data}",
                    index=["Error"],
                    columns=["Error"],
                )
            else:
                if isinstance(df, pd.DataFrame):
                    if any(isinstance(x, frozenset) for x in df.index):
                        df.index = [", ".join(map(str, fset)) for fset in df.index]
                        df.index = df.index.map(str)

                try:
                    wb.sheets(row.worksheet).range(row.range).clear_contents()
                    # df.to_excel(wb, sheet_name=row.worksheet, startrow=row.startrow, startcol=row.startcol, h
                    wb.sheets(row.worksheet).range(row.range).options(
                        index=row.include_index, header=row.include_header
                    ).value = df
                except:
                    logger.critical(
                        f"Error with output details: {row.worksheet}-{row.range}"
                    )
            pbar.update(1)
        pbar.close()
        # Clsoe and save the workbook
        # Clsoe teh app if it wasn't open
        wb.save()
        wb.close()

        tqdm._instances.clear()

    print(f"Results saved to {export_file}")

    return True
