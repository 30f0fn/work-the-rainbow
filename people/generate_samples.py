import itertools, random

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from people.models import User, Child, Classroom
from main.models import WorktimeCommitment, Period, Shift, CareDay, ShiftPreference, CareDayAssignment, WorktimeSchedule
from main.model_fields import WEEKDAYS
from tests.main.test_utils import random_str


"""
given scheduler's email and classroom_name
add classroom with name sample_classroom_name
add children (and parents?) to classroom
add two periods for each classroom, one expiring Aug 31 and populated by commitments, another beginning Sept 1 and populated by shiftpreferences
"""

SHIFT_TIMESPANS = [('8:30', '10:30'), ('13:30', '15:30'), ('15:30', '17:30')]
NUM_KIDS_PER_CLASSROOM = 10
NUM_PERIODS = 2
PERIOD_LENGTH = relativedelta(months=4)
PERIODS_START = timezone.now().replace(month=1, day=1)
CAREDAYASSIGNMENT_END=PERIODS_START + PERIOD_LENGTH * 3
while PERIODS_START + PERIOD_LENGTH < timezone.now():
    PERIODS_START += PERIOD_LENGTH

def create_classroom(classroom_name):
    return Classroom.objects.create(name=classroom_name)

def create_shifts(classroom):
    for w in WEEKDAYS:
        if int(w) < 5:
            for st in SHIFT_TIMESPANS:
                Shift.objects.create(weekday=w,
                                     start_time = st[0],
                                     end_time=st[1],
                                     classroom=classroom)

def create_caredays(classroom): 
    for w in WEEKDAYS:
        if int(w) < 5:
            CareDay.objects.get_or_create(weekday=w,
                                          start_time='8:30',
                                          end_time='15:30',
                                          classroom=classroom)
            CareDay.objects.get_or_create(weekday=w,
                                          start_time='15:30',
                                          end_time='17:30',
                                          classroom=classroom)

def create_periods(classroom, start=PERIODS_START, num_periods=NUM_PERIODS):
    """create a period beginning 30 days in the future, preceded consecutively by another NUM_PERIODS - 1 periods; each period has length four months"""
    # print("creating periods...")
    retval = []
    for _ in range(NUM_PERIODS):
        next_start = start + relativedelta(months=4)
        end = next_start - relativedelta(days=1)
        retval.append(
            Period.objects.create(classroom=classroom, start=start, end=end))
        start = next_start
    return retval


def create_kids(classroom, num_kids=NUM_KIDS_PER_CLASSROOM):
    return [Child.objects.create(
            nickname=f"Kid {random_str()}", classroom=classroom)
              for n in range(1, num_kids + 1)]

def create_caredayassignments(classroom):
    all_caredays = list(CareDay.objects.filter(start_time__hour=8,
                                               classroom=classroom))
    for c in classroom.child_set.all():
        num_days = random.randrange(2, 6)
        caredays_for_child = random.sample(list(all_caredays), num_days)
        for careday in caredays_for_child:
            CareDayAssignment.objects.create(child=c,
                                             careday=careday,
                                             start=PERIODS_START,
                                             end=CAREDAYASSIGNMENT_END)
            if random.randrange(2):
                extd_careday = CareDay.objects.get(
                    start_time__hour=15,
                    weekday=careday.weekday,
                    classroom=classroom)
                CareDayAssignment.objects.create(child=c,
                                                 careday=extd_careday,
                                                 start=PERIODS_START,
                                                 end=CAREDAYASSIGNMENT_END)

def create_shiftpreferences(period):
    children = period.classroom.child_set.all().distinct()
    for child in children:
        caredays = CareDay.objects.filter(caredayassignment__child=child).distinct()
        shifts = list(itertools.chain.from_iterable([
            careday.shifts() for careday in caredays]))
        shifts = random.sample(shifts, 2)
        for shift in shifts:
            ShiftPreference.objects.create(
                child=child, shift=shift, rank=1, period=period)

def create_shiftassignments(period):
    list(itertools.islice(WorktimeSchedule.generate_schedules(
        period), 10))


def create_worktimecommitments(period):
    schedule = next(WorktimeSchedule.generate_schedules(period))
    schedule.commit()



def setup_sample_classroom(name):
    classroom = create_classroom(name)
    create_shifts(classroom)
    create_caredays(classroom)
    periods = create_periods(classroom)
    kids = create_kids(classroom)
    create_caredayassignments(classroom)
    for period in periods:
        create_shiftpreferences(period)
    create_worktimecommitments(periods[0])
    return classroom
