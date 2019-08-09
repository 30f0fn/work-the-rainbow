import datetime
import random
import collections

from django.test import TestCase
from people.models import *
from django.utils import timezone

from main.models import *
from main.model_fields import WEEKDAYS

from tests.main.test_utils import *
from tests.main.daycare_testcase import *

class _EventAlgebraTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # INTERVAL = (0, 1)
        INTERVAL = (-4, 4)
        """within interval -4, 4, build event with start,end == i, j for all i, j in interval with i < j"""
        cls.dates = [timezone.now() + datetime.timedelta(days=i)
                 for i in range(*INTERVAL)]
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


class _EventByDateAndTimeTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        start = timezone.make_aware(timezone.datetime(2019, 1, 1, 0, 0, 0))
        end = timezone.make_aware(timezone.datetime(2019, 2, 1, 0, 0, 0))
        cls.datetimes = [random.uniform(start, end) for _ in range(50)]
        cls.events = [cls.event_class.objects.create(
            start=random.choice(cls.datetimes)) for _ in range(100)]
        
    def _test_by_date_and_time(self):
        actual = self.event_class.objects.by_date_and_time(
            timezone.make_aware(timezone.datetime(2019, 1, 5, 0, 0, 0)),
            timezone.make_aware(timezone.datetime(2019, 1, 10, 0, 0, 0)))
        for event in self.events:
            for date, times in actual.items():
                for time, events in times.items():
                    self.assertEqual(event.start.date() == date\
                               and event.start.time() == time,
                               event in events)


class HolidayByDateAndTimeTest(_EventByDateAndTimeTest):
    event_class = Holiday

    def test_by_date_and_time(self):
        return  self._test_by_date_and_time()


class HolidayAlgebraTest(_EventAlgebraTest):

    event_class = Holiday

    def test_overlaps(self):
        return self._test_overlaps()

    def test_spans(self):
        return self._test_spans()

    

class HolidayDatesForRangeTest(TestCase):

    def setUp(self):
        NUM_HOLIDAYS = 1
        self.dates = [timezone.now() + datetime.timedelta(days = i)
                      for i in range(-50, 50)]
        starts = [random.choice(self.dates) for _ in range(NUM_HOLIDAYS)]
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
                                 start.date() <= date <= end.date())
                    

class HappeningAlgebraTest(_EventAlgebraTest):

    event_class = Happening

    def test_spans(self):
        return self._test_spans()

    def test_overlaps(self):
        return self._test_overlaps()


class ClassroomTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.classroom = Classroom.objects.create(name="some test classroom")


class CareDayInstanceOccurrencesForDateRangeTest(ClassroomTestCase):

    def _test_careday_for_date_range(self, careday, start, end,
                                     ignore_holidays=False):
        # Holiday.objects.create(start=start,
                               # end=start+datetime.timedelta(days=15))
        actual_occs = careday.occurrences_for_date_range(
            start, end,
            ignore_holidays=ignore_holidays
        )
        # occs_display = list(careday.occurrences_for_date_range(
            # start, end))
        # print(occs_display)
        exclusions = Holiday.objects._dates_for_range(start, end)
        # print(f"exclusions found in test: {exclusions}")
        for date in dates_in_range(start, end):
            if str(date.weekday()) == str(careday.weekday) and date not in exclusions:
                careday.initialize_occurrence(date)
                self.assertEqual(date,
                                 next(actual_occs).start.date())
        self.assertRaises(StopIteration,
                          lambda : next(actual_occs))
        occs_display = list(careday.occurrences_for_date_range(
            start, end,
            # ignore_holidays=True
        ))
        # print(f"verified that {careday} has {len(occs_display)} occurrences from {start} until {end}")


    def test_occurrences_for_date_range_oneoff(self):
        """pick careday and daterange, verify its occurrences_for_date_range
        """
        start = timezone.make_aware(timezone.datetime(2019, 1, 1, 0, 0, 0))
        end = timezone.make_aware(timezone.datetime(2019, 2, 1, 0, 0, 0))
        classroom = Classroom.objects.create(name="test classroom")
        careday = CareDay.objects.create(
            start_time = datetime.time(8, 0, 0),
            end_time = datetime.time(10, 0, 0),
            weekday = "0",
            classroom = classroom)
        self._test_careday_for_date_range(careday, start, end, ignore_holidays=True)

    def test_occurrences_for_date_range_oneoff_with_holidays(self):
        """pick careday and daterange, verify its occurrences_for_date_range
        """
        start = timezone.datetime(2019, 1, 1, 0, 0, 0)
        end = timezone.datetime(2019, 2, 1, 0, 0, 0)
        # print("before make_aware", start)
        start = timezone.make_aware(start)
        # print("after make_aware", start)
        end = timezone.make_aware(end)
        classroom = Classroom.objects.create(name="test classroom")
        Holiday.objects.create(start=start,
                               end=start + datetime.timedelta(days=15))
        careday = CareDay.objects.create(
            start_time = datetime.time(8, 0, 0),
            end_time = datetime.time(10, 0, 0),
            weekday = "0",
            classroom = classroom)
        self._test_careday_for_date_range(careday, start, end)

    def test_occurrences_for_date_range_random(self):
        NUM_TRIALS = 100
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
            self._test_careday_for_date_range(careday, *date_range, ignore_holidays=True)

    def test_occurrences_for_date_range_random_with_holidays(self):
        NUM_TRIALS = 100
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
                                             classroom = self.classroom)
            date_range = random_daterange()
            holiday_start = random.uniform(*date_range)
            holiday_duration = datetime.timedelta(days=random.randrange(7))
            Holiday.objects.create(start=holiday_start,
                                   end=holiday_start + holiday_duration)
            self._test_careday_for_date_range(careday, *date_range)


class CareDayQuerySetTest(DayCareTestCase):

    def test__by_weekday(self):
        careday_qs = CareDay.objects.all()
        actual_by_weekday = careday_qs.by_weekday()
        for careday in careday_qs:
            self.assertTrue(careday in actual_by_weekday[int(careday.weekday)])
        for weekday in WEEKDAYS:
            actual = len(actual_by_weekday[int(weekday)])
            expected = CareDay.objects.filter(weekday=weekday).count()
            self.assertEqual(actual, expected)

    def _test_for_date_range(self, careday_qs, start, end,
                                        ignore_holidays=False):
        found_occs = careday_qs.occurrences_for_date_range(
            start, end,
            ignore_holidays=ignore_holidays)
        caredays = careday_qs.by_weekday()
        # print(caredays)
        exclusions = ([] if ignore_holidays\
            else Holiday.objects._dates_for_range(start, end))
        for date in dates_in_range(start, end):
            for careday in caredays[date.weekday()]:
                # print(Holiday.objects.filter(start__lte=date, end__gte=date))
                if date not in exclusions:
                    found_occ = next(found_occs)
                    expected_occ = careday.initialize_occurrence(date)
                    self.assertEqual(
                        found_occ.start.date(),
                        expected_occ.start.date())
        # print(list(found_occs))
        # self.assertEqual(len(found_occs), 0)
        self.assertRaises(StopIteration,
                          lambda : next(found_occs))
    
    def test_singleton_occs_for_date_range(self):
        careday_qs = CareDay.objects.filter(weekday="0", start_time="8:30")
        # daterange = random_daterange(earliest=timezone.now(),
                              # latest=timezone.now() + datetime.timedelta(days=300))
        daterange = (timezone.now(), timezone.now() + datetime.timedelta(days=30))
        self._test_for_date_range(
            careday_qs,
            *daterange,
            ignore_holidays=True)
            # timezone.now() - datetime.timedelta(days=30),
            # timezone.now())

    def test_occs_for_date_range(self): 
        careday_qs = CareDay.objects.filter(
            classroom=Classroom.objects.first())
        date_range = (timezone.now() - datetime.timedelta(days=30),
                      timezone.now())
        self._test_for_date_range(
            careday_qs,
            *date_range,
            ignore_holidays=True)

    def test_singleton_qs_occs_for_date_range_excluding_holidays(self):
        careday_qs = CareDay.objects.filter(weekday="0", start_time="8:30")
        daterange = (timezone.now(), timezone.now() + datetime.timedelta(days=30))
        self._test_for_date_range(
            careday_qs,
            *daterange,
            ignore_holidays=False)
            # timezone.now() - datetime.timedelta(days=30),
            # timezone.now())

    def test_occs_for_date_range_excluding_holidays(self): 
        careday_qs = CareDay.objects.filter(
            classroom=Classroom.objects.first())
        date_range = (timezone.now() - datetime.timedelta(days=30),
                      timezone.now())
        self._test_for_date_range(
            careday_qs,
            *date_range,
            ignore_holidays=False)
        
    def _test_occs_by_date(self, careday_qs, start, end,
                           ignore_holidays=False):
        found_occs = careday_qs.occurrences_by_date(
            start, end,
            ignore_holidays=ignore_holidays)
        caredays_by_date = careday_qs.occurrences_by_date(start, end,
                                              ignore_holidays=ignore_holidays)
        # print(caredays)
        exclusions = ([] if ignore_holidays\
            else Holiday.objects._dates_for_range(start, end))
        for date in dates_in_range(start, end):
            if date not in exclusions:
                expected_occ_starts = {careday.initialize_occurrence(date).start
                                 for careday in careday_qs.by_weekday()[date.weekday()]}
                actual_occ_starts = {cdo.start for cdo in caredays_by_date[date]}
                # print(f"expected_occ_starts={expected_occ_starts},\
                # actual_occ_starts={actual_occ_starts}")
                self.assertEqual(
                    expected_occ_starts,
                    actual_occ_starts)

    def test_occs_by_date(self):
        careday_qs = CareDay.objects.filter(
            classroom=Classroom.objects.first())
        date_range = (timezone.now() - datetime.timedelta(days=30),
                      timezone.now())
        self._test_occs_by_date(
            careday_qs,
            *date_range,
            ignore_holidays=False)

    def _test_occs_by_date_and_time(self, careday_qs, start, end,
                                    ignore_holidays=False):
        found_occs = careday_qs.occurrences_by_date_and_time(
            start, end,
            ignore_holidays=ignore_holidays)
        # caredays_by_weekday_time = careday_qs.occurrences_by_date_and_time(start, end,
                                              # ignore_holidays=ignore_holidays)
        # print(caredays)
        exclusions = ([] if ignore_holidays\
            else Holiday.objects._dates_for_range(start, end))
        for date in dates_in_range(start, end):
            if date not in exclusions:
                # print(f"by weekday of {date}...",
                      # careday_qs.by_weekday()[date.weekday()])
                expected_occ_times = sorted(list({
                    careday.initialize_occurrence(date).start.time()\
                    for careday in
                    careday_qs.by_weekday()[date.weekday()]
                }))
                actual_occ_times = list(found_occs[date].keys())
                self.assertEqual(expected_occ_times, actual_occ_times)

    def test_occs_by_date_and_time(self):
        careday_qs = CareDay.objects.filter(
            classroom=Classroom.objects.first())
        date_range = (timezone.now() - datetime.timedelta(days=30),
                      timezone.now())
        self._test_occs_by_date_and_time(
            careday_qs,
            *date_range)


        
class CareDayTest(DayCareTestCase):
    
    def test_shifts(self):
        classroom = Classroom.objects.first()
        careday = CareDay.objects.get(weekday=0,
                                      start_time__hour=8,
                                      classroom=classroom)
        # print(careday.shifts())
        actual = careday.shifts()
        expected = Shift.objects.filter(weekday=careday.weekday,
                                        start_time__gte=careday.start_time,
                                        end_time__lte=careday.end_time,
                                        classroom=careday.classroom)

class CareDayOccurrenceTest(DayCareTestCase):

    def test_children(self):
        careday = CareDay.objects.first()
        date = next_date_with_given_weekday(careday.weekday, timezone.now())
        cdo = careday.initialize_occurrence(date)
        cda_list = CareDayAssignment.objects.filter(
            child__classroom=careday.classroom,
            start__lte=date, end__gte=date,
            careday=careday
        )
        actual_children = cdo.children()
        for cda in cda_list:
            self.assertTrue(cda.child in actual_children)

    def test_shift_occurrences(self):
        careday = CareDay.objects.first()
        date = next_date_with_given_weekday(careday.weekday, timezone.now()).date()
        cdo = careday.initialize_occurrence(date)
        sh_occ_shifts = [sh_occ.shift for sh_occ in cdo.shift_occurrences()]
        expected_sh_occ_shifts = list(Shift.objects.filter(
            weekday=careday.weekday,
            start_time__hour__in=[8, 13],
            classroom=careday.classroom))
        self.assertEqual(sh_occ_shifts, expected_sh_occ_shifts)
        sh_occ_dates = [sh_occ.start.date() for sh_occ in cdo.shift_occurrences()]
        expected_sh_occ_dates = [date for _ in expected_sh_occ_shifts]
        self.assertEqual(sh_occ_dates, expected_sh_occ_dates)


class CareDayAssignmentMaintenanceTest(CareDayAssignmentTestCase):
    """ make sure caredayassignments are maintained nicely, so that no two overlap for same careday
        create/edit sequentially some caredayassignments for a given child.
        at each step, memoize resulting "correct" set AssignedOccurrences of assigned caredayoccurrences
        then, verify (i) no two assignments have common caredayoccurrence, and 
        (ii) that an occurrence is covered by a caredayassignment iff it is belongs to AssignedOccurrences
        """
    
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.classroom = Classroom.objects.first()
        cls.child = random.choice(list(Child.objects.filter(classroom=cls.classroom)))
        cls.caredays = CareDay.objects.filter(classroom=cls.classroom)
        cls.start = timezone.make_aware(timezone.datetime(2018,9,1,0,0,0))
        cls.end = cls.start + datetime.timedelta(days=365)

    def memoize_creation(self, cda, memo):
        for occ in cda.occurrences_for_date_range(self.start, self.end):
            memo.add(occ)
            # print(f"added occ {occ}")

    def memoize_deletion(self, cda, memo):
        for occ in cda.occurrences_for_date_range(self.start, self.end):
            memo.discard(occ)
            # print(f"removed occ {occ}")

    def _create_and_memoize(self, memo):
        start, end = random_daterange(earliest = self.start,
                                      latest = self.end,
                                      max_delta_days = 365)
        cda = CareDayAssignment(start=start,
                                end=end,
                                child=self.child,
                                careday=random.choice(self.caredays))
        cda.save()
        self.memoize_creation(cda, memo)

    def _delete_and_memoize(self, memo):
        assignments = list(CareDayAssignment.objects.filter(child=self.child))
        if not assignments:
            return
        cda = random.choice(assignments)
        cda.delete()
        self.memoize_deletion(cda, memo)

    def _revise_and_memoize(self, memo):
        assignments = list(CareDayAssignment.objects.filter(child=self.child))
        if not assignments:
            return
        max_delta_days=60
        cda = random.choice(assignments)
        attr = random.choice(['start', 'end'])
        delta = datetime.timedelta(days = random.randrange(-max_delta_days,
                                                           max_delta_days))
        newVal = getattr(cda, attr) + delta
        new_start = {attr : newVal}.get('start') or cda.start
        new_end = {attr : newVal}.get('end') or cda.end
        cda.delete()
        self.memoize_deletion(cda, memo)
        cda = CareDayAssignment(start=new_start,
                                end=new_end,
                                child=self.child,
                                careday=cda.careday)
        cda.save()
        self.memoize_creation(cda, memo)


    def _verify(self, memo):
        actual = set(CareDayAssignment.objects.occurrences_for_child(
            self.child, start=self.start, end=self.end))
        expected = memo
        # print(f"size of actual = {len(actual)};\nactual = {actual}\n")
        # print(f"size of expected = {len(expected)};\nexpected = {expected}")
        self.assertEqual(actual, expected)
        for occ in actual:
            assignments = CareDayAssignment.objects.filter(
                careday=occ.careday,
                start__date__lte=occ.start, end__date__gte=occ.end)
            try:
                self.assertEqual(1, assignments.count())
            except AssertionError:
                print(assignments)
                self.assertEqual(1, assignments.count())

        # print(CareDayAssignment.objects.filter(careday__classroom = self.classroom))

    def test_create(self):
        """
        create a bunch of caredayassignments, recording what caredayoccurrences should be given for child
        then verify that these are the occurrences generated by assignments created for child, and that each occurrence is generated by only one assignment
        """
        memo = set()
        num_creations = 30
        for _ in range(num_creations):
                self._create_and_memoize(memo)
        self._verify(memo)

    def test_revise(self):
        
        memo = set()
        num_creations = 30
        num_random_actions = 100
        for _ in range(num_creations):
                self._create_and_memoize(memo)
        for _ in range(num_random_actions):
            action = random.choice(('_create_and_memoize',
                                    '_revise_and_memoize',
                                    '_delete_and_memoize'))
            getattr(self, action)(memo)
        self._verify(memo)

    
class _WorktimeCommitmentTestCase(DayCareTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for classroom in cls.classrooms:
            for period in Period.objects.filter(classroom=classroom):
                create_shiftpreferences(period)
                create_shiftassignments(period)
                create_worktimecommitments(period)
        # # cls.create_random_commitments()
        # cls.period = Period.objects.first()
        # cls.child = Child.objects.first()
        # cls.cdos = CareDayAssignment.objects.occurrences_for_child(
        #     cls.child, cls.period.start, cls.period.end)
        # cls.wtcs = [shocc.create_commitment(cls.child)
        #              for cdo in cls.cdos
        #              for shocc in cdo.shift_occurrences()]
        # print(f"num commitments created: {len(cls.wtcs)}")

class ShiftQuerySetTest(_WorktimeCommitmentTestCase):
    """
    methods to test
    - occurrences_by_date_and_time with include_commitments=True
    """
    def test_occs_with_commitments(self):
        for classroom in self.classrooms:
            for period in Period.objects.filter(classroom=classroom):
                expected_commitments = set(WorktimeCommitment.objects.filter(
                    child__classroom=classroom,
                    start__gte=period.start,
                    end__lte=period.end))
                # print(f"num commitments expected: {len(expected_commitments)}")
                shocc_qs = Shift.objects.filter(
                    classroom=classroom).occurrences_by_date_and_time(
                        start=period.start, end=period.end,
                        include_commitments=True,
                        # ignore_holidays=True
)
                commitments_from_shoccs = {shocc.commitment
                                           for times in shocc_qs.values()
                                           for shocc in times.values()
                                           if shocc.commitment}
                self.assertEqual(commitments_from_shoccs, expected_commitments)

class ShiftOccurrenceCommitmentMethodsTest(TestCase):
    """
    methods to test
    - create_commitment, get_commitment
    """
    @classmethod
    def setUpTestData(cls):
        cls.classroom = create_classrooms(num=1)[0]
        # create_caredays(cls.classroom)
        create_shifts(cls.classroom)
        cls.period = create_periods(cls.classroom, num=1)[0]
        cls.kid1 = Child.objects.create(classroom=cls.classroom, nickname='kid1')
        # cls.kid2 = Child.objects.create(classroom=cls.classroom, nickname='kid2')
        # careday1 = CareDay.objects.get(classroom=cls.classroom,
                                       # weekday='1', start_time__hour=8)
        # careday2 = CareDay.objects.get(classroom=cls.classroom,
                                       # weekday='2', start_time__hour=8)
        # CareDayAssignment.objects.create(
            # child=cls.kid1,
            # careday = careday1,
            # start=cls.period.start, end=cls.period.end)
        # CareDayAssignment.objects.create(
            # child=cls.kid1,
            # careday = careday2,
            # start=cls.period.start, end=cls.period.end)

    def testCreateAndGetCommitment(self):
        shift = Shift.objects.get(classroom=self.classroom,
                                  weekday='1',start_time__hour=8)
        shocc = next(shift.occurrences_for_date_range(self.period.start, self.period.end))
        created_wtc = shocc.create_commitment(self.kid1)
        gotten_wtc = shocc.get_commitment()
        self.assertEqual(created_wtc, gotten_wtc)

class ShiftOccurrenceSerializationTest(TestCase):
    """
    methods to test 
    - serialize, deserialize
    """
    @classmethod
    def setUpTestData(cls):
        cls.classroom = create_classrooms(num=1)[0]
        create_shifts(cls.classroom)
        create_kids(Classroom.objects.get(),
                    num=1)
        cls.kid = Child.objects.first()
        cls.shift = Shift.objects.get(classroom=cls.classroom,
                                       weekday='1',start_time__hour=8)
        cls.start = timezone.now() - datetime.timedelta(days=30)
        cls.end = timezone.now()


        
    def test_serialize_and_deserialize(self):
        shoccs = self.shift.occurrences_for_date_range(self.start, self.end)
        for shocc in shoccs:
            self.assertEqual(shocc, ShiftOccurrence.deserialize(shocc.serialize()))

    def test_serialize_and_deserialize_with_commitment(self):
        shoccs = self.shift.occurrences_for_date_range(self.start, self.end)
        for shocc in shoccs:
            wtc = shocc.create_commitment(self.kid)
            self.assertEqual(wtc,
                             ShiftOccurrence.deserialize(
                                 shocc.serialize(),
                                 include_commitment=True).commitment)


class WorktimeCommitmentTest(TestCase):

    """methods to test:
    alternatives - enumerates all shiftoccurrences for classroom of child of commitment, minus those already committed, plus shiftoccurrence of current commitment, whose careday is in the caredayassignment of the child
    """

    @classmethod
    def setUpTestData(cls):
        cls.classroom = create_classrooms(num=1)[0]
        create_shifts(cls.classroom)
        create_caredays(cls.classroom)
        create_kids(Classroom.objects.get(),
                    num=10)
        cls.kid = Child.objects.first()
        cls.other_kids = Child.objects.filter(pk__gt=cls.kid.pk)
        cls.shift = Shift.objects.get(classroom=cls.classroom,
                                       weekday='1',start_time__hour=8)


    def test_wtc_alternatives(self):
        """add caredayassignments for kid, 
        verify that alternatives are just the shiftoccurrences within their ranges, 
        then add worktimecommitment to one shiftoccurrence for other kid, 
        and verify that this shiftoccurrence is removed from alternatives"""
        self.kid_caredays = CareDay.objects.filter(classroom=self.classroom,
                                                    weekday__in=['0', '1', '2'],
                                                    start_time__hour=8)
        for careday in self.kid_caredays:
            CareDayAssignment.objects.create(
                child=self.kid,
                careday=careday,
                start=timezone.make_aware(timezone.datetime(2024, 2, 1)),
                end=timezone.make_aware(timezone.datetime(2024, 4, 30)))
        kid_shift = Shift.objects.get(start_time__hour=8,
                                      classroom=self.kid.classroom,
                                      weekday='0')
        kid_shocc_date = timezone.make_aware(timezone.datetime(2024, 3, 4))
        while kid_shocc_date <= timezone.make_aware(timezone.datetime(2024, 4, 30)):
            shocc = kid_shift.initialize_occurrence(kid_shocc_date)
            wtc = shocc.create_commitment(self.kid)
            kid_shocc_date += datetime.timedelta(days=14)
            # should be 3/4, 3/18, 4/1, 4/15,, 4/29

        kid_shifts = Shift.objects.filter(
            classroom=self.kid.classroom,
            weekday__in=['0', '1', '2'],
            start_time__hour__in=[8, 13])
        month_day_pairs = [(2,26), (2,27), (2,28), (3,4), (3,5), (3,6), (3,11)]
        expected_alt_dates = [timezone.make_aware(timezone.datetime(2024, *md))
                              for md in month_day_pairs]
        expected_alt_shoccs = set(shift.initialize_occurrence(date)
                               for shift in kid_shifts
                               for date in expected_alt_dates
                               if int(shift.weekday) == date.weekday())
        wtc = WorktimeCommitment.objects.get(
            start = timezone.make_aware(timezone.datetime(2024, 3, 4, 8, 30)),
            child = self.kid)
        delta_week = datetime.timedelta(days=7)
        actual_alt_shoccs = set(wtc.alternatives(earlier=delta_week, later=delta_week))
        self.assertEqual(expected_alt_shoccs, actual_alt_shoccs)

        other_kid = self.other_kids.first()
        other_shocc = kid_shift.initialize_occurrence(
            timezone.make_aware(timezone.datetime(2024, 3, 11)))
        other_wtc = other_shocc.create_commitment(other_kid)
        expected_alt_shoccs.remove(other_shocc)
        actual_alt_shoccs = set(wtc.alternatives(earlier=delta_week, later=delta_week))
        # print(actual_alt_shoccs)
        self.assertEqual(expected_alt_shoccs, actual_alt_shoccs)


class ShiftTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.classroom = create_classrooms(num=1)[0]
        create_shifts(cls.classroom)
        create_caredays(cls.classroom)
        cls.kids = create_kids(classroom=cls.classroom, num=5)
        cls.periods = create_periods(cls.classroom, num=2)
        cls.shifts = {(weekday, hour) :
                      Shift.objects.get(
                          weekday=weekday,
                          start_time__hour=int(hour),
                          classroom=cls.classroom)
                      for hour in (8, 13, 15)
                      for weekday in (0, 1, 2, 3, 4)}


class ShiftPreferenceTestCase(ShiftTestCase):
    @classmethod
    def setUpTestData(cls):    
        super().setUpTestData()

        def build_pref(cls, kid_index, weekday, hour, rank, period_index):
            ShiftPreference.objects.create(
                child=cls.kids[kid_index], shift=cls.shifts[weekday, hour], 
                rank=rank, period=cls.periods[period_index])
            
        PrefDatum = collections.namedtuple('PrefDatum',
                                           ['kid_index', 'weekday', 'hour', 'rank', 'period_index'])
        cls.pref_data = [PrefDatum(0, 0, 8, 1, 0),
                         PrefDatum(0, 1, 8, 1, 0),
                         PrefDatum(0, 2, 13, 2, 0),
                         PrefDatum(0, 3, 13, 3, 0),
                         \
                         PrefDatum(0, 0, 13, 1, 1),
                         PrefDatum(0, 1, 13, 2, 1),
                         \
                         PrefDatum(1, 0, 8, 1, 1),
                         PrefDatum(1, 1, 13, 2, 1),
                         \
                         PrefDatum(1, 0, 13, 1, 0),
                         PrefDatum(1, 1, 13, 1, 0),
                         PrefDatum(1, 2, 13, 2, 0)]

        for datum in cls.pref_data:
            build_pref(cls, **datum._asdict())

        # cls.shift08 = cls.shifts[0,8]
        # cls.shift013 = cls.shifts[0,13]
        # cls.shift113 = cls.shifts[1,13]
        # cls.pref008 = ShiftPreference.objects.get(child=cls.kids[0].pk,
                                                  # shift=cls.shift08)
        # cls.pref0013 = ShiftPreference.objects.get(child=cls.kids[0].pk,
                                                   # shift=cls.shift013)
        # cls.pref1113 = ShiftPreference.objects.get(child=self.kids[1].pk, shift=shift113)


class ShiftPreferenceManagerTest(ShiftPreferenceTestCase):

    def test_by_time_and_weekday(self):
        act_dict = ShiftPreference.objects.by_time_and_weekday(self.periods[0])
        shift08 = self.shifts[0,8]
        shift013 = self.shifts[0,13]
        actual08 = set(act_dict[shift08.start_time][shift08.weekday])
        expected08 = set(ShiftPreference.objects.filter(
            shift=shift08,
            period=self.periods[0]))
        self.assertEqual(actual08, expected08)
        actual013 = set(act_dict[shift013.start_time][shift013.weekday])
        expected013 = set(ShiftPreference.objects.filter(
            shift=shift013,
            period=self.periods[0]))
        self.assertEqual(actual013, expected013)
        self.assertNotEqual(actual08, actual013)


    def test_by_shift(self):
        shift08 = self.shifts[0,8]
        actual08 = set(ShiftPreference.objects.by_shift(self.periods[0])[shift08])
        expected08 = set(ShiftPreference.objects.filter(shift=shift08,
                                                        period=self.periods[0]))
        self.assertEqual(actual08, expected08)
        shift013 = self.shifts[0,13]
        actual013 = set(ShiftPreference.objects.by_shift(self.periods[1])[shift013])
        expected013 = set(ShiftPreference.objects.filter(shift=shift013,
                                                      period=self.periods[1]))
        self.assertEqual(actual013, expected013)
        self.assertNotEqual(actual08, actual013)
        

class ShiftPreferenceTest(ShiftPreferenceTestCase):

    def test_generate_assignables(self):
        pref008 = ShiftPreference.objects.get(child=self.kids[0],
                                              shift=self.shifts[0, 8],
                                              period=self.periods[0])
        actual008 = set(pref008.generate_assignables())
        expected008 = set(ShiftAssignable.objects.create(preference=pref008,
                                                        offset=i, offset_modulus=2)
                      for i in range(2))
        self.assertEqual(actual008, expected008)
        pref1013 = ShiftPreference.objects.get(child=self.kids[1],
                                               shift=self.shifts[0, 13],
                                               period=self.periods[0])
        actual1013 = set(pref1013.generate_assignables())
        expected1013 = set(ShiftAssignable(preference=pref1013,
                                           offset=i, offset_modulus=2)
                      for i in range(2))
        self.assertEqual(actual1013, expected1013)
        self.assertNotEqual(actual008, actual1013)


class ShiftAssignableManagerTest(ShiftPreferenceTestCase):
    def test_generate(self):
        period = self.periods[1]
        actual_assignables = set(ShiftAssignable.objects.generate(period=period))
        prefs = (ShiftPreference.objects.get(child=self.kids[0],
                                             shift=self.shifts[0, 13],
                                             period=self.periods[1]),
                 ShiftPreference.objects.get(child=self.kids[0],
                                             shift=self.shifts[1, 13],
                                             period=self.periods[1]),
                 ShiftPreference.objects.get(child=self.kids[1],
                                             shift=self.shifts[0, 8],
                                             period=self.periods[1]),
                 ShiftPreference.objects.get(child=self.kids[1],
                                             shift=self.shifts[1, 13],
                                             period=self.periods[1]))
        expected_assignable_data = [
            {"preference" : prefs[0], "offset" : 0, "offset_modulus" : 2},
            {"preference" : prefs[0], "offset" : 1, "offset_modulus" : 2},
            {"preference" : prefs[1], "offset" : 0, "offset_modulus" : 2},
            {"preference" : prefs[1], "offset" : 1, "offset_modulus" : 2},
            {"preference" : prefs[2], "offset" : 0, "offset_modulus" : 2},
            {"preference" : prefs[2], "offset" : 1, "offset_modulus" : 2},
            {"preference" : prefs[3], "offset" : 0, "offset_modulus" : 2},
            {"preference" : prefs[3], "offset" : 1, "offset_modulus" : 2}
        ]
        expected_assignables = [ShiftAssignable.objects.get(**data_set)
                        for data_set in expected_assignable_data]
        self.assertEqual(set(actual_assignables), set(expected_assignables))
        for assignable in actual_assignables:
            self.assertEqual(assignable.preference.rank==1,
                             assignable.is_active)
            


class ShiftAssignableTest(ShiftTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        pref1 = ShiftPreference.objects.create(child=cls.kids[0],
                                              shift=cls.shifts[0, 8],
                                              period=cls.periods[0],
                                              rank=1)
        pref2 = ShiftPreference.objects.create(child=cls.kids[1],
                                               shift=cls.shifts[2, 13],
                                               period=cls.periods[1],
                                               rank=2)
        pref3 = ShiftPreference.objects.create(child=cls.kids[1],
                                               shift=cls.shifts[0, 8],
                                               period=cls.periods[0],
                                               rank=1)
        pref4 = ShiftPreference.objects.create(child=cls.kids[2],
                                               shift=cls.shifts[0, 8],
                                               period=cls.periods[0],
                                               rank=1)
        cls.sa1 = ShiftAssignable.objects.create(
            preference=pref1, offset=1, offset_modulus=2)
        cls.sa2 = ShiftAssignable.objects.create(
            preference=pref2, offset=1, offset_modulus=4)
        cls.sa3 = ShiftAssignable.objects.create(
            preference=pref3, offset=1, offset_modulus=4)
        cls.sa4 = ShiftAssignable.objects.create(
            preference=pref3, offset=0, offset_modulus=2)
        cls.sa5 = ShiftAssignable.objects.create(
            preference=pref3, offset=1, offset_modulus=2)

        Holiday.objects.create(name="test holiday 1",
                               start=timezone.make_aware(timezone.datetime(2000, 12, 1)),
                               end=timezone.make_aware(timezone.datetime(2000, 12, 31)))
        Holiday.objects.create(name="test holiday 2",
                               start=timezone.make_aware(timezone.datetime(2001, 2, 1)),
                               end=timezone.make_aware(timezone.datetime(2001, 2, 28)))

    def test_occurrences(self):
        actual_occs1 = self.sa1.occurrences()
        expected_occs1 = [
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,9,11)),
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,9,25)),
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,10,9)),
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,10,23)),
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,11,6)),
            ShiftOccurrence(shift=self.shifts[0, 8], date=timezone.datetime(2000,11,20)),
        ]
        self.assertEqual(set(actual_occs1), set(expected_occs1))
        # print(list(self.sa1.occurrences()))
        actual_occs2 = self.sa2.occurrences()        
        expected_occs2 = [
            ShiftOccurrence(shift=self.shifts[2, 13], date=timezone.datetime(2001,1,10)),
            ShiftOccurrence(shift=self.shifts[2, 13], date=timezone.datetime(2001,3,7)),
            ShiftOccurrence(shift=self.shifts[2, 13], date=timezone.datetime(2001,4,4)),
        ]
        self.assertEqual(set(actual_occs2), set(expected_occs2))

        def test_normalized_offsets(self):
            actual1 = self.sa1._normalized_offsets()
            expected1 = {1, 3}
            self.assertEqual(actual1, expected1)
            actual2 = self.sa1._normalized_offsets()
            expected2 = {1}
            self.assertEqual(actual2, expected2)

        def test_is_compatible_with(self):
            self.assertTrue(self.sa1.is_compatible_with(self.sa1))
            self.assertTrue(self.sa1.is_compatible_with(self.sa2))
            self.assertTrue(self.sa1.is_compatible_with(self.sa2))
            self.assertFalse(self.sa1.is_compatible_with(self.sa3))
            self.assertTrue(self.sa1.is_compatible_with(self.sa4))

        def test_create_commitments(self):
            self.sa1.create_commitments()
            actual_created = WorktimeCommitment.objects.filter(
                child=self.kids[0])
            expected_created = [
                WorktimeCommitment.objects.get(timezone.datetime(2000, 9, 11, 8, 0)),
                WorktimeCommitment.objects.get(timezone.datetime(2000,9,25, 8, 0)),
                WorktimeCommitment.objects.get(timezone.datetime(2000,10,9, 8, 0)),
                WorktimeCommitment.objects.get(timezone.datetime(2000,10,23, 8, 0)),
                WorktimeCommitment.objects.get(timezone.datetime(2000,11,6, 8, 0)),
                WorktimeCommitment.objects.get(timezone.datetime(2000,11,20, 8, 0)),
            ]
            self.assertEqual(set(actual_created), set(expected_created))


class WorktimeScheduleManagerTest(ShiftTestCase):
        
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
            
    def test_generate_all_ranked_1(self):
        pref_data = [
            {"shift" : self.shifts[0, 8], "child" : self.kids[0]},
            # {"shift" : self.shifts[1, 8], "child" : self.kids[0]},
            {"shift" : self.shifts[0, 8], "child" : self.kids[1]},
            # {"shift" : self.shifts[2, 8], "child" : self.kids[1]},
            {"shift" : self.shifts[1, 8], "child" : self.kids[2]},
            # {"shift" : self.shifts[1, 13], "child" : self.kids[2]},
            {"shift" : self.shifts[1, 8], "child" : self.kids[3]},
            # {"shift" : self.shifts[0, 15], "child" : self.kids[3]},
        ]
        prefs = [ShiftPreference.objects.create(
            rank=1, period=self.periods[0], **kwargs)
                     for kwargs in pref_data]
        assignables_data = [
            {"preference" : prefs[0], "offset" : 0},
            {"preference" : prefs[0], "offset" : 1},
            {"preference" : prefs[1], "offset" : 0},
            {"preference" : prefs[1], "offset" : 1},
           
            {"preference" : prefs[2], "offset" : 0},
            {"preference" : prefs[2], "offset" : 1},
            {"preference" : prefs[3], "offset" : 1},
        ]
        assignables = [ShiftAssignable.objects.create(
            offset_modulus=2, is_active=True, **kwargs)
                       for kwargs in assignables_data]
        actual_schedules = list(WorktimeSchedule.objects.generate(self.periods[0]))
                
        # should have two assignments on kids 0, 1; two on kid 2; and one on kid 3
        # so four possible total assignments
        
        self.assertEqual(2, len(actual_schedules))
        for sched in actual_schedules:
            self.assertTrue(assignables[0] in sched.assignments_set.all()\
                            != assignables[1] in sched.assignments_set.all())
            self.assertTrue(assignables[2] in sched.assignments_set.all()\
                            != assignables[3] in sched.assignments_set.all())
            self.assertTrue(assignables[0] in sched.assignments_set.all()\
                            != assignables[2] in sched.assignments_set.all())
            self.assertTrue(assignables[6] in sched.assignments_set.all())
            self.assertFalse(assignables[5] in sched.assignments_set.all())
            self.assertTrue(assignables[4] in sched.assignments_set.all())            
