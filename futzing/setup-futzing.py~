#################
# generic setup #
#################

import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.scheduler import *

child = Child.objects.first()
classroom = Classroom.objects.first()
period = Period.objects.filter(classroom=classroom).first()
shift = Shift.objects.first()

###############
# local stuff #
###############



problem = Problem()

families = Child.objects.filter(classroom=classroom)

for f, family in enumerate(families):
    accepted_shifts = Shift.objects.filter(
        shiftpreference__family=family,
        shiftpreference__rank=1)
    print(family, accepted_shifts)


osa = get_optimal_shift_assignments(classroom, period)
[sa.save() for sa in osa]
generate_commitments(classroom, period)


