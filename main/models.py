import datetime
import ast
from collections import defaultdict
import itertools
import json
import random
from constraint import *

from django.db import models
from django.utils import timezone

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField, WEEKDAYS
from main.utilities import WeekdayIterator, next_date_with_given_weekday, dates_in_range, in_a_week, serialize_datetime, deserialize_datetime
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

    def spans(self, start, end): 
        """get all events which span given start and end datetimes"""
        return super().get_queryset().filter(start__lte=start,
                                             end__gte=end)

    def _by_date(self, start, end, restriction=None):
        """map each date in range to the list of its events"""
        events = super().get_queryset().filter(start__lte=end,
                             end__gte=start)
        dates = dates_in_range(start, end)
        results = defaultdict(list)
        for event in events:
            # if event.start.date() <= date <= event.end.date():
            results[event.start.date()].append(event)
        return results

    def by_date_and_time(self, start, end, restriction=None):
        """map each date to a mapping from times to events"""
        by_date = self._by_date(start, end, restriction=restriction)
        results = defaultdict(lambda : defaultdict(list))
        for date in by_date:
            for event in by_date[date]:
                results[date][event.start.time()].append(event)
        return results

    def _dates_for_range(self, start, end, restriction=None):
        """return all dates spanned by any event within given range
        
        mainly used for Holiday class to detect cancellations
        """
        # dates = (date for event in self.overlaps(start, end)
                 # for date in event.all_dates()
                 # if start <= date <= end)
        # print(f"overlaps = {self.overlaps(start, end)}")
        return set(date for event in self.overlaps(start, end)
                 for date in event.all_dates()
                   if start.date() <= date <= end.date())



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
        ordering = ['start']
        abstract = True



class _WeeklyEventFormatter(object):
    """various functions drawing on data from _events() 
    classes which implement _events() include
    WeeklyEventQuerySet, WeeklyEvent"""

    def by_weekday(self):
        events_by_weekday = [[] for _ in range(7)]
        for event in self._events():
            events_by_weekday[int(event.weekday)].append(event) 
        return events_by_weekday

    # def by_weekday_and_time(self):
    #     # for each weekday, list all shifts in order of time
    #     shifts_dict = defaultdict(list)
    #     for shift in shifts:
    #         shifts_dict[shift.weekday].append(shift)
    #     return shifts_dict

    def occurrences_for_date_range(self, start, end, ignore_holidays=False):
        """enumerate all occurrences with date in daterange, inclusive"""
        exclusions = ([] if ignore_holidays
                      else Holiday.objects._dates_for_range(start, end))
        for date in dates_in_range(start, end):
            if date not in exclusions:
                for event in self.by_weekday()[date.weekday()]:
                    yield event.initialize_occurrence(date)

    def occurrences_by_date(self, start, end, ignore_holidays=False, **kwargs):
        occurrences = self.occurrences_for_date_range(
            start, end, ignore_holidays=ignore_holidays,
            **kwargs)
        retval = defaultdict(list)
        retval.update({date : list(occs)
                       for date, occs in itertools.groupby(
                               occurrences, lambda o : o.start.date())})
        return retval
            
    def occurrences_by_date_and_time(self, start, end, ignore_holidays=False, **kwargs):
        occurrences_by_date = self.occurrences_by_date(
            start, end, ignore_holidays=ignore_holidays, **kwargs)
        data = {date : {occ.start.time() : occ for occ in occurrences_by_date[date]}
                for date in occurrences_by_date}
        return defaultdict(lambda : defaultdict(list), data)


class WeeklyEventQuerySet(_WeeklyEventFormatter,
                          models.QuerySet):

    def _events(self):
        return self.all()


class WeeklyEvent(_WeeklyEventFormatter, models.Model):
    start_time = models.TimeField() # todo timezone-aware?
    end_time = models.TimeField()
    weekday = WeekdayField()

    objects = WeeklyEventQuerySet.as_manager()

    def _events(self):
        return [self]

    def _occurrence_class(self):
        return globals()[self.__class__.__name__+'Occurrence']

    def initialize_occurrence(self, date):
        assert int(self.weekday) == date.weekday()
        return self._occurrence_class()(self, date)



    class Meta:
        abstract = True
        ordering = ['weekday', 'start_time']

    def weekday_str(self):
        return WEEKDAYS[self.weekday]


class IdentityMixin(object):

    def __hash__(self):
        if '__identity__' in dir(self):
            return hash(self.__identity__())
        else:
            return super().__hash__()

    def __eq__(self, other):
        return self.__identity__() == other.__identity__() if '__identity__' in dir(self) else super().__eq__(other)    

    def __ne__(self, other):
        return not self.__eq__(other)


# todo implement equality?
class WeeklyEventOccurrence(IdentityMixin, object):

    def __init__(self, weekly_event, date):
        weekly_cls_name = self.__class__.__name__[:-len("Occurrence")]
        setattr(self, weekly_cls_name.lower(), weekly_event)
        # self.weekly_event = weekly_event
        self.start = timezone.make_aware(
            timezone.datetime.combine(date, weekly_event.start_time))
        self.end = timezone.make_aware(
            timezone.datetime.combine(date, weekly_event.end_time))



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

    # @property
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
        
    def __identity__(self):
        return (self.careday.pk,
                self.start, self.end)

    def children(self):
        return Child.objects.filter(classroom=self.careday.classroom,
                                    caredayassignment__careday=self.careday,
                                    caredayassignment__end__gte=self.start,
                                    caredayassignment__start__lte=self.end,
                                    ).distinct()
    
    def shift_occurrences(self):
        for shift in Shift.objects.filter(weekday=self.careday.weekday,
                                          start_time__gte=self.careday.start_time,
                                          end_time__lte=self.careday.end_time,
                                          classroom=self.classroom):
            yield ShiftOccurrence(shift=shift, date=self.start.date())
 


class CareDayAssignmentManager(EventManager):

    # # not in use
    # def create_multiple(self, child, caredays, start, end):
    #     for careday in caredays:
    #         CareDayAssignment.objects.create(
    #             child=child, careday=careday, start=start, end=end)

    def overlaps(self, child, start, end, careday=None):
        o = super().overlaps(start, end).filter(
            child=child)
        if careday:
            o = o.filter(careday=careday)
        return o

    # def create(self, child, careday, start, end):
    #     overlaps = self.overlaps(child, start, end, careday=careday)
    #     new_start = min([o.start.date() for o in overlaps] + [start])
    #     new_end = max([o.end.date() for o in overlaps] + [end])
    #     super().create(child=child,
    #                    careday=careday,
    #                    start=new_start,
    #                    end=new_end)
    #     overlaps.delete()
    #     # for assignment in overlaps:
    #         # assignment.extend_to(start, end)
    #     # if not overlaps:
    #         # super().create(child=child, careday=careday, start=start, end=end)

    def remove_child_from_careday_for_range(self, careday, child, start, end):
        for assignment in self.overlaps(
                child, start, end,
                careday=careday):
            assignment.retract_from(start, end)

    # todo implement as queryset method, like with Shift
    def occurrences_for_child(self, child, start, end):
        assignments = self.overlaps(child, start, end)
        assignments_by_weekday = [
            [assignment for assignment in assignments
             if assignment.careday.weekday==weekday]
            for weekday in WEEKDAYS]
        for date in dates_in_range(start, end):
            for assignment in assignments_by_weekday[date.weekday()]:
                if assignment.start.date() <= date <= assignment.end.date():
                    yield assignment.careday.initialize_occurrence(date)





class CareDayAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE) 
    careday = models.ForeignKey(CareDay, on_delete=models.CASCADE)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=in_a_week)

    objects = CareDayAssignmentManager()

    def retract_from(self, start, end):
        """revise self (creating another if necessary) as required to remove from child all assignments to caredays from start to end inclusive"""
        assert start >= end
        if self.end < start or self.start > end:
            # disjoint
            pass
        elif self.start >= start and self.end <= end:
            # self weakly included by range
            self.delete()
        elif self.start < start < end < self.end:
            # self strictly includes range, so need split
            self.end = start - datetime.timedelta(days = 1)
            self.save()
            CareDayAssignment.objects.create(
                start = end + datetime.timedelta(days = 1),
                end = self.end,
                careday = self.careday)
        elif self.start >= start:
            # then self.end > start since per above, self is not weakly included
            self.start = end + datetime.timedelta(days = 1)
            self.save()
        elif self.end <= end:
            # then self.start < start since per above, self is not weakly included 
            self.end = start - datetime.timedelta(days = 1)
            self.save()

        raise Exception("Unhandled daterange comparison!")

    def save(self, *args, **kwargs):
        # todo some view logic should prevent start > end
        if self.start > self.end and self.pk:
            self.delete()
            return
        overlaps = CareDayAssignment.objects.overlaps(
            self.child, self.start, self.end, careday=self.careday)
        new_start = min(cda.start for cda in list(overlaps) + [self])
        new_end = max(cda.end for cda in list(overlaps) + [self])
        overlaps.delete()
        self.start = new_start
        self.end = new_end
        super().save()

    def occurrences_for_date_range(self, start, end, ignore_holidays=True):
        for occ in self.careday.occurrences_for_date_range(
                start = max(self.start, start),
                end = min(self.end, end),
                ignore_holidays = ignore_holidays):
            yield occ

    # def careday_occurrences(self, start, end):
    #     careday_dict = defaultdict(dict)
    #     for careday in self.caredays:
    #         careday_dict[careday.weekday][careday.start_time] = careday
    #     for date in self.dates_in_range:
    #         for careday_occurrence in careday_dict[date.weekday()].values():
    #             yield careday_occurrence
        
    # def shift_occurrences(self, start, end):
    #     for careday_occurrence in self.occurrences_for_date_range(start, end):
    #         for shift_occurrence in careday_occurrence.shift_occurrences:
    #             yield shift_occurrence
    
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


class ShiftQuerySet(WeeklyEventQuerySet):

    def occurrences_for_date_range(self, start, end, ignore_holidays=False, include_commitments=False):
        """option to include commitments for a classroom"""
        
        wtc_dict = {}
        if include_commitments:
            for wtc in WorktimeCommitment.objects.filter(
                    shift__in=self.all(),
                    start__gte=start,
                    end__lte=end):
                wtc_dict[wtc.start] = wtc
        occs = super().occurrences_for_date_range(start, end, ignore_holidays)
        for occ in occs:
            occ.commitment = wtc_dict.get(occ.start, None)
            yield occ
    

class Shift(WeeklyEvent):

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)

    objects = ShiftQuerySet.as_manager()

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
                f"The shift {shift} has no occurrence on {date},\
                because {shift.weekday} != {date.weekday()}")
        super().__init__(shift, date)
        self.classroom=self.shift.classroom
        self.commitment = kwargs.pop('commitment', None)

    def __identity__(self):
        return (self.classroom.pk, self.start)

    def create_commitment(self, child):
        """commit child to this occurrence
        doesn't check whether it's covered by a careday"""
        # shift = Shift.objects.get(classroom=child.classroom,
                                  # start_time=self.start.time(),
                                  # weekday=str(self.start.date().weekday()))
        commitment = WorktimeCommitment(
            start = self.start,
            end = self.end,
            child = child,
            shift = self.shift)
        self.commitment = commitment
        commitment.save()
        return commitment

    def get_commitment(self):
        return getattr(self, 'commitment', None) or WorktimeCommitment.objects.get(
            shift=self.shift,
            start=self.start)

    def reservation_deadline(self):
        maxtime = timezone.datetime.max.time()
        day_before = self.start - datetime.timedelta(days=1)
        if not self.start.tzinfo:
            self.start = timezone.make_aware(self.start)
        deadline = day_before.replace(
            hour=maxtime.hour, minute=maxtime.minute)
        return deadline


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
    def deserialize(repr_string, include_commitment=False):
        repr_dict = ast.literal_eval(repr_string)
        shift = Shift.objects.get(pk=repr_dict['shift'])
        dt = deserialize_datetime(repr_dict['start'])
        shocc = ShiftOccurrence(shift, dt)
        if include_commitment:
            shocc.commitment = WorktimeCommitment.objects.get(pk=int(repr_dict.get('commitment')))
        return shocc
 

class WorktimeCommitment(Event):
    """assignment of Child to ShiftOccurrence (via shift, date fields)
    don't create these directly; 
    instead use create_commitment instance method of ShiftOccurrence
    note that the fields are a bit redundant, because from event superclass it has a datetimefield start while theshift field gives it a timefield start_time
    todo: throw error if we try to assign commitment to holiday?
    """

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
        """should be noop when instance is initialized through ShiftOccurrence instance method"""
        self.shift = self.shift or Shift.objects.get(
            classroom=self.child.classroom,
            start_time=self.start.time(),
            weekday=self.start.weekday())
        super().save(*args, **kwargs)

    def __str__(self):
        return f'commitment of {str(self.child)} to {str(self.shift_occurrence())}'

    def alternatives(self, earlier, later):
        """enumerate all shiftoccurrences for classroom of child of commitment, minus those already committed, plus shiftoccurrence of current commitment, whose careday is in the caredayassignment of the child"""
        dt_min = max(timezone.now(), self.start - earlier).replace(
            hour=timezone.datetime.min.hour,
            minute=timezone.datetime.min.minute)
        dt_max = max(timezone.now(), self.start + later).replace(
            hour=timezone.datetime.max.hour,
            minute=timezone.datetime.max.minute)
        assignments = CareDayAssignment.objects.occurrences_for_child(
            child=self.child, start=dt_min, end=dt_max)
        sh_occs = (sh_occ for cdo in assignments
                   for sh_occ in cdo.shift_occurrences())
        # print(WorktimeCommitment.objects.all())
        commitments_by_start = {wtc.start : wtc \
                                for wtc in WorktimeCommitment.objects.filter(
                                        child__classroom=self.child.classroom,
                                        start__gte=dt_min, end__lte=dt_max)}
        print(f"commitments_by_start={commitments_by_start}")
        for proposed_occ in sh_occs:
            if commitments_by_start.get(proposed_occ.start, self) == self:
                print(f"yielded proposed_occ {proposed_occ}")
                print(commitments_by_start.get(proposed_occ.start))
                print(proposed_occ.start)
                yield proposed_occ
            else:
                print(f"skipped proposed_occ {proposed_occ}")

    class Meta:
        unique_together = (("shift", "start"),)
        ordering = ['start']


class ShiftPreferenceManager(models.Manager):

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
        prefs_dict = defaultdict(lambda : defaultdict(list))
        for pref in preferences:
            prefs_dict[pref.shift.start_time][pref.shift.weekday].append(pref)
        return prefs_dict


class ShiftPreference(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    rank_choices = ((1, 'best'), (2, 'pretty good'), (3, 'acceptable'))
    rank = models.IntegerField(choices=rank_choices, default=3,
                               null=True, blank=True)
    objects = ShiftPreferenceManager()

    def generate_assignables(self):
        modulus = ShiftAssignable.NORMAL_MODULUS // self.child.shifts_per_month 
        # print(f"modulus={modulus}")
        for offset in range(modulus):
            yield ShiftAssignable.objects.create(preference=self,
                                                 offset_modulus=modulus,
                                                 offset=offset)

    class Meta:
        unique_together = (("child", "shift", "period"), )
        ordering = ('period', 'rank', 'shift')

    def __repr__(self):
        return f"<ShiftPreference {self.pk}: {self.child} ranks {self.shift} as {self.rank}>"


class _ShiftOffsetMixin(object):
    """migrations need this, frk"""
    pass

    

class ShiftAssignableManager(models.Manager):

    def generate(self, period, rank_lte=1):
        ShiftAssignable.objects.filter(preference__period=period).delete()
        prefs = ShiftPreference.objects.filter(period=period)
        for pref in prefs:
            for assignable in pref.generate_assignables():
                if pref.rank <= rank_lte:
                    assignable.is_active = True
                yield assignable


class ShiftAssignable(IdentityMixin, models.Model):
    preference = models.ForeignKey(ShiftPreference, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    offset = models.IntegerField()
    offset_modulus = models.IntegerField()
    NORMAL_MODULUS = 4
    objects = ShiftAssignableManager()

    @property
    def shift(self):
        return self.preference.shift

    @property
    def period(self):
        return self.preference.period

    def occurrences(self):
        occ_pool = self.shift.occurrences_for_date_range(
            self.period.start, self.period.end)
        return (occ for index, occ in enumerate(occ_pool)
                if index % self.offset_modulus == self.offset)

    def _normalized_offsets(self):
        if self.NORMAL_MODULUS % self.modulus != 0:
            raise Exception(
                f"the value {self.modulus} as modulus of recurrence is not normalizable!")
        return {self.offset + i
                for i in range(0, self.NORMAL_MODULUS, self.NORMAL_MODULUS // modulus)}

    def is_compatible_with(self, other):
        return self._normalized_offsets().is_disjoint(
            other._normalized_offsets())

    # def __identity__(self):
        # return (self.preference.pk, self.offset, self.offset_modulus)

    def create_commitments(self):
        for shocc in self.occurrences():
            shocc.create_commitment(self.preference.child)
     

class WorktimeScheduleManager(models.Manager):

    """ each child gets as domain a set of shifts-with-offset, 
    which is generated by their shift preferences (then tweaked by scheduler)
    the solution assigns each child a shift-with-offset, 
    so that all assignments are compatible
    """

    def generate(self, period, no_worse_than=1):
        problem = Problem()
        assignables = ShiftAssignable.objects.filter(
            period=period, select_related=(['preference', 'child']),
            ordering=('kid'))
        doms = defaultdict(list)
        for assignable in assignables:
            doms[assignable.preference.child.pk].append(assignable)
        for k, dom in doms.items():
            problem.addVariable(k, dom)
        for k1, k2 in itertools.combinations(doms.keys(), 2):
            problem.addConstraint(lambda a1, a2: a1.is_compatible_with(a2),
                                  (k1, k2))
        solutions = problem.getSolutions()
        for solution in solutions:
            schedule = WorktimeSchedule.objects.create(period=period)
            for assignable in solution.values():
                schedule.assignments.add(assignable)
            yield schedule


class WorktimeSchedule(models.Model):
    date = models.DateTimeField(default=timezone.now)
    period = models.ForeignKey(Period, on_delete = models.CASCADE)
    assignments = models.ManyToManyField(ShiftAssignable)
    objects = WorktimeScheduleManager()

    def commit(self):
        for assignable in self.assignments.all():
            assignable.create_commitments()
            


