import datetime
import ast
from collections import defaultdict
from itertools import chain
import json

from django.db import models
from django.utils import timezone



from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField, WEEKDAYS
from main.utilities import WeekdayIterator, next_date_with_given_weekday, add_delta_to_time, dates_in_range, in_a_week, serialize_datetime, deserialize_datetime
from people.views import ClassroomMixin

# what if family has two kids in one classroom?
# one (end-user) solution is to apportion all worktime obligations to one of them

# todo rename CareDay to CareSession

# todo standardize __repr__ 

# todo subclass CareDayAssignment with ContractedCareDayAssignment, for preferences

# todo check for timezone awareness... timezone.datetime.combine seems to return non-aware datetimes (?)

"""
for generic __str__ method:
str_attrs_list = ['attr1', 'attr2']
str_attrs = ",".join([f"{attr}={getattr(self, attr)}" for attr in self.display_attrs])
return f"<{self.__class__.__name__} {self.pk}: " + str_attrs + ">"
"""

# todo
# class Agenda(object):
    # def __init__(self, *class_requests):
    
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
        return super().get_queryset().filter(start__lte=end, end__gte=start)
    
    def by_date(self, start, end, restriction=None):
        events = super().get_queryset().filter(start__lte=end,
                             end__gte=start)
        dates = dates_in_range(start, end)
        results = defaultdict(list)
        for event in events:
            # if event.start.date() <= date <= event.end.date():
            results[event.start.date()].append(event)
        return results

    def dates_for_range(self, start, end, restriction=None):
        events = self.by_date(start, end, restriction=restriction)
        return [date for date in events if events[date]]
        

    def by_date_and_time(self, start, end, restriction=None):
        by_date = self.by_date(start, end, restriction=restriction)
        results = defaultdict(dict)
        for date in by_date:
            for event in by_date[date]:
                results[date][event.start.time()] = event
        return results


# todo combine start_date and start_time; end_date and end_time

class Event(models.Model):
    start = models.DateTimeField(default=timezone.now)
    # todo below default is dumb because what if start is future?
    end = models.DateTimeField(default=timezone.now)


    @property
    def date(self):
        if self.end.date() == self.start.date():
            return self.start.date()

    def save(self, *args, **kwargs):
        self.end = self.end or self.start.replace(hours=23, minutes=59)
        super().save(*args, **kwargs)

    objects = EventManager()

    class Meta:
        ordering = ['start', 'end']
        abstract = True


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


class WeeklyEventManager(EventManager):

    # enumerate all occurrences in range, for all weekly events
    # todo support filtering
    def occurrences_for_date_range(self, start, end, ignore_holidays=False):
        occ_nest = (occ.occurrences_for_date_range(start, end,
                                                   ignore_holidays=True)
                    for occ in super().get_queryset().all())
        occurrences = list(chain.from_iterable(occ_nest))
        occurrences.sort(key=lambda x: x.start)
        exdates = ([] if ignore_holidays
                   else Holiday.objects.dates_for_range(start, end))
        for occ in occurrences:
            if occ not in exdates:
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
    start_time = models.TimeField() # todo for some reason this might not be timezone-aware?
    end_time = models.TimeField()
    weekday = WeekdayField()

    objects = WeeklyEventManager()

    def occurrence_class(self):
        return globals()[self.__class__.__name__+'Occurrence']

    def initialize_occurrence(self, date):
        assert int(self.weekday) == date.weekday()
        return self.occurrence_class()(self, date)

    def occurrences_for_date_range(self, start, end, ignore_holidays=False):
        exclusions = ([] if ignore_holidays 
                      else reversed(Holiday.objects.dates_for_range(start, end)))
        dt = timezone.datetime.combine(
            next_date_with_given_weekday(self.weekday, start),
            self.start_time)
        if not end.tzinfo:
            end = timezone.make_aware(end)
        dt = timezone.make_aware(dt)

        while dt <= end:
            if dt.date() not in exclusions:
                yield self.initialize_occurrence(dt)
            dt += datetime.timedelta(days=7)

    class Meta:
        abstract = True
        ordering = ['weekday', 'start_time']





"""
todo - calendar refactoring plan
have weekly events, namely caredays (weekday * (normal, extended)), and shifts (weekday * (morning, afternoon, latestay))
for each child, have CaredaySchedule object which points to child and generates all caredays for that child; this includes delete and add methods for exceptions
for each classroom, have ShiftSchedule object which points to classroom and generates all shifts for that classroom; this includes delete and add methods for exceptions.  for worktime assignment construction, want different object for each weekly shift
"""


class CareDayOccurrence(WeeklyEventOccurrence):

    def __init__(self, careday, date, **kwargs):
        # shift = kwargs.pop('shift')
        # date = kwargs.pop('date')
        super().__init__(careday, date)
        self.careday = careday
        self.classroom=self.careday.classroom


    def children(self):
        return Child.objects.filter(caredayassignment__end__gte=self.start,
                                    caredayassignment__start__lte=self.end,
                                    caredayassignment__careday=self.careday,
                                    classroom=self.careday.classroom)
    
    def shift_occurrences(self):
        for shift in Shift.objects.filter(weekday=self.careday.weekday,
                                          start_time__lte=self.careday.start_time,
                                          end_time__gte=self.careday.start_time,
                                          classroom=self.classroom):
            yield ShiftOccurrence(shift=shift, date=self.start.date())


# HAVE weekdays * (regular/extended) = ten of these
# maybe do disjoint "regular" and "extension"  rather than "regular" and "extended"
class CareDay(WeeklyEvent):
    classroom=models.ForeignKey(Classroom, on_delete=models.CASCADE)

    @property
    def shifts(self):
        return Shift.objects.filter(weekday=self.weekday, 
                                    start_time__gte=self.start_time,
                                    end_time__lte=self.end_time,
                                    classroom=self.classroom)

    def __repr__(self):
        return f"<CareDay {self.pk}: weekday={self.weekday}, start_time={self.start_time}, end_time={self.end_time}>"

    def __str__(self):
        return f"{WEEKDAYS[self.weekday]}, {self.start_time} - {self.end_time}"



class ShiftManager(WeeklyEventManager):

    # todo how does this differ from the method it overrides?
    def occurrences_for_date_range(self, start, end,
                                   include_commitments=False,
                                   classrooms=[],
                                   child=None):
        occ_nest = (occ.occurrences_for_date_range(start, end, ignore_holidays=True)
                    for occ in self.all().select_related('classroom'))
        occurrences = list(chain.from_iterable(occ_nest))
        occurrences.sort(key=lambda x: x.start)
        exdates = Holiday.objects.dates_for_range(start, end)
        for occ in occurrences:
            if occ not in exdates:
                yield occ

    def occurrences_by_date_and_time(self, start, end,
                                     include_commitments=False,
                                     classrooms=[]):
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


class ClassroomShiftSchedule(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete = models.CASCADE)


class Holiday(Event):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        end = '-'.append(self.end) if self.end.date() != self.start.date() else ''
        return f"{self.name} ({self.start.date()}{end})"


class Happening(Event):
    name = models.CharField(max_length=50)
    description = models.TextField()
    

class Period(Event):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    duration = models.DurationField(default=datetime.timedelta(days=7*4*4))

    def __str__(self):
        return f"<Period {self.pk}: {self.start} - {self.end}>"




class CareDayAssignmentManager(WeeklyEventManager):

    def create_careday_assignments(child, caredays, start, end):
        for careday in caredays:
            CareDayAssignment.objects.create(
                child=child, careday=careday, start=start, end=end)

    def overlaps(self, child, start, end, careday=None):
        o = super().overlaps(start, end).filter(child=child).select_related('careday')
        if careday:
            o = o.filter(careday=careday)
        return o

    def add_child_to_careday_for_range(self, careday, child, start, end):
        for assignment in self.overlaps(
                child, start, end,
                careday=careday):
            assignment.extend_to(start, end)

    def remove_child_from_careday_for_range(self, careday, child, start, end):
        for assignment in self.overlaps(
                child, start, end,
                careday=careday):
            assignment.retract_from(start, end)

    def careday_occurrences_for_child(self, child, start, end):
        # for each weekday, list of all caredayassignments which overlap the daterange; then for each each date, yield caredayoccurrence if possible, then pop caredayassignments with enddate <= the date
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
        self.start = min(start, self.start)
        self.end = max(end, self.end)
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

    # def __str__(self):
        # return f"<{self.__class__.__name__} {self.pk}>: child={self.child}, careday={self.careday}, start={self.start}, end={self.end}"



class ExtraCareDay(Event):

    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    extended = models.BooleanField(default=False)





# class CancelledCareDay(models.Model):
    # child = models.ForeignKey(Child, on_delete=models.CASCADE)
    # date = models.DateField()


# todo how about adding/deleting late stay?

"""
given caredaycontracts of child, access its possible shifts
conversely, access children from shift
"""


###################################
# worktime shifts  and assignments #
###################################


class ShiftOccurrence(WeeklyEventOccurrence):
    # include classroom field? 

    # todo inherit then override
    def __init__(self, shift, date, **kwargs):
        # shift = kwargs.pop('shift')
        # date = kwargs.pop('date')
        super().__init__(shift, date)
        self.classroom=self.shift.classroom
        self.commitment = kwargs.pop('commitment', None)

    # @classmethod
    # def deserialize()

    # dont inherit
    def create_commitment(self, child):
        return WorktimeCommitment.objects.create(
            start = self.start,
            # date = self.date,
            child = child)

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
        return f"{self.start} shift in {self.classroom.slug}"

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
        return ShiftOccurrence(Shift.objects.get(pk = repr_dict['shift']),
                               deserialize_datetime(repr_dict['start']))
        

# todo this should just have shift and fields?
# then, override start and end property methods?  seems ugly
class WorktimeCommitment(Event):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    completed = models.NullBooleanField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)

    def shift_occurrence(self):
        return ShiftOccurrence(shift=self.shift,
                               date=self.start.date(),
                               commitment=self)

    def save(self, *args, **kwargs):
        self.shift = Shift.objects.get(classroom=self.child.classroom,
                                       start_time=self.start.time(),
                                       weekday=self.start.weekday())
        super().save(*args, **kwargs)

    # @property
    # def start(self):
    #     return timezone.make_aware(
    #         timezone.datetime.combine(self.date, self.shift.start_time))

    # @property
    # def end(self):
    #     return timezone.make_aware(
    #         timezone.datetime.combine(self.date, self.shift.end_time))


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



class ShiftPreference(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    rank_choices = ((1, 'best'), (2, 'pretty good'), (3, 'acceptable'))
    rank = models.IntegerField(choices=rank_choices, default=3)
    def __repr__(self):
        return f"<ShiftPreference {self.pk}: {self.child} ranks {self.shift} as {self.rank}>"


# could be called shiftassignment
class ShiftAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    def __repr__(self):
        return f"<WorktimeAssignment {self.pk}: {self.child} assigned {self.shift} in period {self.period}>"

class ShiftInstance(object):
    pass


