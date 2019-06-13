# 7938

import datetime
import random

from django.test import TestCase
from people.models import *
from django.utils import timezone

from main.models import *
from main.model_fields import WEEKDAYS

from tests.main.test_utils import *


class _EventAlgebraTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.dates = [timezone.now() + datetime.timedelta(i)
                 for i in range(-4, 4)]
        cls.events = {index1 :
                        {index2 : cls.event_class.objects.create(
                            start=date1,
                            end=date2)
                         for index2, date2 in enumerate(cls.dates[index1:])}
                        for index1, date1 in enumerate(cls.dates)}

    def _test_spans(self):
        h = self.events[2][5]
        span = self.event_class.objects.spans(self.dates[3], self.dates[4])
        self.assertTrue(h in span)
        for i, start in enumerate(self.dates):
            for end in self.dates[i:]:
                span = self.event_class.objects.spans(start, end)
                # print("span: ", span)
                if start < h.start or end > h.end:
                    self.assertFalse(h in span)
                else:
                    self.assertTrue(h in span)

    def _test_overlaps(self):
        h = self.events[2][5]
        for i, start in enumerate(self.dates):
            for end in self.dates[i:]:
                overlap = self.event_class.objects.overlaps(start, end)
                # print("overlap: ", overlap)
                if h.start > end or h.end < start:
                    self.assertFalse(h in overlap)
                else:
                    self.assertTrue(h in overlap)


# class _EventByDateAndTimeTest(TestCase):

#     @classmethod
#     def setUpTestData(cls):
#         start = timezone.datetime(2019, 1, 1, 0, 0, 0)
#         end = timezone.datetime(2019, 2, 1, 0, 0, 0)
#         cls.datetimes = [random.uniform(start, end) for _ in range(50)]
#         cls.events = [cls.event_class.objects.create(
#             start=random.choice(cls.datetimes)) for _ in range(100)]
        
    # def _test_by_date_and_time(self):
    #     actual = self.event_class.objects.by_date_and_time(
    #         timezone.datetime(2019, 1, 5, 0, 0, 0),
    #         timezone.datetime(2019, 1, 10, 0, 0, 0))
    #     print(f"actual.items() : {actual.items()}")
    #     for event in self.events:
    #         for date, times in actual.items():
    #             print(date, times)
    #             for time, events in times.items():
    #                 print(time, events)
    #                 self.assertEqual(event.start.date() == date\
    #                            and event.start.time() == time,
    #                            event in events)


# class HolidayByDateAndTimeTest(_EventByDateAndTimeTest):
#     event_class = Holiday

#     def test_by_date_and_time(self):
#         return  self._test_by_date_and_time()


class HolidayAlgebraTest(_EventAlgebraTest):

    event_class = Holiday

    def test_spans(self):
        return self._test_spans()

    def test_overlaps(self):
        return self._test_overlaps()
    

class HolidayDatesForRangeTest(TestCase):

    def setUp(self):
        self.dates = [timezone.now() + datetime.timedelta(days = i)
                      for i in range(-50, 50)]
        starts = [random.choice(self.dates) for _ in range(20)]
        ends = [d + datetime.timedelta(days=random.randrange(7))
                             for d in starts]
        self.holidays = [Holiday.objects.create(start=start, end=end)
                         for start, end in zip(starts, ends)]
    
    def test_dates_for_range(self):
        start, end = self.dates[30], self.dates[70]
        found_holiday_dates = Holiday.objects._dates_for_range(start, end)
        for holiday in self.holidays:
            for date in holiday.all_dates():
                self.assertEqual(date in found_holiday_dates,
                                 start <= date <= end)
            

class HappeningAlgebraTest(_EventAlgebraTest):

    event_class = Happening

    def test_spans(self):
        return self._test_spans()

    def test_overlaps(self):
        return self._test_overlaps()


# class _WeeklyEventTest(TestCase):

#     @classmethod
#     def setUpTestData(cls):
#         NUM_TRIALS = 10
#         DATERANGE_LEN_MAX = 60
#         DATERANGE_START_RANGE = 365
#         start_times = (timezone.time(random.randrange(8, 16), 1, 1)
#                             for _ in range(NUM_TRIALS))
#         end_times = (start_time + datetime.timedelta(
#             hours=random.randrange(1,4))
#                           for start_time in start_times) 
#         weekdays = (random.choice(WEEKDAYS)
#                         for _ in start_times)
#         weekly_events = {wd : 
#             cls.weekly_event_class.objects.create(
#                 start_time = st,
#                 end_time = et,
#                 weekday = wd)
#             for st, et, wd in zip(start_times, end_times, weekdays)}
#         setattr(cls,
#                 cls.weekly_event_class.__name__.lower() + "_list",
#                 weekly_events)
#         cls.weekly_events = {wd : 
#             cls.weekly_event_class.objects.create(
#                 start_time = st,
#                 end_time = et,
#                 weekday = wd)
#             for st, et, wd in zip(start_times, end_times, weekdays)}
#         def random_daterange():
#             start = random.uniform(
#             timezone.now() - datetime.timedelta(
#                 days=DATERANGE_START_SPREAD),
#             timezone.now())
#             end = start + datetime.timedelta(
#                 days = random.randrange(1, DATERANGE_LEN_MAX))
#             return start, end
#         cls.date_ranges = [random_daterange() for _ in range(NUM_TRIALS)]

class ClassroomTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.classroom = Classroom.objects.create(name="some test classroom")


class CareDayOccurrencesForDateRangeTest(ClassroomTestCase):

    def _test_careday_for_date_range(self, careday, start, end):
            actual_occs = careday.occurrences_for_date_range(
                start, end,
                ignore_holidays=True)
            for date in dates_in_range(start, end):
                if str(date.weekday()) == str(careday.weekday):
                    careday.initialize_occurrence(date)
                    self.assertEqual(
                        next(actual_occs).start.date(),
                        date.date())
            self.assertRaises(StopIteration,
                lambda : next(actual_occs))
            occs_display = list(careday.occurrences_for_date_range(
                start, end,
                ignore_holidays=True))
            # print(f"verified that {careday} has {len(occs_display)} occurrences from {start} until {end}")


    def test_occurrences_for_date_range_oneoff(self):
        """pick careday and daterange, verify its occurrences_for_date_range
        """
        start = timezone.datetime(2019, 1, 1, 0, 0, 0)
        end = timezone.datetime(2019, 2, 1, 0, 0, 0)
        classroom = Classroom.objects.create(name="test classroom")
        careday = CareDay.objects.create(
            start_time = datetime.time(8, 0, 0),
            end_time = datetime.time(10, 0, 0),
            weekday = "0",
            classroom = classroom)
        self._test_careday_for_date_range(careday, start, end)


    def test_occurrences_for_date_range_random(self):
        NUM_TRIALS = 500
        DATERANGE_LEN_MAX = 100
        DATERANGE_START_RANGE = 500
        EVENT_LEN_MAX = 7
        START_TIME_RANGE = (8, 16)
        for _ in range(NUM_TRIALS):
            start_time = datetime.time(random.randrange(*START_TIME_RANGE), 0, 0)
            end_time = datetime.time(
                start_time.hour + random.randrange(1, EVENT_LEN_MAX), 0, 0)
            weekday = random.choice(list(WEEKDAYS.keys()))
            careday = CareDay.objects.create(start_time = start_time,
                                             end_time = end_time,
                                             weekday = weekday,
                                             classroom=self.classroom)
            date_range = random_daterange()
            self._test_careday_for_date_range(careday, *date_range)
            



