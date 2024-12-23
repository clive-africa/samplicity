"""

Various generic helper functions used the SCR and supporting classes.

"""

from itertools import combinations
import pandas as pd
import numpy as np
from typing import Union
import time
import functools
import samplicity as sam


def combins_df_col(df: pd.DataFrame, column: str, calc_type: Union[str, int]) -> list:
    """Get all possible combinations of a dataframe column."""

    # COnvert our datframe to a unique set
    df = df.sort_values(by=[column])
    set_df = set(df[column].unique())
    # We loop through our set to work out what we need to return
    if calc_type in ("diversification", -1):
        comb_range = range(1, len(set_df) + 1)
    elif calc_type in ("overall", 0):
        comb_range = [len(set_df), len(set_df)]
    elif calc_type in ("individual", 1):
        comb_range = [1, len(set_df)]
    else:
        raise Exception(
            "helper_functions",
            "combins_from_df_column",
            f"Invalid diversification level supplied, "
            f" {calc_type} is not recognised.",
        )

    # Create a blank list
    list_combinations = list()

    for n in comb_range:
        res = list(combinations(set_df, n))
        # res = [frozenset(x) for x in res]
        list_combinations += res

    # We are using sets as order doesn't matter
    # A frozenset is needed for the variosu dataframes

    list_combinations = [frozenset(x) for x in list_combinations]
    return list_combinations


def allocation_matrix(
    df: pd.DataFrame, column: str, calc_type: Union[str, int]
) -> pd.DataFrame:
    unique = df[column].unique()
    len_unique = len(unique)

    if calc_type in ("diversification", -1):
        comb_range = range(1, len_unique + 1)
    elif calc_type in ("overall", 0):
        comb_range = [len_unique, len_unique]
    elif calc_type in ("individual", 1):
        comb_range = [1, len_unique]
    else:
        raise Exception(
            "helper_functions",
            "combins_from_df_column",
            f"Invalid diversification level supplied, "
            f" {calc_type} is not recognised.",
        )

    combins = []
    for r in comb_range:
        combins.extend(combinations(unique, r))

    # Create a DataFrame with 0s and 1s
    df = pd.DataFrame(
        [{element: (element in combo) for element in unique} for combo in combins],
        index=[frozenset(x) for x in combins],
    )

    # Convert boolean values to int
    df = df.astype(int)

    return df


def check_tuple(x, tuple_string="('b', 'c', 'd')"):
    if str(x).find(tuple_string) >= 0:
        return True

def f_div_match(self, list_to_match):
    if list_to_match in self.list_combinations:
        return list_to_match
    else:
        count_intersect = list(
            map(lambda i: len(i.intersection(list_to_match)), self.list_combinations)
        )
        max_value = max(count_intersect)
        match_value = list(map(lambda i: i == max_value, count_intersect))
        filtered = np.array(self.list_combinations)[np.array(match_value)]
        return filtered

def f_best_match(x, join_list):
    """Function not used, repalce with f_new_match_element."""
    # The new version is a little more robust and does more checks
    # Need to check on the speed of the new version
    if x in join_list:
        return x
    else:
        count_intersect = pd.Series(
            map(
                lambda i: len(set(i).intersection(set(x)))
                * int(set(i).difference(set(x), join_list) == set()),
                join_list,
            )
        )

        max_value = max(count_intersect)
        if max_value > 0:
            count_intersect = count_intersect == max_value
            if sum(count_intersect) == 1:
                filtered = np.array(join_list)[count_intersect]
                return filtered[0]
            else:
                return np.nan
        else:
            return np.nan


def f_fast_join(left_df, right_df, dest_field, source_field):
    # Handle the case when the rigth df is None
    # This cna occur when there is no data to join
    # We do this here jsut to avoid repeatign it multiple times
    if right_df is None:
        return left_df

    set_left = set(left_df.index.to_list())
    set_right = set(right_df.index.to_list())

    # Find elements in list_A not in list_B
    diff_lr = set_left.difference(set_right)
    match_lr = set_left.intersection(set_right)

    # Convert back to list of sets
    match_lr = list(match_lr)
    diff_lr = list(diff_lr)

    # Match the records where we have a direct match
    left_df.loc[match_lr, dest_field] += right_df.loc[match_lr, source_field].values

    # We only run thsi if we need a join
    if len(diff_lr) == 0:
        return left_df

    # Now we start the 'fuzzy' joins
    # Apply the filer as we are only interested in those we couldn't match
    left_idx = left_df.loc[diff_lr, :].index.tolist()
    right_idx = right_df.index.tolist()

    left_idx = [frozenset(x) for x in left_idx]
    right_idx = [frozenset(x) for x in right_idx]

    # Precompute match_idx and isna_mask
    match_idx = [f_fast_match_element(x, right_idx) for x in left_idx]
    # orig_idx = [x if notna(y) else np.na  for x,y in zip(diff_lr,match_idx)]
    isna_mask = pd.notna(match_idx)

    # Filter indices with not NA
    notna_idx = [x for x, mask in zip(diff_lr, isna_mask) if mask]
    match_idx = [x for x, mask in zip(match_idx, isna_mask) if mask]

    # Update left_df in one indexing operation
    left_df.loc[notna_idx, dest_field] += right_df.loc[match_idx, source_field].values

    return left_df


def f_best_join(left_df, right_df, dest_field, source_field):
    # Convert index to list for faster lookup
    left_idx = left_df.index.tolist()
    right_idx = right_df.index.tolist()

    left_idx = [set(x) for x in left_idx]
    right_idx = [set(x) for x in right_idx]

    # Precompute match_idx and isna_mask
    match_idx = [f_fast_match_element(x, right_idx) for x in left_idx]
    isna_mask = pd.notna(match_idx)

    # Filter indices with not NA
    notna_idx = [x for x, mask in zip(left_idx, isna_mask) if mask]

    # Update left_df in one indexing operation
    left_df.loc[notna_idx, dest_field] += right_df.loc[match_idx, source_field].values

    return left_df


def f_accummulate_figures(
    dest_df,
    source_df,
    dest_col,
    source_col,
    dest_index_col="index",
    dest_index=True,
    source_index_col="index",
    source_index=True,
    agg_func="sum",
):
    """Matches a df with tuples index, against df with 'traditional' index."""
    if dest_index:
        dest_index_col = "index"
        prelim = pd.DataFrame(
            dest_df.index.values, columns=["explode"], index=dest_df.index
        )
    else:
        prelim = pd.DataFrame(
            dest_df[dest_index_col], columns=["explode"], index=dest_df[dest_index_col]
        )

    prelim.index.names = ["index"]
    prelim["explode"] = prelim["explode"].apply(list)
    prelim.reset_index(inplace=True)
    prelim = prelim.explode("explode")

    if source_index:
        prelim = prelim.merge(
            source_df[[source_col]], how="left", left_on="explode", right_index=True
        )
    else:
        prelim = prelim.merge(
            source_df[[source_index_col, source_col]],
            how="left",
            left_on="explode",
            right_on=source_index_col,
        )

    prelim = prelim[["index", source_col]].groupby("index").agg(agg_func)

    if dest_index:
        dest_df.loc[prelim.index, dest_col] = prelim[source_col]
    else:
        dest_df.loc[:, dest_col] = prelim.loc[dest_df[dest_index_col], source_col]
        dest_df[source_col].fillna(0, inplace=True)


def f_get_total_row(df):
    """Returns the index with the longest tuple."""
    length = [len(x) for x in df.index]
    max_length = max(length)
    pos = [x == max_length for x in length]

    return df.loc[pos, :].copy(deep=True)


def f_fast_match_element(x, right_list):

    # Check for an exact match
    if x in right_list:
        return x

    # Calculate match lengths and mismatches
    match_len = [len(x.intersection(y)) for y in right_list]
    no_mis_match = [y.difference(x) == set() for y in right_list]

    # Update match_len to remove mismatches
    match_len = [l * int(m) for l, m in zip(match_len, no_mis_match)]

    # Check if there are any matches
    if sum(match_len) == 0:
        return np.nan

    # Find the maximum match length
    max_match = max(match_len)

    # Check if there's more than one max match
    if match_len.count(max_match) > 1:
        return np.nan

    # Return the element with the max match
    return right_list[match_len.index(max_match)]


def f_new_match_element(x, right_list):
    # We first chekc for an exact match
    if type(right_list) != list:
        if x in right_list.to_list():
            return x
    else:
        if x in right_list:
            return x

    # We start with x in the left index and
    # compare it to the right index elements
    # We do this for eahc x in the left index
    # match_len = right_list.apply(lambda y: len(set(x).intersection(set(y))))
    match_len = list(map(lambda y: len(set(x).intersection(set(y))), right_list))

    # Now we chekc if any elements in x but not in y
    # So it is in the x but not in my right list
    # Need to chekc this

    no_mis_match = list(map(lambda y: set(y).difference(set(x)) == set(), right_list))
    # Convert to interger
    no_mis_match = list(map(int, no_mis_match))
    # The multiplication will remove values where tehre is a mis-match
    match_len = list(map(lambda x, y: x * y, match_len, no_mis_match))

    if sum(match_len) == 0:
        return np.nan

    max_match = max(match_len)

    if max_match > 0:
        # Get the elements where we get the most matches
        match_found = list(map(lambda x: x == max_match, match_len))
        if sum(match_found) > 1:
            return np.nan

        # match_element=filter_match_list.loc[filter_match_list==max_match]

        match_value = [x for x, flg in zip(right_list, match_found) if flg]
        # We pick the first elemet where it matches
        # match_element=match_element.index[0]
        return match_value[0]
    else:
        return np.nan


def f_new_match_idx(
    left_list: list, right_list: list, both: bool = False
) -> Union[pd.Series, pd.DataFrame]:
    # The function above chekc for each element x if it cna find an appropriate match in right_list
    # We now loop through left_list and chekc each element
    # A small deviation is that if we want an outer join, then we match agaisnt both

    # NB the lsit has to be a unique set of values

    if not both:
        # match_list=left_list.apply(lambda x: match_element(x,right_list))
        match_list = [f_new_match_element(x, right_list) for x in left_list]
        match_list = pd.Series(match_list, index=left_list)
        return match_list
    else:
        com_list = pd.concat([left_list, right_list], ignore_index=True).unique()
        com_list = pd.Series(com_list)
        left_match = [f_new_match_element(x, left_list) for x in com_list]
        right_match = [f_new_match_element(x, right_list) for x in com_list]
        df = pd.DataFrame(
            {"left_list": left_match, "right_list": right_match}, index=com_list
        )
        return df


def log_decorator(func):
    """
    A decorator that logs the runtime of the decorated function and appends it to the `output_runtimes` attribute
    of the first argument if it has either `scr` or `output_runtimes` attributes.
    This decorator also ensures that the decorated function retains its original name and docstring.

    :param func: The function to be decorated.
    :type func: function
    :return: The wrapped function with added logging functionality.
    :rtype: function

    The decorator measures the time taken by the function to execute and appends the runtime information to the
    `output_runtimes` list of the first argument if it has the `scr` or `output_runtimes` attribute.

    :Example:
    >>> @log_decorator
    ... def create_prem_res():
    ...     return PremRes(sam_scr, True)
    >>>
    >>> prem_res = create_prem_res()
    """

    # Add this line to ensure that Sphnx documents the functions correctly.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start

        # Need to see fi there is a better way to process this.
        # We look at the first argument to see if it has the attibute scr
        # our output_runtimes.
        if args and hasattr(args[0], "scr"):
            parent_scr = args[0].scr
        elif hasattr(args[0], "output_runtimes"):
            parent_scr = args[0]

        if parent_scr is not None:
            parent_scr.output_runtimes.append(
                {
                    "module": func.__module__,
                    "function": func.__name__,
                    "runtime": elapsed,
                }
            )
        return result

    return wrapper


def f_best_match_new(x, join_list):
    """Function not used, repalce with f_new_match_element."""
    # The new version is a little more robust and does more checks
    # Need to check on the speed of the new version
    # blank=set()
    if x in join_list:
        return x
    else:
        count_intersect = pd.Series(
            map(
                lambda i: len(set(i).intersection(set(x)))
                * int(set(i).difference(set(x), join_list) == set()),
                join_list,
            )
        )

        max_value = max(count_intersect)
        if max_value > 0:
            count_intersect = count_intersect == max_value
            if sum(count_intersect) == 1:
                filtered = np.array(join_list)[count_intersect]
                return filtered[0]
            else:
                return np.nan
        else:
            return np.nan
