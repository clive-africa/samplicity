from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
import pandera.pandas as pa
import numpy as np

if TYPE_CHECKING:
    from .data import Data

# Import the data models that are stored as classes
from .data_models import AssetData, NatCat, PremRes, ReinsuranceProg, ReinsuranceShare, AssetShocks

# Import the standard data models
from .data_models import division_detail_schema, reinsurance_schema, counterparty_schema


# We create a dictionary of all the vlaidatiosn that we need to process
# The name should match up to the name of the imported variable


def f_validate_import(sam_data: Data):
    """Validate the imported data dictionary against the schemas defined in the data models."""

    # We map the different data models to their respective dataframes
    validations = {
        "division_detail": division_detail_schema,
        "counterparty": counterparty_schema,
        'asset_shocks': AssetShocks(sam_data),
        "asset_data": AssetData(sam_data),
        "ri_contract": reinsurance_schema,
        "ri_contract_share": ReinsuranceShare(sam_data),
        "prem_res": PremRes(sam_data),
        "nat_cat_si": NatCat(sam_data),
    }

    all_errors = []  # Collect all errors
    validation_results = {}  # Store successful validations

    summary_stats = {
        "total_schemas": len(validations),
        "successful_validations": 0,
        "failed_validations": 0,
        "input_rows": 0,
        "output_rows": 0,
        "total_error_rows": 0,
        "total_errors": 0,
    }

    for key, schema in validations.items():
        df = sam_data.output["data"][key]

        try:
            new_df = schema.validate(df, lazy=True)
            validation_results[key] = new_df
            summary_stats["successful_validations"] += 1
            summary_stats["input_rows"] += len(df)
            summary_stats["output_rows"] += len(new_df)
            print(f"✓ {key}: Validation successful")

        except pa.errors.SchemaErrors as e:
            print(f"✗ {key}: Validation failed")

            # Create error DataFrame with additional context
            error_df = pd.DataFrame(e.failure_cases)

            # Add context columns
            error_df["data_key"] = key
            error_df["schema_name"] = getattr(
                schema, "name", str(type(schema).__name__)
            )

            # Add timestamp for tracking
            error_df["validation_timestamp"] = pd.Timestamp.now()

            error_df["input_rows"] = len(df)
            error_df["output_rows"] = len(new_df)
            distinct_errors = error_df["index"].nunique()
            error_df["distinct_error_rows"] = distinct_errors
            error_df["failure_cases"] = len(e.failure_cases)
            error_df["error_percentage"] = np.round(distinct_errors / len(df) * 100, 2)

            # Reorder columns to put context first
            context_cols = [
                "data_key",
                "schema_name",
                "validation_timestamp",
                "input_rows",
                "output_rows",
                "distinct_error_rows",
                "failure_cases",
                "error_percentage",
            ]
            other_cols = [col for col in error_df.columns if col not in context_cols]
            error_df = error_df[context_cols + other_cols]

            all_errors.append(error_df)
            summary_stats["failed_validations"] += 1
            summary_stats["input_rows"] += len(df)
            summary_stats["output_rows"] += len(new_df)
            summary_stats["total_errors"] += len(e.failure_cases)
            summary_stats["total_error_rows"] += distinct_errors

        except Exception as e:
            print(f"✗ {key}: Unexpected error - {str(e)}")
            # Create error record for unexpected errors
            unexpected_error = pd.DataFrame(
                [
                    {
                        "data_key": key,
                        "schema_name": getattr(
                            schema, "name", str(type(schema).__name__)
                        ),
                        "validation_timestamp": pd.Timestamp.now(),
                        "input_rows": None,
                        "output_rows": None,
                        "distinct_error_rows": None,
                        "failure_cases": None,
                        "error_percentage": None,
                        "error_type": "UNEXPECTED_ERROR",
                        "error_message": str(e),
                        "schema": key,
                        "column": None,
                        "check": None,
                        "check_number": None,
                        "failure_case": str(e),
                    }
                ]
            )
            all_errors.append(unexpected_error)

    # Combine all errors into a single DataFrame
    if all_errors:
        non_empty_errors = [df for df in all_errors if not df.empty]
        if non_empty_errors:
            combined_errors = pd.concat(non_empty_errors, ignore_index=True)

        # Print summary
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        for key, value in summary_stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("=" * 50)

        return validation_results, combined_errors
    else:
        print("\n✓ All validations passed successfully!")
        return validation_results, pd.DataFrame()  # Empty error DataFrame


