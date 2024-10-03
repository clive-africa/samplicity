=================
Known Issues
=================

--------------
Introduction
--------------
This document details the various known issues, concerns, development areas and areas of (potential) contention within the *samplicity* tool.

----------------------------
Premium and Reserve Risk
----------------------------
The FSI is not very clear on how the (sub-) lines of business should be split.
There are a couple areas of uncertainty: 
- Should direct, proportional, faculatative proportional, etc be allocated to the same entires in the matrix or split out. 
- Should lines 18b & 18e be grouped together. 
- Should lines 18c & 18f be grouped together. 
- How does one treat non-proportional and other risk mitigation where the underlying business is known.

The tool has used the methodology where: 
-18b & 18e are grouped together 
-18e & 18f are grouped together.

Other practitioners do perform the calculation differently.
   
------------------------------
Factor Based Catastrophe Risk
------------------------------
The FSI seems to be contradictary on the treatment of the Major Marine, Aviation and Transit (MAT) disaster event. 
The FSI notes that this event is applicable to classes classes 5i, 6i and 7i. 
However, unlike for all the other disaster evetns it does not include the text "Corresponding proportional reinsurance (sub-)lines of business to those above (18a and 18d)." 
This appears to be an oversgith. The tool applies the shcoks to the Facultative and Proportional business.

This may not be consistent with other approaches used in the market.

------------------------------
Concentration Risk
------------------------------
The tools doesn't allow for disallowed assets that may exist within insurer's that are part of banking groups.

------------------------------
Python Design
------------------------------
A couple design choices have been made that could be criticised. However, soem trade-offs needed to be made.

Object Orientated Approach
==================================
*Samplciity* uses an object orienatted approach (OOP). It was felt that this was appropriate for this type of project.
The use of classes was intentional, the idea was to make a set of 'classes' that can be re-used fro different calculations - for example an ORSA.

A challenge in prior projects was how the different values were manipulated by different functions and/or routines. This has been avoided in this project.

Splitting of Classes
==================================
A number of lcasses in this project are split across multiple modules. These inlcude:
- ``SCR``
- ``Data``
- ``Reinsurance``

These classes are probalby around 1 000 lines long - they are not exceptionally large.
A more Pythonic method may ahve been to include all the code in a single module.
Alternatively we could ahve split the classes into multiple classes.
Ultimately it was decided to use a few smaller modules to improve the readbility of the code.
Future editiosn of *samplicity* may make changes to this.
It is likely that the ``Data`` class will be split into multiple classes - Excel, database, data validation