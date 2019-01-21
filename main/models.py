import datetime

from django.db import models
from django.utils.timezone import make_aware

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField
from main.utilities import WeekdayIterator, next_date_with_given_weekday

# what if family has two kids in one classroom?
# one (end-user) solution is to apportion all worktime obligations to one of them

"""
for generic __str__ method:
str_attrs_list = ['attr1', 'attr2']
str_attrs = ",".join([f"{attr}={getattr(self, attr)}" for attr in self.display_attrs])
return f"<{self.__class__.__name__} {self.pk}: " + str_attrs + ">"
"""


class Holiday(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    

class Happening(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    start_date = models.DateField()
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    

class Period(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    start_date = models.DateField()
    duration = models.DurationField(default=datetime.timedelta(days=7*4*4))

    @property
    def end_date(self):
        return self.start_date + self.duration

    def __str__(self):
        return f"<Period {self.pk}: {self.start_date} - {self.end_date}>"


class TimeSpan(models.Model):
    name = models.CharField(max_length=32)
    start_time = models.TimeField()
    end_time = models.TimeField()
    # duration = models.DurationField(default=datetime.timedelta(days=0))

    # @property
    # def end_time(self):
        # (datetime.datetime.combine(datetime.datetime(1, 1, 1),
                                  # self.start_time) + self.duration).time()

    def __str__(self):
        return f"<Timespan {self.pk}: {self.name}>"

    class Meta:
        ordering = ['start_time']
        abstract = True


# plausibly this has only one instance
class CareDayTimeSpan(TimeSpan):
    extended_endtime = models.TimeField()
    
    def __str__(self):
        return f"<CareDayTimeSpan {self.pk}: {self.name}>"


class CareDay(models.Model):
    weekday = WeekdayField()
    time_span = models.ForeignKey(CareDayTimeSpan, on_delete=models.CASCADE)

    @property
    def shifts(self):
        return Shift.objects.filter(weekday=self.weekday, 
                                    time_span__start_time__gte=self.time_span.start_time,
                                    time_span__end_time__lte=self.time_span.end_time)

    """
    the start_time, end_time accessors should be abstracted (ditto for Shift class)
    """
    @property
    def start_time(self):
        return self.time_span.start_time

    @property
    def end_time(self):
        return self.time_span.end_time

    def __str__(self):
        return f"<CareDay {self.pk}: weekday={self.weekday}, time_span={self.time_span}>"


"""
this and and also shiftinstance should be virtual (generated by shift, careday)
"""
class CareDayInstance(models.Model):
    care_day = models.ForeignKey(CareDay, null=True, on_delete=models.CASCADE)
    date = models.DateField()

    def shift_instances(self):
        return ShiftInstance.objects.filter(date=self.date)
    

class CareDayAssignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    extended = models.BooleanField(default=False)
    careday = models.ForeignKey(CareDay, on_delete=models.CASCADE)
    def __str__(self):
        return f"<{self.__class__.__name__} {self.pk}>: child={self.child}, extended={self.extended}, careday={self.careday}"


"""
given caredaycontracts of child, access its possible shifts
conversely, access children from shift
"""


###################################
# worktime shifts  and assignments #
###################################


class ShiftTimeSpan(TimeSpan):
    def __str__(self):
        return f"<ShiftTimeSpan {self.pk}: {self.name}>"


class Shift(models.Model):
    # add foreignkey to classroom
    weekday = WeekdayField()
    time_span = models.ForeignKey(ShiftTimeSpan, on_delete=models.CASCADE)

    @property
    def start_time(self):
        return self.time_span.start_time

    @property
    def end_time(self):
        return self.time_span.end_time

    def next_instance_from(self, from_date):
        # offset = (int(self.weekday) - period.start_date.weekday()) % 7        
        instance_date = next_date_with_given_weekday(int(self.weekday), from_date)
        return datetime.datetime.combine(instance_date, self.time_span.start_time)

    def create_instances_in_period(self, period):
        wi = WeekdayIterator(self.next_instance_from(period.start_date))
        for k in range(period.duration.days // 7):
            if not Holiday.objects.filter(date=wi[k]):
                ShiftInstance.objects.get_or_create(date=wi[k], shift=self)

    def instances_in_period(self, period):
        return ShiftInstance.objects.filter(shift=self,
                                            date__gte=period.start_date,
                                            date__lte=period.start_date+period.duration)
    def __str__(self):
        return f"<Shift {self.pk}: weekday={self.weekday}, time={self.time_span}>"

    @property
    def children(self):
        return Child.objects.filter(caredaycontract__careday__shifts__contains=self)

    @property
    def care_day(self):
        return CareDay.objects.get(weekday=self.weekday,
                                   time_span__start_time__lte=self.time_span.start_time,
                                   time_span__end_time__gte=self.time_span.end_time)

    class Meta:
        ordering = ['weekday', 'time_span']


class ShiftInstance(models.Model):
    shift = models.ForeignKey(Shift, null=True, on_delete=models.CASCADE)
    date = models.DateField()

    @property
    def start_time(self):
        return self.shift.start_time

    @property
    def end_time(self):
        return self.shift.end_time

    @property
    def commitment(self):
        return self.worktimecommitment_set.first()

    class Meta:
        ordering = ['date', 'shift']



class ShiftPreference(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    rank = NumChoiceField()
    def __str__(self):
        return f"<ShiftPreference {self.pk}: {self.family} ranks {self.shift} as {self.rank}>"


# could be called shiftassignment
class WorktimeAssignment(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    def __str__(self):
        return f"<WorktimeAssignment {self.pk}: {self.family} assigned {self.shift} in period {self.period}>"


class WorktimeCommitment(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift_instance = models.ForeignKey(ShiftInstance, on_delete=models.CASCADE)

    @property
    def date(self):
        return self.shift_instance.date

    @property
    def start_time(self):
        return self.shift_instance.start_time

    @property
    def end_time(self):
        return self.shift_instance.end_time

    def __str__(self):
        return f"<WorktimeCommitment {self.pk}: {self.family} has {self.shift_instance}>"

    class Meta:
        ordering = ['shift_instance']


