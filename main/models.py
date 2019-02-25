import datetime
from collections import defaultdict

from django.db import models
from django.utils.timezone import make_aware

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField, WEEKDAYS
from main.utilities import WeekdayIterator, next_date_with_given_weekday, add_delta_to_time, dates_in_range

from people.views import ClassroomMixin

# what if family has two kids in one classroom?
# one (end-user) solution is to apportion all worktime obligations to one of them

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

class TimeSpan(models.Model):
    # name = models.CharField(max_length=32)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['start_time']
        abstract = True



class EventManager(models.Manager):
    
    def for_date_range(self, start, end):
        events = super().get_queryset().filter(start_date__lte=end,
                                      end_date__gte=start)
        return events
 
    def by_date(self, start, end):
        events = self.for_date_range(start, end)
        dates = dates_in_range(start, end)
        results = defaultdict(list)
        for event in events:
            if event.start_date <= date <= event.end_date:
                results[event.date].append(event)
        return results

    def by_date_and_time(self, start, end):
        events = self.by_date(start, end)
        results = defaultdict(dict)
        for event in events:
            results[event.start_date][event.start_time] = event
        return results


# todo combine start_date and start_time; end_date and end_time

class Event(TimeSpan):
    start = models.DateTimeField(default=datetime.datetime.now())
    end = models.DateField(default=datetime.datetime.now()+
                           datetime.timedelta(days=1))

    # start_date = models.DateField(blank=True, null=True)
    # end_date = models.DateField(blank=True, null=True)
    # start_time = models.TimeField(default=datetime.time())
    # end_time = models.TimeField(default=datetime.time(23,59))

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


class WeeklyEventManager(models.Manager):

    def by_weekday_and_time(self):
        events = {}
        for event in super().get_queryset().all():
            events.setdefault(event.weekday, {}).setdefault(
                event.start_time, event)
        return events

    def instances_by_date_and_time(self, start, end):
        results = defaultdict(lambda: defaultdict())
        for weekly_event in self.get_queryset().all():
            for instance in weekly_event.instances_from_date_range(start, end):
                results[instance.date][instance.start_time] = instance
        return results


class WeeklyEventInstance(object):

    def __init__(self, **kwargs):
        self.start = kwargs.get('start')
        self.end = kwargs.get('end')

    def __str__(self):
        return f"weekly event instance : {self.start}"

    def init_from_weekly(self, weekly, date):
        assert int(weekly.weekday) == date.weekday()
        start = datetime.datetime.combine(date, weekly.start_time)
        end = datetime.datetime.combine(date, weekly.end_time)
        return self.__class__(start=start, end=end)

    class Meta:
        abstract = True


class WeeklyEventCancellation(Event):
    pass
    
class WeeklyEventAddition(Event):
    pass

#  assume an addition is a one-day event
#  cancellation can be multiday
class WeeklyEvent(TimeSpan):

    weekday = WeekdayField()
    objects = WeeklyEventManager()

    @property
    def instantiating_class:
        return globals()[self.__class__.__name__+'Instance']

    @property
    def cancellations:
        return globals()[self.__class__.__name__+'Cancellation']

    # the point of addition is mainly to support modification (cancel + add)
    # is that a good idea?  seems weird, because e.g., a "tuesday" event instance then might  not be not be on a tuesday
    # maybe exceptions should be handled, along with generated instances, by the manager
    # additions should inherit from the instance class

    @property
    def additions:
        return globals()[self.__class__.__name__+'Addition']

    def instances_from_date_range(self, start, end):
        cancellations = self.cancellations.filter(start__lte=end,
                                          end__gte=start)
        additions = self.additions.filter(start__lte=end,
                                          end__gte=start)
        date = next_datetime_with_given_weekday(int(self.weekday), start)
        while date <= end:
            if additions and additions[-1].start <= date:
                yield additions.pop()
            while cancellations and cancellations[-1].end < date:
                cancellations.pop()
            if date < cancellations[-1].start:
                yield self.instantiating_class.init_from_weekly(
                    weekly=self, date=date)
            date += datetime.timedelta(days=7)

    class Meta:
        abstract = True
        ordering = ['weekday', 'start_time']


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

    @property
    def end_date(self):
        # do this with query
        return self.start_date + self.duration

    def save(self, *args, **kwargs):
        self.end = self.start + self.duration
        super().save(*args, **kwargs)

    def __str__(self):
        return f"<Period {self.pk}: {self.start.date()} - {self.end.date()}>"





class CareDayInstance(WeeklyEventInstance):
    pass


class CareDay(WeeklyEvent):
    extended_endtime = models.TimeField()

    @property
    def shifts(self):
        return Shift.objects.filter(weekday=self.weekday, 
                                    start_time__gte=self.start_time,
                                    end_time__lte=self.end_time)

    def __repr__(self):
        return f"<CareDay {self.pk}: weekday={self.weekday}, start_time={self.start_time}, end_time={self.end_time}>"
    

class CareDayAssignmentInstance(WeeklyEventInstance):
    pass


# normalize between extended and end_time?
class CareDayAssignment(WeeklyEvent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE) 
    extended = models.BooleanField(default=False)
    careday = models.ForeignKey(CareDay, on_delete=models.CASCADE)
    
    @property
    def start_time(self):
        return self.careday.start_time

    @property
    def end_time(self):
        if self.extended:
            return self.careday.extended_endtime
        else:
            return self.careday.end_time

    @property
    def weekday(self):
        return self.careday.weekday
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.pk}>: child={self.child}, weekday={self.weekday}, start_time={self.start_time}, end_time={self.end_time}"


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

class ShiftManager(WeeklyEventManager):
    def instances_by_date_and_time(self, start, end, include_commitments = False):
        results = super().instances_by_date_and_time()
        # commitments


class Shift(WeeklyEvent):
    # add foreignkey to classroom
    weekday = WeekdayField()
    objects = ShiftManager()

    @property
    def children(self):
        return Child.objects.filter(caredaycontract__careday__shifts__contains=self)

    @property
    def care_day(self):
        return CareDay.objects.get(weekday=self.weekday,
                                   start_time__lte=self.start_time,
                                   end_time__gte=self.end_time)

    def __repr__(self):
        return f"<Shift {self.pk}: weekday={self.weekday}, time={self.start_time}>"

    def __str__(self):
        return f"{WEEKDAYS[self.weekday]} {self.start_time}"


class ShiftInstance(object):
    # include classroom field? 

    # todo inherit then override
    def __init__(self, **kwargs):
        super().__init__()
        # todo bad that the below is hardcoded
        self.end = self.end or self.start + datetime.timedelta(hours=2))
        self.commitment = kwargs.get('commitment')

    # dont inherit
    def create_commitment(self, family):
        return WorktimeCommitment.objects.create(
            start = self.start,
            date = self.date,
            family = family)

    def __str__(self):
        return f"{self.start} shift"


class WorktimeCommitment(Event):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    completed = models.BooleanField


class ShiftPreference(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    status_choices = ((0, 'incomplete'), (1, 'complete'), (2, 'excused'))
    status = models.IntegerField(choices=status_choices, default=0)
    def __repr__(self):
        return f"<ShiftPreference {self.pk}: {self.family} ranks {self.shift} as {self.rank}>"


# could be called shiftassignment
class ShiftAssignment(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    def __repr__(self):
        return f"<WorktimeAssignment {self.pk}: {self.family} assigned {self.shift} in period {self.period}>"



# class ClassroomWorktimeMixin(object):
 
#     def shifts_dict(self, date, classroom=None):
#         classroom = classroom or self.classroom
#         return {shift_instance:
#                 shift_instance.commitment
#                 for shift_instance in ShiftInstance.objects.filter(date=date)}

#     def days_dict(self, start_date, num_days, classroom=None):
#         classroom = classroom or self.classroom
#         return {date: self.shifts_dict(date, classroom=classroom)
#                 for date in [start_date + datetime.timedelta(days=n)
#                              for n in range(num_days)]}

#     def weeks_list(self, start_date, num_weeks, classroom=None):
#         classroom = classroom or self.classroom
#         return [self.days_dict(date, 5, classroom=classroom)
#                 for date in [start_date + n * datetime.timedelta(days=7)
#                              for n in range(num_weeks)]]



