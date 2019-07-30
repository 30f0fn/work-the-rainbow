import random
import constraint
from constraint import *
import itertools
import rules

from allauth.account.models import *
from invitations.models import *

from people.models import *
from  main.models import *

def randy_str():
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(3)])





# shifts = Shift.objects.all()
for c in classroom.child_set.all():
    s = random.choice(shifts)
    sp = ShiftPreference(family=c, shift=s, rank=1)
    sp.save()
    print(sp)
    
# families = {f:fam for f, fam in enumerate(classroom.child_set.all())}


def display_assignment(asgn):
    for l in asgn:
        pretty = "{}: {}".format(l, asgn[l])
        print(pretty)

for asgn in problem.getSolutions():
    print("\n-------")
    display_assignment(asgn)






def generate_problem():
    cr_name = randy_str().upper()
    classroom = Classroom(name=cr_name, slug=cr_name)
    # classroom.save()
    # print(f"created classroom {classroom}")
    problem = Problem()
    families = list(range(10))
    for f in families:
        problem.addVariable(f, [random.choice(shifts)]) 
    for c1,c2,c3 in itertools.combinations(families, 3):
        problem.addConstraint(lambda s1, s2, s3:
                              not(s1 == s2 == s3),
                              [c1, c2, c3])
    return problem



def frac_solvable(num_tests):
    def yes():
        return len(generate_problem().getSolutions())
    return sum([yes() for i in range(num_tests)])/num_tests


