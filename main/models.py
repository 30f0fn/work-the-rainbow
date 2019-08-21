import datetime
import ast
from collections import defaultdict, namedtuple
import itertools
import functools
import json
import random
from constraint import Problem
from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.utils import timezone

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField, WEEKDAYS
from main.utilities import WeekdayIterator, next_date_with_given_weekday, dates_in_range, in_a_week, serialize_datetime, deserialize_datetime
# import main.scheduler
from people.views import ClassroomMixin


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
    """
    todo subclass this with DateBoundedEvent, as parent of Period, CareDayAssignment etc
    it should support comparison of its bounds with datetimes, 
    but also manipulating the bounds as dates
    """

    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(blank=True, null=True)

    objects = EventManager()

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

    class Meta:
        ordering = ['start']
        abstract = True



class _WeeklyEventFormatter(object):
    """various functions drawing on data from _events method 
    classes which implement that method include
    WeeklyEvent and WeeklyEventQuerySet"""

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
    """don't use for models"""

    def __hash__(self):
        if '__identity__' in dir(self):
            return hash(self.__identity__())
        else:
            return super().__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)


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
    description = models.TextField(blank=True)
    

class Period(Event):
    """todo add field 'preference_deadline' and revise rules so that child can't modify ShiftPreference for Period after deadline?
    add 'published' field so that scheduler can wait to reveal commitments"""
    DEFAULT_LENGTH = relativedelta(months=4)
    def start_default():
        today = timezone.now().date()
        year_inc = 1 if today.month==12 else 0
        next_month = today.replace(year=today.year + year_inc,
                                   month=(today.month + 1 % 12),
                                   day=1)
    start = models.DateTimeField(default=start_default)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    solicits_preferences = models.BooleanField(default=True)
    published = models.BooleanField(default=True)
    preference_deadline = models.DateTimeField(null=True,
                                               default=start_default)

    def worktime_commitments(self, child=None):
        commitments = WorktimeCommitment.objects.filter(
            child__classroom=self.classroom,
            start__range = (self.start, self.end)
        )
        if child:
            commitments.filter(child=child)
        return commitments

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
        # self.classroom=self.careday.classroom
        
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
                                          classroom=self.careday.classroom):
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
        if self.start >= self.end and self.pk:
            self.delete()
            return
        overlaps = CareDayAssignment.objects.overlaps(
            self.child, self.start, self.end, careday=self.careday)
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
        # todo below is hideous hack... need to fix handling of date-bounded events
        try:
            self.start = self.start.date()
            self.end = self.end.date()
        except AttributeError:
            pass
        new_start = min([cda.start.date() for cda in list(overlaps)] + [self.start])
        new_end = max([cda.end.date() for cda in list(overlaps)] + [self.end])
        overlaps.delete()
        self.start = new_start
        self.end = new_end
        super().save(*args, **kwargs)

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
        return f"{self.careday} for {self.child}, from {self.start} through {self.end}"

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
        # self.classroom=self.shift.classroom
        self.commitment = kwargs.pop('commitment', None)

    def __identity__(self):
        return (self.shift.classroom_pk, self.start)

    def instantiate_commitment(self, child):
        commitment = WorktimeCommitment(
            start = self.start,
            end = self.end,
            child = child,
            shift = self.shift)
        self.commitment = commitment
        return commitment

    def create_commitment(self, child):
        """commit child to this occurrence
        doesn't check whether it's covered by a careday"""
        self.instantiate_commitment(child)
        self.commitment.save()
        return self.commitment

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
        return f"{self.start.strftime('%-H:%M %a, %-d %b')} ({self.shift.classroom.slug})"

    def __repr__(self):
        result = super().__repr__()+f", classroom={self.shift.classroom}"
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
            shocc.commitment = WorktimeCommitment.objects.get(
                pk=int(repr_dict.get('commitment')))
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
        """just super().save when instance is initialized through ShiftOccurrence instance method"""
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
        # print(f"commitments_by_start={commitments_by_start}")
        for proposed_occ in sh_occs:
            if commitments_by_start.get(proposed_occ.start, self) == self:
                # print(f"yielded proposed_occ {proposed_occ}")
                # print(commitments_by_start.get(proposed_occ.start))
                # print(proposed_occ.start)
                yield proposed_occ
            # else:
                # print(f"skipped proposed_occ {proposed_occ}")

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

    def for_scheduler(self, period):
        """by weekday, time, active, child"""

    def for_child_by_period(self, child, periods):
        PbyP = namedtuple('PbyP', ['period', 'preferences'])
        # periods = self.periods_soliciting_preferences()
        retval = []
        preferences = list(ShiftPreference.objects.filter(
            child=child,
            period__in=periods)\
                           .select_related('shift').order_by('rank').order_by('-period'))
        for period in periods:
            print(period)
            pp = PbyP(period, [[], [], []])
            while preferences and preferences[-1].period == period:
                pref = preferences.pop()
                pp.preferences[(pref.rank - 1)].append(pref)
            retval.append(pp)
        return retval

    def by_child_for_period(self, period, children):
        PbyC = namedtuple('PbyP', ['child', 'preferences'])
        # periods = self.periods_soliciting_preferences()
        retval = []
        preferences = list(ShiftPreference.objects.filter(
            period=period,
            child__in=children)\
                           .select_related('shift').order_by('rank').order_by('-child'))
        for child in children:
            # print(child)
            pc = PbyC(child, [[], [], []])
            while preferences and preferences[-1].child == child:
                pref = preferences.pop()
                pc.preferences[(pref.rank - 1)].append(pref)
            retval.append(pc)
        return retval





class ShiftPreference(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    rank_choices = ((1, 'best'), (2, 'pretty good'), (3, 'acceptable'))
    rank = models.IntegerField(choices=rank_choices, default=1,
                               null=True, blank=True)
    objects = ShiftPreferenceManager()
    _modulus = models.IntegerField(null=True)
    _active_offsets = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if self._modulus is None:
            self._modulus = ShiftAssignable.NORMAL_MODULUS // self.child.shifts_per_month
        worst_to_activate = ShiftAssignable.DEFAULT_ACTIVE_LEVEL
        # print(self.rank.__class__, worst_to_activate.__class__)
        if self._active_offsets is None:
            self._active_offsets = sum(1 << o for o in range(self.modulus)
                                       if self.rank <= worst_to_activate)
        super().save(*args, **kwargs)

    @property
    def modulus(self):
        if self._modulus is None:
            self._modulus = ShiftAssignable.NORMAL_MODULUS // self.child.shifts_per_month
            self.save()
        return self._modulus

    def offset_is_active(self, offset):
        return (self._active_offsets >> offset) & 1

    def activate_offset(self, offset):
        if not 0 <= offset < self.modulus:
            raise Exception("offset out of bounds!")
        else:
            self._active_offsets |= (1 << offset)

    def deactivate_offset(self, offset):
        if not 0 <= offset < self.modulus:
            raise Exception("offset out of bounds!")
        else:
            self._active_offsets &= ~(1 << offset)

    def activate_all_offsets(self):
        for o in range(self.modulus):
            self.activate_offset(o)
        
    def deactivate_all_offsets(self):
        self._active_offsets = 0

    def assignable_from_offset(self, offset):
        if offset >= self.modulus:
            raise Exception("offset must be smaller than modulus!")
        return ShiftAssignable(preference=self,
                               offset=offset)

    def assignables(self):
        for offset in range(self.modulus):
            yield self.assignable_from_offset(offset)

    def assignables_by_status(self):
        by_status = namedtuple('ByStatus', 'active inactive')([], [])
        for offset in range(self.modulus):
            assignable = self.assignable_from_offset(offset)
            if self.offset_is_active(offset):
                by_status.active.append(assignable)
            else:
                by_status.inactive.append(assignable)
        return by_status

    class Meta:
        unique_together = (("child", "shift", "period"), )
        ordering = ('period', 'rank', 'shift')

    def __repr__(self):
        return f"<ShiftPreference {self.pk}: {self.child} ranks {self.shift} as {self.rank}>"


class ShiftPreferenceNoteForPeriod(models.Model):
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    contents = models.TextField()
    

class _ShiftOffsetMixin(object):
    """migrations need this, frk"""
    pass


class ShiftAssignable(IdentityMixin, object):
    NORMAL_MODULUS = 4
    DEFAULT_ACTIVE_LEVEL = 1

    def __init__(self, preference, offset):
        self.preference = preference
        self.offset = offset
        self.child = preference.child
        self.shift = preference.shift
        self.rank = preference.rank
        self.modulus = preference.modulus
        self._is_active = preference.offset_is_active(offset)

    @property
    def is_active(self):
        return self._is_active

    def __identity__(self):
        return (self.preference.pk, self.offset)

    def serialize(self):
        return (self.preference.pk,
                self.child.pk,
                self.shift.pk,
                self.offset)

    @classmethod
    def _from_data(cls, data):
        preference_pk, child_pk, shift_pk, offset = data
        preference=ShiftPreference.objects.get(pk=preference_pk)
        assignable = cls(preference=preference, offset=offset)
        if (assignable.child.pk, assignable.shift.pk) != (child_pk, shift_pk):
            raise Exception("The scanned assignment is invalid,\
            because the preference {preference} does not match the other data.")
        return assignable

    @classmethod
    def deserialize(cls, data_str):
        data = ast.literal_eval(data_str)
        return cls._from_data(data)

    @property
    def period(self):
        return self.preference.period

    def activate(self):
        self.preference.activate_offset(self.offset)

    def deactivate(self):
        self.preference.deactivate_offset(self.offset)

    def occurrences(self):
        occ_pool = self.shift.occurrences_for_date_range(
            self.period.start, self.period.end)
        return (occ for index, occ in enumerate(occ_pool)
                if index % self.modulus == self.offset)

    def _normalized_offsets(self):
        if self.NORMAL_MODULUS % self.modulus != 0:
            raise Exception(
                f"the value {self.modulus} as modulus of recurrence is not normalizable!")
        return {(self.offset + i) % self.NORMAL_MODULUS
                for i in range(0, self.NORMAL_MODULUS, self.modulus)}

    def is_compatible_with(self, other):
        return self == other\
            or self._normalized_offsets().isdisjoint(
                other._normalized_offsets())\
                or self.preference.shift != other.preference.shift

    def instantiate_commitments(self):
        return [shocc.instantiate_commitment(self.preference.child)
                for shocc in self.occurrences()]

    def create_commitments(self):
        commitments = self.instantiate_commitments()
        for commitment in commitments:
            commitment.save()
        return commitments

    class Meta:
        ordering = ['preference', 'offset']

    def __repr__(self):
        return f"<ShiftAssignable: child={self.child}, shift={self.shift}, offset={self.offset}, modulus={self.modulus}>"        
     

 

class WorktimeSchedule(object):
    def __init__(self, solution=None, assignments=None):
        if solution and not assignments:
            self.assignments = list(solution.values())
        elif assignments and not solution:
            self.assignments = assignments
        else:
            raise Exception("WorktimeSchedule constructor takes either a solution or a list of assignments (but not both)")
        self.children = [assignment.child for assignment in self.assignments]
        if len(self.assignments) != len(self.children):
            raise Exception("this schedule is invalid,\
            because it gives some child more than one assignment!")
        self._score = None
        if not self.assignments:
            raise Exception("Schedule requires at least one assignment")
        self.period = self.assignments[0].period
        return super().__init__()

    # def __identity__(self):
        # return self.assignments

    def __eq__(self, other):
        return set(self.assignments) == set(other.assignments)

    def score(self):
        if self._score is None:
            self._score = sum(assignment.rank
                              for assignment in self.assignments)
        return self._score

    """ each child gets as domain a set of shifts-with-offset, 
    which is generated by their shift preferences (then tweaked by scheduler)
    the solution assigns each child a shift-with-offset, 
    so that all assignments are "compatible"
    """
    @classmethod
    def _generate_solutions(cls, period, doms):
        problem = Problem()
        prefs = ShiftPreference.objects.filter(period=period)\
                                       .select_related('shift').select_related('child')
        for pref in prefs:
            for assignable in pref.assignables():
                # print(assignable)
                if assignable.is_active:
                    # print("is active!")
                    doms[assignable.child.pk].append(assignable)
        for k, dom in doms.items():
            try:
                # print(f"added dom {dom} for kid with pk {k}")
                problem.addVariable(k, dom)
            except ValueError:
                return {}
        cached_compatibility = functools.lru_cache()(lambda a1, a2:
                                                     a1.is_compatible_with(a2))
        for k1, k2 in itertools.combinations(doms.keys(), 2):
            problem.addConstraint(cached_compatibility, (k1, k2))
        return problem.getSolutionIter()

    @classmethod
    def generate_solutions(cls, period, total=True):
        doms = defaultdict(list) if not total\
            else {child.pk : [] for child in period.classroom.child_set.all()}
        for solution in cls._generate_solutions(period, doms=doms):
            yield solution

    @classmethod
    def generate_schedules(cls, period, total=True):
        for solution in cls.generate_solutions(period, total=total):
            yield WorktimeSchedule(solution=solution)

    """Schedule object maps each child to an assignable (preference+offset)"""
    """commit maps each child to shift+offset+offset_modulus"""
    """soundness means that a shiftpreference of that child exists for that shift"""

    def serialize(self):
        return [assignment.serialize() for assignment in self.assignments]

    @classmethod
    def deserialize(cls, data_str):
        assignments_data = ast.literal_eval(data_str)
        assignments = [ShiftAssignable._from_data(datum) for datum in assignments_data]
        return WorktimeSchedule(assignments=assignments)


    def instantiate_commitments(self):
        return [commitment for assignable in self.assignmments
                for commitment in assignable.instantiate_commitments()]

    def commit(self):
        # commitments_already = WorktimeCommitment.objects.filter(
            # child__in=self.children,
            # start__range=(self.period.start, self.period.end)).exists()
        # if commitments_already:
            # raise Exception("commitments already exist for the given period!")
        return [commitment for assignable in self.assignments
                for commitment in assignable.create_commitments()]
            
    def __repr__(self):
        return f"<WorktimeSchedule: assignments = {self.assignments}>"        
