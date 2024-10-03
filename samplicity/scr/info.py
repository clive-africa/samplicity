"""
SCR Info Module

This module provides functionality to extract and organize information about the
structure and content of an SCR (Solvency Capital Requirement) object.

The module contains functions to recursively extract information from nested
dictionaries and compile it into a pandas DataFrame for easy analysis.

Functions:
    extract_dict_info: Recursively extracts information from nested dictionaries.
    info: Compiles information about an SCR object into a DataFrame.

Dependencies:
    pandas
    numpy
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Union

def info(sam_scr: Any) -> pd.DataFrame:
    """
    Compile information about an SCR object into a DataFrame.

    This function extracts information from the 'classes' and 'output' attributes
    of an SCR object and compiles it into a pandas DataFrame for easy analysis.

    Args:
        sam_scr (Any): An SCR object containing 'classes' and 'output' attributes.

    Returns:
        pd.DataFrame: A DataFrame containing information about the structure and
        content of the SCR object. The DataFrame has the following columns:
        ["Module", "Dictionary", "Level", "Object Type", "Rows", "Columns", "Size"]

    Raises:
        AttributeError: If the input object doesn't have the expected attributes.
        TypeError: If the 'classes' attribute is not a dictionary.
    """
    try:
        if not isinstance(sam_scr.classes, dict):
            raise TypeError("The 'classes' attribute must be a dictionary.")

        dict_info = []
        for k, v in sam_scr.classes.items():
            if hasattr(v, "output"):
                dict_info.extend(_f_extract_dict_info(v.output, k))
            else:
                print(f"Warning: Class '{k}' does not have an 'output' attribute.")

        dict_info.extend(_f_extract_dict_info(sam_scr.output, "scr"))

        df = pd.DataFrame(
            dict_info,
            columns=[
                "Module",
                "Dictionary",
                "Level",
                "Object Type",
                "Rows",
                "Columns",
                "Size",
            ],
        )
        return df

    except AttributeError as e:
        print(f"Error: The input object doesn't have the expected attributes. {str(e)}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise

def _f_extract_dict_info(
    d: Dict[str, Any], module: str, parent_name: str = "", level: int = 0
) -> List[
    Tuple[str, str, int, str, Union[int, float], Union[int, float], Union[int, float]]
]:
    """
    Recursively extract information from nested dictionaries.

    This function traverses a dictionary and its nested structures, collecting
    information about each item including its type, size, and location in the
    hierarchy.

    Args:
        d (Dict[str, Any]): The dictionary to extract information from.
        module (str): The name of the module this dictionary belongs to.
        parent_name (str, optional): The name of the parent key. Defaults to "".
        level (int, optional): The current nesting level. Defaults to 0.

    Returns:
        List[Tuple[str, str, int, str, Union[int, float], Union[int, float], Union[int, float]]]:
        A list of tuples containing information about each item in the dictionary.
        Each tuple contains:
        (module, full_key_name, nesting_level, object_type, rows, columns, size)
    """
    dict_info = []

    for key, value in d.items():
        current_name = f"{parent_name}/{key}" if parent_name else key

        if isinstance(value, pd.DataFrame):
            rows, cols = value.shape
            size = rows * cols
        elif isinstance(value, dict):
            rows, cols = 0, 0
            size = len(value)
        else:
            rows, cols, size = np.nan, np.nan, np.nan

        dict_info.append(
            (module, current_name, level, type(value).__name__, rows, cols, size)
        )

        if isinstance(value, dict):
            dict_info.extend(extract_dict_info(value, module, current_name, level + 1))

    return dict_info
