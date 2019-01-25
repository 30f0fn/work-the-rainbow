simple version - assume each family has duty 2, try to map families to first-preferred shifts

elaborated 
- break period into months
- assign num_duties[f] shifts in each month to each family f
- represent this as: assign an n-tuple of shifts for each month, for n = num_duties[f]
    - require values not overlap
- optimize preference score
- minimize variances of
    - time between shifts
    - time of shifts
