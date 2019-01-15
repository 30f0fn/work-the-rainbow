import datetime

from django.db import models
from django.utils.timezone import make_aware

from people.models import Child, Classroom
from main.model_fields import WeekdayField, NumChoiceField
from main.utilities import WeekdayIterator, next_date_with_given_weekday

# what if family has two kids in one classroom?
# one (end-user) solution is to apportion all worktime obligations to one of them


class Holiday(models.Model):
    name = models.CharField(max_length=50)
    start = models.DateField()
    end = models.DateField(null=True)
    

class Period(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    start_date = models.DateField()
    duration = models.DurationField(default=datetime.timedelta(days=7*4*4))
    # def get_weeks(self):
        # cal = calendar.Calendar()
        # year_weeks = cal.yeardays2calendar(start_date)
    def __str__(self):
        return f"<Period {self.pk}: {self.start_date} - {self.start_date + self.duration}>"


class DatelessTimedEvent(models.Model):
    name = models.CharField(max_length=32)
    start_time = models.TimeField()
    duration = models.DurationField(default=datetime.timedelta(hours=2))
    def __str__(self):
        return f"<ShiftTime {self.pk}: {self.name}>"
    class Meta:
        ordering = ['start_time']
    


class ShiftTime(DatelessTimedEvent):
    name = models.CharField(max_length=32)
    start_time = models.TimeField()
    duration = models.DurationField(default=datetime.timedelta(hours=2))
    def __str__(self):
        return f"<ShiftTime {self.pk}: {self.name}>"
    class Meta:
        ordering = ['start_time']


    



class Shift(models.Model):
    # add foreignkey to classroom
    weekday = WeekdayField()
    shift_time = models.ForeignKey(ShiftTime, on_delete=models.CASCADE)
    @property
    def start_time(self):
        return self.shift_time.start_time

    def next_instance_from(self, from_date):
        # offset = (int(self.weekday) - period.start_date.weekday()) % 7        
        instance_date = next_date_with_given_weekday(int(self.weekday), from_date)
        return datetime.datetime.combine(instance_date, self.shift_time.start_time)

    def create_instances_in_period(self, period):
        wi = WeekdayIterator(self.next_instance_from(period.start_date))
        for k in range(period.duration.days // 7):
            ShiftInstance.objects.get_or_create(date=wi[k], shift=self)

    def instances_in_period(self, period):
        return ShiftInstance.objects.filter(shift=self,
                                            date__gte=period.start_date,
                                            date__lte=period.start_date+period.duration)
    def __str__(self):
        return f"<Shift {self.pk}: weekday={self.weekday}, time={self.shift_time}>"

    class Meta:
        ordering = ['weekday', 'shift_time']


class ShiftInstance(models.Model):
    shift = models.ForeignKey(Shift, null=True, on_delete=models.CASCADE)
    date = models.DateField()
    @property
    def start_time(self):
        return self.shift.start_time
    class Meta:
        ordering = ['date', 'shift']

class ShiftPreference(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    rank = NumChoiceField()
    def __str__(self):
        return f"<ShiftPreference {self.pk}: {self.family} ranks {self.shift} as {self.rank}>"

class FamilyAssignment(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    def __str__(self):
        return f"<FamilyAssignment {self.pk}: {self.family} assigned {self.shift} in period {self.period}>"


class FamilyCommitment(models.Model):
    family = models.ForeignKey(Child, on_delete=models.CASCADE)
    shift_instance = models.ForeignKey(ShiftInstance, on_delete=models.CASCADE)
    @property
    def date(self):
        return self.shift_instance.date
    @property
    def start_time(self):
        return self.shift_instance.start_time
    def __str__(self):
        return f"<FamilyCommitment {self.pk}: {self.family} has {self.shift_instance}>"
    class Meta:
        ordering = ['shift_instance']
