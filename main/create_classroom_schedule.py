from django.db import transaction
from people.models import User, Child, Classroom
from main.models import Shift, CareDay
from main.model_fields import WEEKDAYS

SHIFT_TIMESPANS = [('8:30', '10:30'), ('13:30', '15:30'), ('15:30', '17:30')]
CAREDAY_TIMESPANS = [('8:30', '15:30'), ('15:30', '17:30')]

@transaction.atomic
def create_shifts(classroom):
    for w in WEEKDAYS:
        if int(w) < 5:
            for st in SHIFT_TIMESPANS:
                Shift.objects.create(weekday=w,
                                     start_time = st[0],
                                     end_time=st[1],
                                     classroom=classroom)

@transaction.atomic
def create_caredays(classroom): 
    for w in WEEKDAYS:
        if int(w) < 5:
            for start_time, end_time in CAREDAY_TIMESPANS:
                CareDay.objects.get_or_create(weekday=w,
                                              start_time=start_time,
                                              end_time=end_time,
                                              classroom=classroom)
