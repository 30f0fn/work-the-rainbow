import random
import constraint
from constraint import *
import itertools

from main.models import Shift, WorktimeAssignment, WorktimeCommitment
from people.models import Classroom, Child

for each month and family, build each possible assignment of shiftinstances

shift_instances = ShiftInstance.objects.filter(shift__shiftpreference__family=child,
                                               shift__shiftpreference__rank=1)

months = [(start + m, end + m)
          for m in [datetime.timedelta(days=28*n)
                      for n in range(4)]]


