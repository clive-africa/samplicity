"""
A class to handle data operations for the Solvency Capital Requirement (SCR) calculation.

This class is responsible for importing, processing, and exporting data used in the SCR calculations.
It serves as a crucial component in the SCR calculation process, providing data management and
validation functionalities.

The class is split across several modules:
    - **data.py:** The main class file containing core data handling functions
    - **access.py:** Functions for interacting with MS Access databases
    - **excel.py:** Functions for reading from and writing to Excel files
    - **odbc.py:** Functions for ODBC database connections and operations
    - **data_models.py:** Pydantic models for data validation, still under development
    - **data_validation.py:** Functions for validating imported data, still under development

The Data class supports various data sources and formats, ensuring flexibility in data input and output
for SCR calculations. Future plans are to implement data validation to ensure the integrity and correctness of
imported data before it's used in SCR calculations.

Note:
    This class is designed to be used in conjunction with the SCR class and its various risk modules.
    It provides the necessary data infrastructure for accurate and efficient SCR calculations.
"""
