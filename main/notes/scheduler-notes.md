redesign

separate shifts into shifts-with-offset
- map children to shifts-with-offset, so that no two children get the same shift-with-offset
- if family's preferences don't distinguish offsets, assign same rank to both offsets of given shift
- if a family owes two commitments per month, then they see offsets 0, 1
- if a family owes one commitment per month, then they see offsets 0, 1, 2, 3
- then commitments are generated deterministically from the shiftassignment



<!-- simple version - assume each family has duty 2, try to map families to first-preferred shifts -->

<!-- elaborated  -->
<!-- - break period into months -->
<!-- - assign num_duties[f] shifts in each month to each family f -->
<!-- - represent this as: assign an n-tuple of shifts for each month, for n = num_duties[f] -->
<!--     - require values not overlap -->
<!-- - optimize preference score -->
<!-- - minimize variances of -->
<!--     - time between shifts -->
<!--     - time of shifts -->
