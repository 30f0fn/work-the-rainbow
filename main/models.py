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
        return set(date for event in self.overlaps(start, end)
                 for date in event.all_dates()
                   if start.date() <= date <= end.date())



class Event(models.Model):

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

    def by_weekday_and_time(self):
        """for each weekday, list all shifts in order of time"""
        shifts_dict = defaultdict(list)
        for shift in shifts:
            shifts_dict[shift.weekday].append(shift)
        return shifts_dict

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

    def weekday_str(self):
        return WEEKDAYS[self.weekday]

    class Meta:
        abstract = True
        ordering = ['weekday', 'start_time']


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
        self.start = timezone.make_aware(
            timezone.datetime.combine(date, weekly_event.start_time))
        self.end = timezone.make_aware(
            timezone.datetime.combine(date, weekly_event.end_time))

    def __repr__(self):
        # this gives identical values for weeklyevent occurrences with same weekly class and same start datetime
        return f"{self.__class__.__name__}: start={self.start}"

    class Meta:
        abstract = True



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
        first_of_next_month = today.replace(year=today.year + year_inc,
                                   month=(today.month % 12 + 1),
                                   day=1)
        return first_of_next_month
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
        super().__init__(careday, date)
        self.careday = careday
        
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
        """remove from child all assignments to caredays from start to end inclusive"""
        """since assignments are continuous, this can require creating another"""
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
        #  amalgamate with overlapping assignments
        if self.start >= self.end and self.pk:
            self.delete()
            return
        overlaps = CareDayAssignment.objects.overlaps(
            self.child, self.start, self.end, careday=self.careday)
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
        start_as_date = self.start.date() if type(self.start) is datetime.date\
            else self.start
        end_as_date = self.end.date() if type(self.end) is datetime.date\
            else self.end
        self.start = min(start_as_date, *(cda.start.date() for cda in list(overlaps)))
        self.end = max(end_as_date, *(cda.end.date() for cda in list(overlaps)))
        overlaps.delete()
        super().save(*args, **kwargs)

    def occurrences_for_date_range(self, start, end, ignore_holidays=True):
        for occ in self.careday.occurrences_for_date_range(
                start = max(self.start, start),
                end = min(self.end, end),
                ignore_holidays = ignore_holidays):
            yield occ

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.pk}>: child={self.child}, careday={self.careday}, start={self.start}, end={self.end}"

    def __str__(self):
        return f"{self.careday} for {self.child}, from {self.start} through {self.end}"

    class Meta:
        ordering = ['careday', 'start', 'end']



##########
# Shifts #
##########


class ShiftQuerySet(WeeklyEventQuerySet):

    def occurrences_for_date_range(self, start, end,
                                   ignore_holidays=False,
                                   include_commitments=False):
        wtc_dict = {}
        if include_commitments:
            commitments = WorktimeCommitment.objects.filter(
                    shift__in=self.all(),
                    start__gte=start,
                    end__lte=end)
            wtc_dict = {wtc.start: wtc for wtc in commitments}
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
    """
    use this class to create a WorktimeCommitment by passing child to an instance
    stores WorktimeCommitment to avoid DB lookup when instance is in memory
    """

    def __init__(self, shift, date, **kwargs):
        if int(shift.weekday) != (date.weekday()):
            raise ValueError(
                f"The shift {shift} has no occurrence on {date},\
                because {shift.weekday} != {date.weekday()}")
        super().__init__(shift, date)
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
        return (getattr(self, 'commitment', None)
                or WorktimeCommitment.objects.get(
                    shift=self.shift,
                    start=self.start))

    def reservation_deadline(self, days_before=1):
        """
        latest time to reserve this ShiftOccurrence
        """
        maxtime = timezone.datetime.max.time()
        day_before = self.start - datetime.timedelta(days_before)
        if not self.start.tzinfo:
            self.start = timezone.make_aware(self.start)
        deadline = day_before.replace(
            hour=maxtime.hour, minute=maxtime.minute)
        return deadline

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
 
    def __str__(self):
        return f"{self.start.strftime('%-H:%M %a, %-d %b')} ({self.shift.classroom.slug})"

    def __repr__(self):
        result = super().__repr__()+f", classroom={self.shift.classroom}"
        if self.commitment:
            result += f", commitment={self.commitment}"
        return result


class WorktimeCommitment(Event):
    """
    Assignment of Child to ShiftOccurrence (via shift, date fields).
    Do not create these directly; instead use create_commitment instance method of ShiftOccurrence.
    Note that the fields are a bit redundant, because from event superclass it has a datetimefield start while theshift field gives it a timefield start_time.
    todo: throw exception if we try to assign commitment to holiday?
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
        self.shift = self.shift or Shift.objects.get(
            classroom=self.child.classroom,
            start_time=self.start.time(),
            weekday=self.start.weekday())
        super().save(*args, **kwargs)

    def __str__(self):
        return f'commitment of {str(self.child)} to {str(self.shift_occurrence())}'

    def alternatives(self, earlier, later):
        """
        enumerate all ShiftOccurrences between earlier and later,
        whose careday is in caredayassignment of child of this commitment
        minus those ShiftOccurrences already committed, 
        but including the ShiftOccurrence of current commitment
"""
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
        commitments_by_start = {wtc.start : wtc \
                                for wtc in WorktimeCommitment.objects.filter(
                                        child__classroom=self.child.classroom,
                                        start__gte=dt_min, end__lte=dt_max)}
        for proposed_occ in sh_occs:
            if commitments_by_start.get(proposed_occ.start, self) == self:
                yield proposed_occ

    class Meta:
        unique_together = (("shift", "start"),)
        ordering = ['start']


class ShiftPreferenceManager(models.Manager):
    """Extra perspectives on ShiftPreferences"""

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

    # def for_scheduler(self, period):
        # """by weekday, time, active, child"""

    def for_child_by_period(self, child, periods):
        """bundle child's preferences (sorted by rank) for each period;
        return iterator over the bundles"""

        PrefbyP = namedtuple('PrefsByPeriod', ['period', 'preferences'])
        preferences = list(ShiftPreference.objects.filter(
            child=child, period__in=periods)
                           .select_related('shift')
                           .order_by('rank')
                           .order_by('-period'))
        for period in periods:
            pp = PrefsByPeriod(period, [[], [], []])
            while preferences and preferences[-1].period == period:
                pref = preferences.pop()
                pp.preferences[pref.rank - 1].append(pref)
            yield pp

    def by_child_for_period(self, period, children):
        """bundle preferences by child,
        return iterator over the bundles"""

        PrefsByChild = namedtuple('PrefsByChild', ['child', 'preferences'])
        preferences = list(ShiftPreference.objects.filter(
            period=period,
            child__in=children)\
                           .select_related('shift').order_by('rank').order_by('-child'))
        for child in children:
            pc = PrefsByChild(child, [[], [], []])
            while preferences and preferences[-1].child == child:
                pref = preferences.pop()
                pc.preferences[pref.rank - 1].append(pref)
            yield pc


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
        assert self.shift.classroom == self.period.classroom
        if self._modulus is None:
            self._modulus = ShiftAssignable.NORMAL_MODULUS // self.child.shifts_per_month
        worst_to_activate = ShiftAssignable.DEFAULT_ACTIVE_LEVEL
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
    """Attach a note to a submitted preference"""
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    contents = models.TextField()
    

class _ShiftOffsetMixin(object):
    """cruft needed for migrations to run, frk"""
    pass


class ShiftAssignable(IdentityMixin, object):
    """
    Possible assignment of a shift to a child,
    e.g., an assignment to Frankie of the 2nd, 4th, 6th... Wednesdays at 1pm.
    Each family fills its weekly shift every 1, 2 or 4 weeks,
    so a weekly shift can be assigned to more than one family and several ways.
    The *modulus* represents whether the assignment is every 1, 2 or 4 weeks;
    the *offset* represents position in the cycle.
    E.g., offset 1 with modulus 2 gets weeks 1,3,5,... as with Frankie above
"""
    NORMAL_MODULUS = 4    # length of the global assignment cycle (= LCM of all assignable moduli)
    DEFAULT_ACTIVE_LEVEL = 1 # default lowest preference rank to consider

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
        """deserialization helper"""
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

    def normalized_offsets(self):
        if self.NORMAL_MODULUS % self.modulus != 0:
            raise Exception(
                f"the value {self.modulus} as modulus of recurrence is not normalizable!")
        return {(self.offset + i) % self.NORMAL_MODULUS
                for i in range(0, self.NORMAL_MODULUS, self.modulus)}

    def is_compatible_with(self, other):
        return self == other\
            or self.normalized_offsets().isdisjoint(
                other.normalized_offsets())\
                or self.preference.shift != other.preference.shift

    def instantiate_commitments(self):
        for shocc in self.occurrences():
            yield shocc.instantiate_commitment(self.preference.child)

    def create_commitments(self):
        for commitment in self.instantiate_commitments():
            commitment.save()
        return commitments

    class Meta:
        ordering = ['preference', 'offset']

    def __repr__(self):
        return f"<ShiftAssignable: child={self.child}, shift={self.shift}, offset={self.offset}, modulus={self.modulus}>"        

 

class WorktimeSchedule():
    """
    Use this class to generate a worktime schedule from shift preferences submitted by each family.
    The class method generate_schedules returns an iterator over all coherent schedules satisfying a given set of preferences, sorted by optimality
    The constructor takes either a solution, or an iterable of assignments
    The commit() instance method generates the WorktimeCommitments of that schedule and saves them to the database
    """

    def __init__(self, solution=None, assignments=None):
        if solution and not assignments:
            self.assignments = list(solution.values())
        elif assignments and not solution:
            self.assignments = assignments
        else:
            raise Exception("WorktimeSchedule constructor takes either a solution or a list of assignments (but not both)")
        self.children = [assignment.child for assignment in self.assignments]
        if len(self.assignments) != len(self.children):
            raise Exception("This schedule is invalid,\
            because it gives some child more than one assignment.")
        self._score = None
        if not self.assignments:
            raise Exception("Schedule has no assignments.")
        self.period = self.assignments[0].period
        return super().__init__()

    def __eq__(self, other):
        return set(self.assignments) == set(other.assignments)

    def score(self):
        if self._score is None:
            self._score = sum(assignment.rank
                              for assignment in self.assignments)
        return self._score


    @classmethod
    def generate_solutions(cls, period, total=True):
        """
        Generate all consistent sets of ShiftAssignables, sorted by optimality
        Per above, a ShiftAssignable consists of a specification of some repeating instances of a shift, plus a child to whom they would be assigned.
        ShiftAssignables are consistent if no two children are assigned the same instance
        """
        doms = defaultdict(list) if not total\
            else {child.pk : [] for child in period.classroom.child_set.all()}
        for solution in cls._generate_solutions(period, doms=doms):
            yield solution


    @classmethod
    def _generate_solutions(cls, period, doms):
        """
        Each child gets as domain a set of ShiftAssignables, 
        which is generated by their shift preferences;
        each solution selects for each child a ShiftAssignable
        so that all assignments are compatible
        """
        problem = Problem()
        prefs = (ShiftPreference.objects.filter(period=period)
                 .select_related('shift').select_related('child'))
        for pref in prefs:
            for assignable in pref.assignables():
                if assignable.is_active:
                    doms[assignable.child.pk].append(assignable)
        for k, dom in doms.items():
            try:
                problem.addVariable(k, dom)
            except ValueError:
                return {}
        cached_compatibility = functools.lru_cache()(lambda a1, a2:
                                                     a1.is_compatible_with(a2))
        for k1, k2 in itertools.combinations(doms.keys(), 2):
            problem.addConstraint(cached_compatibility, (k1, k2))
        return problem.getSolutionIter()

    @classmethod
    def generate_schedules(cls, period, total=True):
        for solution in cls.generate_solutions(period, total=total):
            yield WorktimeSchedule(solution=solution)

    def serialize(self):
        return [assignment.serialize() for assignment in self.assignments]

    @classmethod
    def deserialize(cls, data_str):
        assignments_data = ast.literal_eval(data_str)
        assignments = [ShiftAssignable._from_data(datum) for datum in assignments_data]
        return WorktimeSchedule(assignments=assignments)


    def instantiate_commitments(self):
        """present data of schedule without saving"""
        for assignable in self.assignmments:
            for commitment in assignable.instantiate_commitments():
                yield commitment

    def commit(self):
        """save the commitments of the schedule"""
        for assignable in self.assignments:
            for commitment in assignable.create_commitments():
                yield commitment
                
    def __repr__(self):
        return f"<WorktimeSchedule: assignments = {self.assignments}>"        
