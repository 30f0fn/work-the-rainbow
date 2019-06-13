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


def create_kids(classroom):
    num_kids = random.randrange(*KIDS_PER_CLASSROOM_RANGE)
            for _ in range(num_kids):
                Child.objects.create(
                    nickname=f"kid {randy_str()}", classroom=classroom)


def create_shifts(classroom):
    for w in WEEKDAYS:
        if int(w) < 5:
            for st in SHIFT_TIMESPANS:
                Shift.objects.create(weekday=w,
                                     start_time = st[0],
                                     end_time=st[1],
                                     classroom=classroom)

def create_periods(classroom):
    """create a period beginning 30 days in the future, preceded consecutively by another NUM_PERIODS - 1 periods"""
    NUM_PERIODS = 4
    bounds = [datetime.timedelta(days=num_days) for num_days in
              [150 - 120 * (i - NUM_PERIODS) for i in range(NUM_PERIODS)]]
    bound_pairs = [{'start' : d1, 'end' : d2}
                      for d1, d2 in zip(bounds, bounds[1:])]
    Period.objects.create(classroom=classroom,
                          *bound_pairs)


def create_careday_assignments(period):
    classroom = period.classroom
    all_caredays = list(CareDay.objects.filter(start_time__hour=8,
                                               classroom=classroom))
    for c in classroom.child_set.all():
        num_days = random.randrange(2,6)
        days = random.sample(list(range(5)), num_days)
        caredays_for_child = random.sample(list(all_caredays), num_days)
        # ext_caredays = CareDay.objects.filter(start_time.hour=15)
    for careday in caredays_for_child:
        CareDayAssignment.objects.create(child=c,
                                         careday=careday,
                                         start=period.start,
                                         end=period.end)
        if random.randrange(2):
            ext_careday = CareDay.objects.get(
                start_time__hour=15,
                weekday=careday.weekday)
            CareDayAssignment.objects.create(child=c,
                                             careday=ext_careday,
                                             start=period.start,
                                             end=period.end)


class DayCareTestCase(TestCase):
    NUM_CLASSROOMS = 100
    KIDS_PER_CLASSROOM_RANGE = (5, 12)
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
                if period.start <= timezone.now():
                    create_careday_assignments(period)
