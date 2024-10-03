# Samplicity Classes
The *Samplicity* package mades use of various classes and helper modules. This document provides a detailed overview of the different classes.

The main classes is the scr class, all of the other classes (child classes) are called by the scr class to perform the various calculations.

## scr
This is the 'main' class that orchestrates the calculation. This is the class that will mainly be used by users to perform the SCR calculation. 

The purpose of the class is to:

* Provide the main interface to the user.
* Orchestrate and call all of the supporting classes.
* Perform the necessary aggregation functions as required by the SCR.
* Perform the LACDT calculations as required.

## Generic Structure
As far as possible we have tried to keep a similar structure across the different classes - particular the child classes of the main scr class.

There are a couple key features to most classes:

* All the supporting classes keep a reference to the main scr class in the variable *scr*.
* Output variable are stored in the dictionary *output*.
* When the various child classes are added they are stored in the dictionary 'classes' in the main scr class.
* When the class is intitialized, the data work required by the class is performed.
* By default the necessary calcualtion are are run when the class is initialized - but this can be overridden.
* All of the child classes have an *f_data*  function to access data within the class - thsi function is discussed below.

### f_data
A challenge of the SCR calculation is that data is used by multiple calculations - any certain functions are used across different areas of the calculation. A goal of the project was to limit data being edited across the different child classes. To prevetn this data is never accessed direct from the *output* dictionary - instead the f_data function is used. Furthermore, although each child class has a *f_data* function the function is never called directly. Instead the *f_data* function from the main scr class is called. It is the job of the *scr* classes to call the relvant *f_data* function in the required child class. Thi si done to ensure that future changes to the code can be accomodated through a single hcange to the main scr class - and try prevent the need for edit to multiple child classes and support code file.

To get a list of all possible data that can be extracted one can simply run the code:

```Python
df = sam_scr.f_info()
```

There might be one or two errors that result from this function but it gives users a very detailed overview of the information available - and how the data is stored.

## data
This class contains the various routines used to import data into the calculation. The SCR calculation, broadley, requires 3 sets of information:

### metadata
This is the metadata required by the SCR calculation - correlation matrices, premium and reserve risk charges, loss given defaults, etc. Thsi data is not imported each time but is rather stored as a *pickle* file within the package. This helps ensure data is not edited and improves calculation speed.

### pa_data
For each valuation we need need to update our various inputs supplied by the PA. This are the:

* Equity symmetric adjsutments; and
* Risk free rates.

*Samplicity* has been designed to allow for the automated import fo these files. The suer only needs to supply the location of the Excel workbooks - provided the format of the Excel workbooks has not been edited. As aprt of the import routine some automated checks of the file are performed.

### data
The SCR calcualtion requires various imports as aprt of the calculation. These imports can be imported from ether a database (preferred) or an Excel file. *Samplicity* performs some (very) limited validation of the data. This data needs to be updated for each valuation. It must be noted that it is not the role and/or purposes of *Samplicity* to ensure that the data is valid and correctly input. This is the role of the user and the decided input mechanism.

## prem_res
This class performs the calculation of premium and reserve risk. Importantly we perform three different types of premium and reserve risk calculations:
* Gross: This is the gross premium and reserve risk with no allowance for reinsurance.
* Actual Net: The is mainly for information and checking purposes. This is the premium and reserve risk based on the net premiums and reserves - which should be entered as per the financial statements.
* Calculated Net: This is the premium and reserve risk net of reinsurance arrangements as captured in *Samplicity*. This is calculation that is used throughout *Samplicity*.

## nat_cat
This class performs the calculation of natural catastrophe risk. The class performs all of the mapping of the exposure information into *zones* and then performs the different natural catastrophe calculations:
* Earthquake
* Hail
* Horizontal 10
* Horizontal 20
## man_made
This class performs the calculation of man-made catastrophe risk.
## non_prop
This class performs the calculation of non-proportional catastrophe risk.
## factor_cat
This class performs the calculation of factor based catastrophe risk.
## reinsurance
This class provide the functionality for all the reinsurance calculations.
## op_risk
This calculates the operational risk capital requirements. This inputs for the calculation are captured in the input *prem_res*.
## market
This class performs the calculation of market risk. The class is further supported by smaller supporting classes. This is done given the complexity of some of the market risk calculations.
## helper (Not a class)
This is not a calss. It is a module with various helper functiosn used by the various classes. This module contaisn various miscellaneous functions.

[Go Home](https://bitbucket.org/omi-it/samplicity/src/main/documentation/main.md)
