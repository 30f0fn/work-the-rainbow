import datetime
import ast
from collections import defaultdict
from itertools import chain
import json

import random
import constraint
from constraint import *
import itertools

from django.db import models
from django.utils import timezone

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField, WEEKDAYS
from main.utilities import WeekdayIterator, next_date_with_given_weekday, add_delta_to_time, dates_in_range, in_a_week, serialize_datetime, deserialize_datetime
# import main.scheduler
from people.views import ClassroomMixin

# todo rename CareDay to CareSession

# todo standardize __repr__ 

# todo subclass CareDayAssignment with ContractedCareDayAssignment, for preferences etc

# todo check for timezone awareness... timezone.datetime.combine seems to return non-aware datetimes (?)

# todo clarify which items have meaningful datetime, which have only meaningful date

"""
for generic __str__ method:
str_attrs_list = ['attr1', 'attr2']
str_attrs = ",".join([f"{attr}={getattr(self, attr)}" for attr in self.display_attrs])
return f"<{self.__class__.__name__} {self.pk}: " + str_attrs + ">"
"""
    
"""
todo
all events have start_date
one-day events have computed property date
maybe all events have an iterator dates?  ---not useful for queries
"""

"""
what contents need to get indexed by date?

shift, careday, holiday, worktimecommitment, 
"""


class EventManager(models.Manager):

    def overlaps(self, start, end): 
        """get all h which overlap with given start and end datetimes"""
        return super().get_queryset().filter(start__lte=end,
                                             end__gte=start)

    # 
    def spans(self, start, end): 
        """get all h which span given start and end datetimes"""
        return super().get_queryset().filter(start__lte=start,
                                             end__gte=end)

    # def _by_date(self, start, end, restriction=None):
    #     """map each date in range to the list of its events"""
    #     events = super().get_queryset().filter(start__lte=end,
    #                          end__gte=start)
    #     dates = dates_in_range(start, end)
    #     results = defaultdict(list)
    #     for event in events:
    #         # if event.start.date() <= date <= event.end.date():
    #         results[event.start.date()].append(event)
    #     return results

    # def by_date_and_time(self, start, end, restriction=None):
    #     """map each date to a mapping from times to events"""
    #     by_date = self._by_date(start, end, restriction=restriction)
    #     results = defaultdict(dict)
    #     for date in by_date:
    #         for event in by_date[date]:
    #             results[date][event.start.time()] = event
    #     return results

    def _dates_for_range(self, start, end, restriction=None):
        """return all dates spanned by any event within given range
        
        mainly used for Holiday class to detect cancellations
        """
        # dates = (date for event in self.overlaps(start, end)
                 # for date in event.all_dates()
                 # if start <= date <= end)
        return set(date for event in self.overlaps(start, end)
                 for date in event.all_dates()
                 if start <= date <= end)



class Event(models.Model):
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(blank=True, null=True)

    @property
    def date(self):
        return self.start.date()

    def all_dates(self):
        return dates_in_range(self.start, self.end)

    def has_started(self):
        return timezone.now() > self.start

    def save(self, *args, **kwargs):
        self.end = self.end or self.start.replace(hour=23, minute=59)
        super().save(*args, **kwargs)

    objects = EventManager()

    class Meta:
        ordering = ['start', 'end']
        abstract = True




class WeeklyEventManager(EventManager):

    # todo support filtering ?
    def occurrences_for_date_range(self, start, end, ignore_holidays=False):
        """enumerate all occurrences in range, for all weekly events"""
        occ_nest = (weekly_event.occurrences_for_date_range(start, end,
                                                   ignore_holidays=True)
                    for weekly_event in super().get_queryset().all())
        occurrences = list(chain.from_iterable(occ_nest))
        occurrences.sort(key=lambda x: x.start)
        exdates = ([] if ignore_holidays
                   else Holiday.objects._dates_for_range(start, end))
        for occ in occurrences:
            if occ.start not in exdates:
                yield occ

    # return a dictionary of dictionaries
    def occurrences_by_date_and_time(self, start, end):
        # this makes sense only if no two instances same start dt
        results = defaultdict(dict)
        # date = start.date()
        occurrences = self.occurrences_for_date_range(start, end)
        for occurrence in occurrences:
            results[occurrence.start.date()][occurrence.start.time()] = occurrence
        return results


class WeeklyEvent(models.Model):
    start_time = models.TimeField() # todo timezone-aware?
    end_time = models.TimeField()
    weekday = WeekdayField()

    objects = WeeklyEventManager()

    def _occurrence_class(self):
        return globals()[self.__class__.__name__+'Occurrence']

    def initialize_occurrence(self, date):
        assert int(self.weekday) == date.weekday()
        return self._occurrence_class()(self, date)


    def occurrences_for_date_range(self, start, end, ignore_holidays=False):
        """yield all occurrences of the WeeklyEvent on any date between dates of start and end datetimes, inclusive"""
        exclusions = ({} if ignore_holidays 
                      else Holiday.objects._dates_for_range(start, end))
        dt = timezone.datetime.combine(
            next_date_with_given_weekday(self.weekday, start),
            self.start_time)
        if not end.tzinfo:
            end = timezone.make_aware(end)
        dt = timezone.make_aware(dt)

        while dt.date() <= end.date():
            if dt.date() not in exclusions:
                yield self.initialize_occurrence(dt)
            dt += datetime.timedelta(days=7)

    class Meta:
        abstract = True
        ordering = ['weekday', 'start_time']

    def weekday_str(self):
        return WEEKDAYS[self.weekday]



class WeeklyEventOccurrence(object):

    def __init__(self, weekly_event, date):
        weekly_cls_name = self.__class__.__name__[:-len("Occurrence")]
        setattr(self, weekly_cls_name.lower(), weekly_event)
        # self.weekly_event = weekly_event
        self.start = timezone.datetime.combine(date, weekly_event.start_time)
        self.end = timezone.datetime.combine(date, weekly_event.end_time)

    class Meta:
        abstract = True

    def __repr__(self):
        # note this gives identical values for weeklyevent occurrences with same weekly class and same start time, which is bad
        return f"{self.__class__.__name__}: start={self.start}"



##########################
# Simple Concrete Events #
##########################



class Holiday(Event):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        end = '-'+str(self.end) if (self.end.date() != self.start.date()) else ''
        return f"{self.name} ({self.start.date()}{end})"


class Happening(Event):
    name = models.CharField(max_length=50)
    description = models.TextField()
    

class Period(Event):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    solicits_preferences = models.BooleanField(default=True)


    def __str__(self):
        return f"<Period {self.pk}: {self.start} - {self.end}>"


#######################
# CareDays and Shifts #
#######################


class CareDay(WeeklyEvent):
    """regular day and extension are disjoint caredays"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)

    @property
    def shifts(self):
        return Shift.objects.filter(weekday=self.weekday, 
                                    start_time__gte=self.start_time,
                                    end_time__lte=self.end_time,
                                    classroom=self.classroom)

    def __repr__(self):
        return f"<CareDay {self.pk}: weekday={self.weekday}, start_time={self.start_time}, end_time={self.end_time}>"

    def __str__(self):
        return f"{WEEKDAYS[self.weekday][:3]}, {self.start_time} - {self.end_time} ({self.classroom.slug})"



class CareDayOccurrence(WeeklyEventOccurrence):

    def __init__(self, careday, date, **kwargs):
        # shift = kwargs.pop('shift')
        # date = kwargs.pop('date')
        super().__init__(careday, date)
        self.careday = careday
        self.classroom=self.careday.classroom


    def children(self):
        return Child.objects.filter(classroom=self.careday.classroom,
                                    caredayassignment__careday=self.careday,
                                    caredayassignment__end__gte=self.start,
                                    caredayassignment__start__lte=self.end,
                                    ).distinct()
    
    def shift_occurrences(self):
        for shift in Shift.objects.filter(weekday=self.careday.weekday,
                                          start_time__lte=self.careday.start_time,
                                          end_time__gte=self.careday.start_time,
                                          classroom=self.classroom):
            yield ShiftOccurrence(shift=shift, date=self.start.date())





class CareDayAssignmentManager(WeeklyEventManager):

    # not in use
    def create_multiple(self, child, caredays, start, end):
        for careday in caredays:
            CareDayAssignment.objects.create(
                child=child, careday=careday, start=start, end=end)

    def create(self, child, careday, start, end):
        overlaps = self.overlaps(child, start, end, careday=careday)
        for assignment in overlaps:
            assignment.extend_to(start, end)
        if not overlaps:
            super().create(child=child, careday=careday, start=start, end=end)

    def overlaps(self, child, start, end, careday=None):
        o = super().overlaps(start, end).filter(
            child=child).select_related('careday')
        if careday:
            o = o.filter(careday=careday)
        return o

    def spans(self, start, end): 
        # todo is this the right way to call filter in the manager?
        return super().filter(start__lte=start,
                              end__gte=end)


    def remove_child_from_careday_for_range(self, careday, child, start, end):
        for assignment in self.overlaps(
                child, start, end,
                careday=careday):
            assignment.retract_from(start, end)


    # todo below seems sketchy
    def careday_occurrences_for_child(self, child, start, end):
        """for each weekday, list all caredayassignments which overlap the daterange; then for each date, yield caredayoccurrence if possible, then eliminate those caredayassignments with enddate <= that date"""
        assignments_by_weekday = [[assignment for assignment in reversed(
            self.overlaps(child, start, end))
                                   if assignment.careday.weekday==weekday]
                                  for weekday in WEEKDAYS]
        # for w in assignments_by_weekday:
        #      print(w)
        for date in dates_in_range(start, end):
            assignments = assignments_by_weekday[date.weekday()]
            for assignment in reversed(assignments):
                if assignment.end >= date:
                    # print(assignment.careday.weekday)
                    # print(date.weekday())
                    yield assignment.careday.initialize_occurrence(date)
                if assignment.start > date:
                    break
            for assignment in reversed(assignments):
                if assignment.end <= date:
                    assignments.remove(assignment)


class CareDayAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE) 
    careday = models.ForeignKey(CareDay, on_delete=models.CASCADE)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=in_a_week)

    objects = CareDayAssignmentManager()

    def extend_to(self, start, end):
        # self must weakly overlap [start, end]
        self.start = min(start, self.start.date())
        self.end = max(end, self.end.date())
        self.save()

    def retract_from(self, start, end):
        if self.end > start:
            self.end = start
            if end < self.end: #strict inclusion, so need another
                self.pk, second = None, self 
                second.start = end 
                second.save()
        if self.start < end:
            self.start = end
            self.save()

    def careday_occurrences(self, start, end):
        careday_dict = defaultdict(dict)
        for careday in self.caredays:
            careday_dict[careday.weekday][careday.start_time] = careday
        for date in self.dates_in_range:
            for careday_occurrence in careday_dict[date.weekday()].values():
                yield careday_occurrence
        
    def shift_occurrences(self, start, end):
        for careday_occurrence in self.occurrences_for_date_range(start, end):
            for shift_occurrence in careday_occurrence.shift_occurrences:
                yield shift_occurrence
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.pk}>: child={self.child}, careday={self.careday}, start={self.start}, end={self.end}"

    def __str__(self):
        return f"{self.careday} for {self.child}, from {self.start.date()} through {self.end.date()}"

    class Meta:
        ordering = ['careday', 'start', 'end']


"""
given caredaycontracts of child, access its possible shifts
conversely, access children from shift
"""



##########
# Shifts #
##########


class ShiftManager(WeeklyEventManager):

    # todo shouldn't this be a method of WeeklyEventManager?
    # or maybe a custom queryset method?
    def occurrences_for_date_range(self, start, end,
                                   include_commitments=False,
                                   classrooms=[],
                                   child=None):
        occ_nest = (shift.occurrences_for_date_range(
            start, end, ignore_holidays=True)
                    for shift in self.all().select_related('classroom'))
        occurrences = list(chain.from_iterable(occ_nest))
        occurrences.sort(key=lambda x: x.start)
        exdates = Holiday.objects._dates_for_range(start, end)
        for occ in occurrences:
            if occ.start not in exdates:
                yield occ

    def occurrences_by_date_and_time(self, start, end,
                                     include_commitments=False,
                                     classrooms=[]):
        """option to include worktime commitments for given shiftoccurrences"""
        results = super().occurrences_by_date_and_time(start, end)
        if include_commitments:
            commitments = WorktimeCommitment.objects.filter( 
                start__range=(start, end)).select_related("child")
            if classrooms:
                commitments = commitments.filter(child__classroom__in=classrooms)
            for commitment in commitments:
                start = commitment.start
                results[start.date()][start.time()].commitment = commitment
                # print(commitment)
                # print(results[start.date()][start.time()])
                # print(results[start.date()][start.time()].commitment)
        return results

    def by_weekday_and_time(self, classroom):
        shifts = Shift.objects.filter(classroom=classroom).order_by('start_time')
        # for each weekday, list all shifts in order of time
        shifts_dict = defaultdict(list)
        for shift in shifts:
            shifts_dict[shift.weekday].append(shift)
        return shifts_dict


class Shift(WeeklyEvent):

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)

    objects = ShiftManager()

    def children(self):
        return self.careday().children()

    def careday(self):
        return CareDay.objects.get(weekday=self.weekday,
                                   start_time__lte=self.start_time,
                                   end_time__gte=self.end_time)

    def __repr__(self):
        return f"<Shift {self.pk}: weekday={self.weekday}, time={self.start_time}>"

    def __str__(self):
        return f"{WEEKDAYS[self.weekday]} {self.start_time}"


class ShiftOccurrence(WeeklyEventOccurrence):
    # include classroom field? 

    # todo inherit then override
    def __init__(self, shift, date, **kwargs):
        # shift = kwargs.pop('shift')
        # date = kwargs.pop('date')
        if int(shift.weekday) != (date.weekday()):
            raise ValueError(
                f"The shift {shift} has no occurrence on {date}, because {shift.weekday} != {date.weekday()}")
        super().__init__(shift, date)
        self.classroom=self.shift.classroom
        self.commitment = kwargs.pop('commitment', None)

    # dont inherit
    def create_commitment(self, child):
        commitment = WorktimeCommitment(
            start = self.start,
            end = self.end,
            child = child)
        commitment.save()

    def get_commitment(self):
        return WorktimeCommitment.objects.get(
            shift=self.shift,
            date=self.date)

    def is_available_to_child(self, child):
        # todo make configurable from settings
        maxtime = timezone.datetime.max.time()
        earliest = timezone.now().replace(
            hour=maxtime.hour, minute=maxtime.minute)
        if not self.start.tzinfo:
            self.start = timezone.make_aware(self.start)
        return self.start >= earliest\
            and (getattr(self, "commitment", None)==None or self.commitment.child==child)


    def __str__(self):
        return f"{self.start.strftime('%-H:%M %a, %-d %b')} ({self.classroom.slug})"

    def __repr__(self):
        result = super().__repr__()+f", classroom={self.classroom}"
        if self.commitment:
            result += f", commitment={self.commitment}"
        return result


    # todo this is ugly; also do I need to convert repr_dict to string?
    def serialize(self):
        repr_dict = {'shift' : self.shift.pk,
                     'start' : serialize_datetime(self.start),
                     'commitment' : (self.commitment.pk if self.commitment
                                     else None)}
        return repr(repr_dict)

    @staticmethod
    def deserialize(repr_string):
        repr_dict = ast.literal_eval(repr_string)
        shift = Shift.objects.get(pk = repr_dict['shift'])
        dt = deserialize_datetime(repr_dict['start'])
        sh_occ = ShiftOccurrence(shift, dt)
        sh_occ.commitment = repr_dict.get('commitment')
        return sh_occ


        
class WorktimeCommitmentManager(EventManager):
    
    def create(self):
        super().create()
        # todo add notification

    def delete(self):
        super.delete()
        # todo add notification

         
# don't create these directly; instead use create_commitment instance method of ShiftOccurrence
class WorktimeCommitment(Event):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    completed = models.NullBooleanField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)

    completion_status_dict = {True : "complete",
                              False : "missed",
                              None : ""}

    def show_completion_status(self):
        return self.completion_status_dict[self.completed]
        

    def shift_occurrence(self):
        return ShiftOccurrence(shift=self.shift,
                               date=self.start.date(),
                               commitment=self)

    def move_to(self, shift_occurrence):
        old_shiftoccurrence = self.shift_occurrence()
        self.shift = shift_occurrence.shift
        self.start = shift_occurrence.start
        self.end = shift_occurrence.end
        self.save()
        

    def save(self, *args, **kwargs):
        self.shift = self.shift or Shift.objects.get(
            classroom=self.child.classroom,
            start_time=self.start.time(),
            weekday=self.start.weekday())
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.shift_occurrence())

    def alternatives(self, earlier, later):
        dt_min = max(timezone.now(), self.start - earlier).replace(
            hour=timezone.datetime.min.hour,
            minute=timezone.datetime.min.minute)
        dt_max = max(timezone.now(), self.start + later).replace(
            hour=timezone.datetime.max.hour,
            minute=timezone.datetime.max.minute)
        maybe_alts = self.child.possible_shifts(
            start=dt_min,
            end=dt_max)
        commitments = WorktimeCommitment.objects.by_date_and_time(
            start=dt_min, end=dt_max)
        print("COMMITMENTS: ", commitments)
        for occ in maybe_alts:
            # print(getattr(occ, 'commitment', None))
            c = commitments[occ.start.date()].get(occ.start.time())
            print(c)
            if c in [None, self]:
                occ.commitment = c
                yield occ

    class Meta:
        unique_together = (("shift", "start"),)


class ShiftPreferenceManager(models.Manager):

# assume shifts_by_weekday_and_time

    def by_shift(self, period):
        shifts = Shift.objects.filter(classroom=period.classroom)
        preferences = ShiftPreference.objects.filter(
            period=period).order_by('shift', 'rank')
        prefs_dict = defaultdict(list)
        for pref in preferences:
            prefs_dict[pref.shift].append(pref)
        return prefs_dict


    def by_time_and_weekday(self, period):
        preferences = super().filter(
            period=period).order_by('shift', 'rank').select_related('shift')
        prefs_dict = defaultdict(dict)
        for pref in preferences:
            prefs_dict[pref.shift.start_time][pref.shift.weekday] = pref
        return prefs_dict




class ShiftPreference(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    rank_choices = ((1, 'best'), (2, 'pretty good'), (3, 'acceptable'))
    rank = models.IntegerField(choices=rank_choices, default=3,
                               null=True, blank=True)
    period = models.ForeignKey(Period, blank=True, null=True, on_delete=models.PROTECT)
    
    objects = ShiftPreferenceManager()

    def __repr__(self):
        return f"<ShiftPreference {self.pk}: {self.child} ranks {self.shift} as {self.rank}>"

    class Meta:
        unique_together = (("child", "shift", "period"), )
        ordering = ('period', 'rank', 'shift')


class ShiftAssignmentCollectionManager(models.Manager):

    # todo below is super-ugly and should be in scheduler.py
    def generate(self, period, no_worse_than=1):
        ShiftAssignmentCollection.objects.filter(period=period).delete()
        problem = Problem()
        all_families = Child.objects.filter(classroom=period.classroom)
        families = []
        preferences = []
        for f, child in enumerate(all_families):
            print(child)
            fam_prefs = ShiftPreference.objects.filter(
                child=child,
                rank__lte=no_worse_than,
                period=period)
            if fam_prefs:
                preferences.append(fam_prefs)
                families.append(child)
        for f in range(len(families)):
            problem.addVariable(f, preferences[f])
        for c1,c2,c3 in itertools.combinations(range(len(families)), 3):
            print("c1,c2,c3:", c1,c2,c3)
            problem.addConstraint((lambda p1, p2, p3:
                                   not(p1.shift == p2.shift == p3.shift)),
                                  [c for c in [c1,c2,c3]])
            # print("constraint:", lambda s1, s2, s3: not(s1 == s2 == s3))
        # print("families with preferences: ", families)
        retval = []
        solutions = problem.getSolutions()
        # print("solutions", solutions)
        for solution in solutions:
            print("solution:", solution)
            collection = ShiftAssignmentCollection.objects.create(period=period)
            for f, family in enumerate(families):
                sh = ShiftAssignment.objects.create(child=family,
                                                    shift=solution[f].shift,
                                                    collection=collection,
                                                    rank=solution[f].rank)
            retval.append(solution)
            print("retval", retval)
        return retval




class ShiftAssignmentCollection(models.Model):
    date = models.DateTimeField(default=timezone.now)
    period = models.ForeignKey(Period, on_delete = models.CASCADE)
    objects = ShiftAssignmentCollectionManager()
    
    def score(self):
    #     # todo this is horribly inefficient but can't see how to combine all these scores into one query 
        retval = 0
        prefs = ShiftPreference.objects.filter(period=period)
        for assn in self.shiftassignment_set.all():
            for pref in prefs:
                if pref.child == assn.child and pref.shift == asn.shift:
                    retval += pref.rank
                    break
            retval += float("inf")
            break
        return retval

    def create_commitments(self):
        shifts = Shift.objects.filter(classroom=self.period.classroom)
        assignments = self.shiftassignment_set.all()
        offset = 0
        for sh in shifts:
            offset = offset + 1
            available_indices = [(offset + i) % 4 for i in range(4)]
            # instead of cycling the indices, keep a count of how many times an index has been used, then always pick the least-used index first
            families = [assignment.child for assignment in assignments
                        if assignment.shift == sh]
            sh_occs = list(sh.occurrences_for_date_range(self.period.start,
                                                         self.period.end))
            assert(sum([child.shifts_per_month for child in families]) <= 4)
            families.sort(key = lambda c : -c.shifts_per_month)
            # so either [0,1,2,3] or [1,2,3,4]
            def assign_from_index(child, index):
                for occ in sh_occs[index::4]:
                    commitment = occ.create_commitment(child)
            for child in families:
                first_index = available_indices.pop()
                assign_from_index(child, first_index)
                available_indices.remove(first_index)
                if child.shifts_per_month == 2:
                    second_index = (first_index + 2) % 4
                    # must be available, since child has at most one predecessor (else sum of children's shifts per months exceeds four), and that predecessor has different parity 
                    available_indices.remove(second_index)
                    assign_from_index(child, second_index)


    
class ShiftAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    collection = models.ForeignKey(ShiftAssignmentCollection,
                                   on_delete=models.CASCADE)
    rank_choices = ((1, 'best'), (2, 'pretty good'), (3, 'acceptable'))
    rank = models.IntegerField(choices=rank_choices, default=3,
                               null=True, blank=True)

    def __repr__(self):
        return f"<Assignment {self.pk} in collection {self.collection.pk}: {self.child.nickname} gets {self.shift}>"



