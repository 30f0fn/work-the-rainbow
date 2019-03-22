import random
import constraint
from constraint import *
import itertools

from main.models import Shift, ShiftAssignment
from people.models import Classroom, Child

"""
SIMPLE VERSION: just try to map shifts to families
"""

def create_optimal_shift_assignments(classroom, period):
    problem = Problem()
    families = Child.objects.filter(classroom=classroom)
    for f, child in enumerate(families): 
        accepted_shifts = Shift.objects.filter(
            shiftpreference__child=child,
            shiftpreference__rank=1)
        problem.addVariable(f, accepted_shifts)
    for c1,c2,c3 in itertools.combinations(range(len(families)), 3):
        problem.addConstraint(lambda s1, s2, s3: not(s1 == s2 == s3),
                              [c1, c2, c3])
    solution = problem.getSolutions()[0]
    return [ShiftAssignment.objects.get_or_create(child=families[f],
                                                     period=period,
                                                     shift=solution[f])
            for f in range(len(families))]


# for each shift, generate its instances in the period
# get the families to whom it's assigned
# apportion instances to families
def create_commitments(classroom, period):
    for sh in Shift.objects.all():
        families = [sha.child for sha in sh.shiftassignment_set.all()]
        sh_occs = list(sh.occurrences_for_date_range(period.start, period.end))
        print(sh_occs)
        print(families)
        for index, child in enumerate(families):
            # alternate weeks to assign
            for occ in sh_occs[index::2]:
                commitment = occ.create_commitment(child)
                print(commitment)

  
