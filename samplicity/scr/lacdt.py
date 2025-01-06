import pandas as pd


def f_lacdt_calculation(sam_scr, base_scr):
    """Aggregate the lacdt amounts."""
    # logger.debug("Function start")

    lacdt = sam_scr.f_data("data", "data", "division_detail")

    # An approximation is used here where we typically would not have
    # assets for each and every product, diversification grouping
    # Instead we add the products, this assumes independence
    # May not always be true.
    # I believe this is a far better approximation than others use.
    # The tax rate and the LACDT for the entire entity is a seperate input.
    # This avoids any errors and/or approximations for the overall entity.
    div_level = sam_scr.f_data("data", "data", "diversification_level").iloc[0]

    div_level_list = sam_scr.output["list_combinations"].iloc[:, 0].values.tolist()
    max_element = [len(x) for x in div_level_list]

    if max_element[len(max_element) - 1] != max(max_element):
        raise Exception(
            "scr",
            "f_lacdt_calculation",
            "diversification listing is incorrect",
            "",
        )

    tax_calc = pd.DataFrame(div_level_list[:-1], index=div_level_list[:-1])

    tax_calc = tax_calc.stack().reset_index(drop=True, level=1)
    tax_calc = pd.DataFrame(tax_calc, columns=["div_level"])
    tax_calc["index"] = tax_calc.index
    tax_calc = tax_calc.merge(
        lacdt[[div_level, "tax_percent", "max_lacdt"]],
        left_on="div_level",
        right_on=div_level,
        how="left",
    )
    tax_calc = tax_calc.drop(["div_level", div_level], axis=1)

    # The 'df_total' stores the actual figures for the overall entity.
    df_total = pd.DataFrame(
        0.0, columns=tax_calc.columns, index=[div_level_list[len(div_level_list) - 1]]
    )
    df_total["tax_percent"] = (
        sam_scr.f_data("data", "data", "tax_percent").astype(float).fillna(0.0).iloc[0]
    )
    df_total["max_lacdt"] = (
        sam_scr.f_data("data", "data", "max_lacdt").astype(float).fillna(0.0).iloc[0]
    )
    df_total["index"] = [div_level_list[len(div_level_list) - 1]]
    tax_calc = pd.concat([tax_calc, df_total])
    tax_calc[["tax_percent", "max_lacdt"]] = tax_calc[
        ["tax_percent", "max_lacdt"]
    ].fillna(0)

    # Convert our dictionary to a dataframe
    base_scr = pd.concat(base_scr.values(), axis=1)
    base_scr.columns = [chrg + "_base_scr" for chrg in base_scr.columns.values]

    tax_calc = tax_calc.merge(base_scr, left_on="index", right_index=True, how="inner")
    for chrg in ["gross", "net", "impairment", "gross_return"]:
        tax_calc[chrg + "_lacdt"] = tax_calc[chrg + "_base_scr"] * tax_calc.tax_percent

        tax_calc[chrg + "_lacdt"] = tax_calc[chrg + "_lacdt"].where(
            tax_calc[chrg + "_lacdt"] > tax_calc["max_lacdt"],
            other=tax_calc["max_lacdt"],
        )

    # Can't exceed the
    tax_calc[chrg + "_lacdt"] = tax_calc[chrg + "_lacdt"].where(
        tax_calc[chrg + "_lacdt"] < tax_calc["max_lacdt"],
        other=tax_calc["max_lacdt"],
    )

    # We only need these 3 fields for the rest of the calculation
    cols = ["gross", "net", "impairment", "gross_return"]
    cols = [chrg + "_lacdt" for chrg in cols]
    tax_calc = tax_calc[["index", *cols]].groupby(by="index", as_index=True).sum()

    return tax_calc
