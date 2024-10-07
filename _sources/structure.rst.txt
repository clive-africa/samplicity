================================
Samplicity Strcuture
================================

The Samplicity package is designed to calculate the Solvency Assessment and Management (SAM) Solvency Capital Requirement (SCR) for non-life insurers.
It consists of several interconnected classes that work together to perform various aspects of the calculation.

--------------
Main Classes
--------------

SCR
=============

The ``SCR`` class is the central class of the Samplicity package. It orchestrates the entire SCR calculation process and manages the interaction between other classes.

Key responsibilities:
- Initializing and managing other classes
- Coordinating the calculation steps
- Aggregating results from various risk modules
- Handling data import and export

Data
=============

The ``Data`` class is responsible for importing, managing, and exporting data used in the SCR calculations.

Key responsibilities:
- Importing data from Excel or databases
- Validating and preprocessing input data
- Exporting calculation results

Risk Module Classes
=======================

PremRes
--------------

The ``PremRes`` class calculates the premium and reserve risk component of the SCR.

NatCat
--------------

The ``NatCat`` class handles the natural catastrophe risk calculations.

FactorCat
--------------

The ``FactorCat`` class computes the factor-based catastrophe risk.

ManMade
--------------

The ``ManMade`` class calculates the man-made catastrophe risk component.

NonProp
--------------

The ``NonProp`` class handles the non-proportional reinsurance risk calculations.

Market
--------------

The ``Market`` class computes various market risk components, including interest rate, equity, property, spread, and concentration risks.

Reinsurance
--------------

The ``Reinsurance`` class calculates reinsurance recoveries and net risk charges.

OpRisk
--------------

The ``OpRisk`` class computes the operational risk component of the SCR.

-------------------------------
How the Classes work together
-------------------------------

1. The ``SCR`` class initializes all other classes and stores them in its `classes` dictionary.

2. Using the ``Data`` class the necessary input data, PA data metadata and is imported and stored in the respective `data`, `pa_data` and `metadata` dictionaries.

3. During the calculation process, the ``SCR`` class calls methods from each risk module class in a specific order:

   a. Premium and Reserve Risk (``PremRes``)
   b. Natural Catastrophe Risk (``NatCat``)
   c. Factor Catastrophe Risk (``FactorCat``)
   d. Man-Made Catastrophe Risk (``ManMade``)
   e. Non-Proportional Reinsurance Risk (``NonProp``)
   f. Reinsurance Risk (``Reinsurance``)
   g. Operational Risk (``OpRisk``)
   h. Market Risk (``Market``)

4. The ``Data`` class is used throughout the process to provide input data and store calculation results.

5. After individual risk modules complete their calculations, the ``SCR`` class aggregates the results using correlation matrices and diversification effects.

6. Finally, the ``SCR`` class computes the overall Solvency Capital Requirement - allowing for LACDT - and stores the results.

-------------------------------
Usage Example
-------------------------------

.. code-block:: python

    import samplicity as sam

    # Create an SCR instance
    sam_scr = sam.scr.SCR()

    # Import data
    sam_scr.f_import_data(
        risk_free_rates="path/to/risk_free_rates.xlsx",
        symmetric_adjustment="path/to/symmetric_adjustment.xlsx",
        data_file="path/to/input_data.xlsx"
    )

    # Perform SCR calculation
    sam_scr.f_calculate()

    # Export results
    sam_scr.f_export_results("path/to/output.xlsx")

This structure allows for a modular and extensible approach to SCR calculations, making it easier to maintain and update individual risk components as regulatory requirements change.