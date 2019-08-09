import random
import datetime

from django.test import TestCase
from people.models import *
from django.utils import timezone
from django.db import models

from main.models import *
from main.model_fields import WEEKDAYS

from tests.main.test_utils import *


SHIFT_TIMESPANS = [('8:30', '10:30'), ('13:30', '15:30'), ('15:30', '17:30')]

NUM_CLASSROOMS = 1
KIDS_PER_CLASSROOM_RANGE = (5, 12)
NUM_PERIODS = 4
NUM_HOLIDAYS = 5
HOLIDAY_LENGTH_RANGE = 7

def create_holidays_for_period(period):
    for _ in range(NUM_HOLIDAYS):
        start = random.uniform(period.start, period.end)
        delta = datetime.timedelta(random.randint(1, HOLIDAY_LENGTH_RANGE))
        holiday = Holiday.objects.create(
            start=start,
            end=start+delta)
        # print(f"holiday {holiday.start} - {holiday.end}")


def create_classrooms(num=NUM_CLASSROOMS):
    return [Classroom.objects.create(name=f"classroom {random_str()}")
                             for i in range(num)]

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


def create_kids(classroom, num=None, num_range=KIDS_PER_CLASSROOM_RANGE):
    num_kids = num if num is not None else random.randrange(*KIDS_PER_CLASSROOM_RANGE)
    return [Child.objects.create(
            nickname=f"kid {random_str()}", classroom=classroom)
              for _ in range(num_kids)]


def create_shifts(classroom):
    for w in WEEKDAYS:
        if int(w) < 5:
            for st in SHIFT_TIMESPANS:
                Shift.objects.create(weekday=w,
                                     start_time = st[0],
                                     end_time=st[1],
                                     classroom=classroom)



def create_periods(classroom, num=NUM_PERIODS):
    """create a period beginning 30 days in the future, preceded consecutively by another NUM_PERIODS - 1 periods; each period has length 120 days"""
    # print("creating periods...")
    retval = []
    start = timezone.make_aware(timezone.datetime(2000, 9, 1))
    for _ in range(NUM_PERIODS):
        next_month = (start.month + 4) % 12
        next_year = start.year + 1 if next_month < start.month else start.year
        next_start = start.replace(year=next_year, month=next_month)
        end = next_start - datetime.timedelta(days=1)
        retval.append(
            Period.objects.create(classroom=classroom, start=start, end=end))
        start = next_start
    return retval


def create_careday_assignments(period):
    classroom = period.classroom
    all_caredays = list(CareDay.objects.filter(start_time__hour=8,
                                               classroom=classroom))
    for c in classroom.child_set.all():
        num_days = random.randrange(2,6)
        caredays_for_child = random.sample(list(all_caredays), num_days)
        # ext_caredays = CareDay.objects.filter(start_time.hour=15)
        # print(f"period.start = {period.start}")
        for careday in caredays_for_child:
            CareDayAssignment.objects.create(child=c,
                                             careday=careday,
                                             start=period.start,
                                             end=period.end)
            if random.randrange(2):
                extd_careday = CareDay.objects.get(
                    start_time__hour=15,
                    weekday=careday.weekday)
                CareDayAssignment.objects.create(child=c,
                                                 careday=extd_careday,
                                                 start=period.start,
                                                 end=period.end)


def create_shiftpreferences(period):
        for child in period.classroom.child_set.all():
            caredays = CareDay.objects.filter(caredayassignment__child=child)
            shifts = list(itertools.chain.from_iterable([
                careday.shifts() for careday in caredays]))
            shifts = random.sample(shifts, 2)
            for shift in shifts:
                ShiftPreference.objects.create(child=child, shift=shift, rank=1, period=period)

def create_shiftassignments(period):
    ShiftAssignmentCollection.objects.generate(period)

def create_worktimecommitments(period):
    shacoll = ShiftAssignmentCollection.objects.filter(period=period).first()
    shacoll.create_commitments()



class DayCareTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.classrooms = create_classrooms()
        for classroom in cls.classrooms:
            create_kids(classroom)
            create_caredays(classroom)
            create_shifts(classroom)
            create_periods(classroom)
            for period in classroom.period_set.all():
                # print(f"period start is {period.start}")
                if period.start <= timezone.now():
                    create_careday_assignments(period)
                create_holidays_for_period(period)



    # @classmethod
    # def create_random_commitments(cls, NUM=8):
    #     """randomly assign NUM commitments per period per child, with no two children commited to same shift in classroom, and each child's committed shifts covered by their caredayassignments"""
    #     print("creating random commitments")
    #     for classroom in cls.classrooms:
    #         for period in Period.objects.filter(classroom=classroom):
    #             classroom = period.classroom
    #             for child in classroom.child_set.all():
    #                 cdos = CareDayAssignment.objects.occurrences_for_child(
    #                     child, start=period.start, end=period.end)
    #                 occupied_shoccs = {wtc.shift_occurrence()
    #                                    for wtc in WorktimeCommitment.objects.filter(
    #                                            child__classroom=child.classroom)}
    #                 shoccs = [shocc for cdo in cdos for shocc in cdo.shift_occurrences()
    #                           if shocc not in occupied_shoccs]
    #                 commitments = [shocc.create_commitment(child)
    #                                for shocc in random.sample(shoccs, NUM)]
    #     print("done creating random commitments")


class CareDayAssignmentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.classrooms = [Classroom.objects.create(name=f"classroom {random_str()}")
                          for i in range(NUM_CLASSROOMS)]
        for classroom in cls.classrooms:
            create_kids(classroom)
            create_caredays(classroom)
            create_shifts(classroom)
            create_periods(classroom)
            for period in classroom.period_set.all():
                create_holidays_for_period(period)
