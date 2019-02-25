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
    for f, family in enumerate(families): 
        accepted_shifts = Shift.objects.filter(
            shiftpreference__family=family,
            shiftpreference__rank=1)
        problem.addVariable(f, accepted_shifts)
    for c1,c2,c3 in itertools.combinations(range(len(families)), 3):
        problem.addConstraint(lambda s1, s2, s3: not(s1 == s2 == s3),
                              [c1, c2, c3])
    solution = problem.getSolutions()[0]
    return [WorktimeAssignment.objects.get_or_create(family=families[f],
                                                     period=period,
                                                     shift=solution[f])
            for f in range(len(families))]


# for each shift, generate its instances in the period
# get the families to whom it's assigned
# apportion instances to families
def create_commitments(classroom, period):
    for s in Shift.objects.all():
        families = [wtc.family for wtc in s.worktimeassignment_set.all()]
        shift_instances = s.instances_in_date_range(period.start_date, period.end_date)
        for index, family in enumerate(families):
            # alternate weeks to assign
            for instance in shift_instances[index::2]:
                commitment = instance.create_commitment(family)
                print(commitment)

  
