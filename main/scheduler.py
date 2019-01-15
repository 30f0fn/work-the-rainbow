import random
import constraint
from constraint import *
import itertools

from main.models import Shift, FamilyAssignment, FamilyCommitment
from people.models import Classroom, Child

"""
SIMPLE VERSION: just try to map shifts to families
"""

def get_optimal_shift_assignments(classroom, period):
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
    return [FamilyAssignment(family=families[f],
                             period=period,
                             shift=solution[f])
            for f in range(len(families))]

# for each shift, generate its instances in the period
# get the families to whom it's assigned
# apportion instances to families
def generate_commitments(classroom, period):
    for s in Shift.objects.all():
        families = Child.objects.filter(familyassignment__shift=s)
        shift_instances = s.instances_in_period(period)
        for index, family in enumerate(families):
            for instance in shift_instances[index::2]:
                FamilyCommitment.objects.get_or_create(family=family,
                                                shift_instance=instance)
  
    
    
