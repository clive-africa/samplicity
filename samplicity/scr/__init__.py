"""
A class to calculate the Solvency Capital Requirement (SCR) for a non-life insurer using the SAM standard formula.

This class serves as the main orchestrator for the SCR calculation process, coordinating various risk modules
and aggregating results. It handles data import, calculation steps, and result export.

The class is split out across a couple different modules:
    - **scr.py:** The main class file
    - **aggregation.py:** Aggregation functions for the SCR class
    - **lacdt.py:** Loss Absorbing Capacity of Deferred Tax (LACDT) calculations
    - **diversification.py:** Diversification calculations
    - **info.py:** Information functions for the SCR class
    - **solver.py:** Solver functions for the SCR class, currently under development

"""
