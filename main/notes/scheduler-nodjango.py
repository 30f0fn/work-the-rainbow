import random
import constraint
from constraint import *
import itertools

from models import ShiftPreference

"""
SIMPLE VERSION: just try to map shifts to families, then override manually in case of clash... but what to do about holidays?


FANCY VERSION: map shiftinstances in a way that minimizes variance

split into monthly problems, then glue them together
among the resulting possible assignments, pick one that
- gets best overall preference score
- minimizes variance, between families, in individual family preference scores
- minimizes sum of the variance, for each family, of time elapsed between their shifts
- minimizes sum of variance, for each fam, of shifts

- for each month in the period, construct set of all its ShiftInstances
- for each month mon and each family fam, assign num_obligs(fam) ShiftInstances in mon to fam
- in constructing assignments, first attempt optimal preference score
- if that fails, then for each family, try 
"""

children = ["Finn",
            "Zafi",
            "Theo",
            "Henry",
            "Eleanor",
            "Tate",
            "Vera"]

pref = {}
pref["Finn"] = ([(3,2)], [(0,2)], [(2, 0)])
pref["Zafi"] = ([(2, 0)], [(0, 0)], [(1, 0)])
pref["Theo"] = ([(3, 2)], [(4, 1)], [(2, 1)])
pref["Henry"] = ([(3, 0)], [], [])
pref["Eleanor"] = ([(0, 2)], [(2, 2)], [(2, 0)])
pref["Tate"] = ([(1, 0), (4, 0)], [(4, 2)], [(4, 0)])
pref["Vera"] = ([(4, 1)], [(3, 0)], [(4, 0)])
pref["Emmett"] = [(3, 0), (0, 0)] 

first_prefs = {kid:pref[kid][0] for kid in pref}

problem = Problem()
for child in children:
    problem.addVariable(child, [slot for slot in first_prefs[child]])

for c1,c2,c3 in itertools.combinations(children, 3):
    problem.addConstraint(lambda s1, s2, s3:
                          not(s1 == s2 == s3),
                          [c1, c2, c3])

def display_slot(s):
    d1 = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    d2 = ["8:30-10:30", "1:30-3:30", "3:30-5:30"]
    return "{}, {}".format(d1[s[0]], d2[s[1]])

def display_assignment(asgn):
    for l in asgn:
        pretty = "{}: {}".format(l, display_slot(asgn[l]))
        print(pretty)

for asgn in problem.getSolutions():
    print("\n-------")
    display_assignment(asgn)


