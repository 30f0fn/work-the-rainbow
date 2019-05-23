def si_by_date():
    qs = ShiftInstance.objects.filter(classroom=classroom).select_related('commitment', 'shift')
    print("--------\n--------\n--------\n")
    ls = list(qs)
    
    return qs


# BELOW IS MAYBE A REASONABLE DATASTRUCTURE FOR CALENDAR
 

for si in lqs:
    if si.date in d:
        d[si.date].append(si)
    else:
        d[si.date]=[si]

from collections import defaultdict

d = defaultdict()

qs = ShiftInstance.objects.filter(
    date__gte=start_date,
    date__lte=end_date,
    classroom=classroom)
[d[si.date].append(si) for si in qs]
 
