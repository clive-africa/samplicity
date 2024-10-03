# Known Issues
This document details the various known issues, concerns, development areas and areas of (potential) contention within the *Samplicity* tool.

## Premium & Reserve Risk

### Lines of business
The FSI is not very clear on how the (sub-) lines of business should be split. There are a couple areas of uncertainty:
- Should direct, proportional, faculatative proportional, ect be allocated to the same entires in the matrix or split out.
- Should lines 18b & 18e be grouped together.
- Should lines 18c & 18f be grouped together.
- How does one treat non-proportional and other risk mitigation where the underlying business is known.

The tool has used the methodology where:
-18b & 18e are grouped together
-18e & 18f are grouped together.

Other practitioners do perform the calculation differently.

## Factor Based Catastrophe Risk
The FSI seems to be contradictary on the treatment of the Major Marine, Aviation and Transit (MAT) disaster event. The FSI notes that this event is applicabel to calsses classes 5i, 6i and 7i. However, unlike for all the other disaster evetns it does not inlcude teh text *"Corresponding proportional reinsurance (sub-)lines of business to those above (18a and 18d)."* This appears to be an oversgith. The tool applies the shcoks to the Facultative and Proportional business.

This may not be consistent with other approaches used in the market.

## Concentration Risk
The issues of 'disallowed' assets within a bank causes