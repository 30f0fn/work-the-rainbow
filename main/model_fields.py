from django.db import models

WEEKDAYS = {
    '0' : 'Monday',
    '1' : 'Tuesday',
    '2' : 'Wednesday',
    '3' : 'Thursday',
    '4' : 'Friday',
    '5' : 'Saturday',
    '6' : 'Sunday',
}

class WeekdayField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = tuple(sorted(WEEKDAYS.items()))
        kwargs['max_length'] = 1 
        super().__init__(*args, **kwargs)

class NumChoiceField(models.IntegerField):
    def __init__(self, lo=1, hi=4, *args, **kwargs):
        kwargs['choices'] = tuple({str(i):i for i in range(lo, hi)}.items())
        super().__init__(*args, **kwargs)
