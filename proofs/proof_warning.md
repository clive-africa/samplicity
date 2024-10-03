# Proof and Testing Code

This folder contains various prrof and tests to show users how *Samplicity* functions.

It contains code to *inject* certain information into the scr class. This is done to perform the tests and should typically never be done in a *production* environment unless there are very good reasons for the behaviour.

Currently the following proofs are implemented, as detailed below.

## Natural Catastophe Risk
The prrof performs a check on natural catstrophe risk for earthquake, hail, horizontal 10 and horizontal 20. To perform the test sums insured have beennpopulated for all post codes (1 to 9 999) and then random sum insured are populated for buidlings, contents, engineering & motor.

The natural catastrophe risk is calcaulted in Excel and then comapred to the results in Python. The comparison in Python is hardcoded. We could improve this.


## Premium and Reserve Risk
This test is still being actively developed.

