==============
Samplicity
==============

*samplicity* is a Python library to calculate the SAM SCR for a South African non-life insurer.
The package attempts to calculate the SCR in accordance with the Financial Soundness Standards that can be found `here <https://www.resbank.co.za/content/dam/sarb/publications/prudential-authority/pa-department-documents/Prudential%20Standards%20Financial%20Soundness%20Standards%20for%20Insurers.zip>`_

Importantly the package allows for a multiple SCR calculations to be performed simultaneously. 
This allows for the easy calcualtion of diversification benefits across various business lines, divisions, insurance classes, etc. 

The package has succesfully performed more than 60 000 SCR calculations in test environments - in matter of minutes. 
This efficiency is obtained through the use of Einstein summation in numpy. 
This prevents slow looping in Python and leverages off fast parallel matrix multiplication in numpy.
Interested readers can find more information on Einstein summation 'here <https://numpy.org/doc/stable/reference/generated/numpy.einsum.html>`_

-----------------
Further Reading
-----------------
There is further documentation that user can read to gain familiartiy with the *samplicity* package.
There is detailed in the navigation pane to the left.

---------------------
Class Documentation
---------------------
*samplicity* is supported by various classes.
Specific documentation on each class can be found in the navigation pane to the left.

---------------------
Indices and Tables
---------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`