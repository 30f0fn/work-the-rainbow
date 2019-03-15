import calendar
import datetime

from django.utils import timezone

class WeekdayIterator:
    def __init__(self, start_date):
        self.first = start_date
        super().__init__()
    def __getitem__(self, index):
        return self.first + (index * datetime.timedelta(days=7))


# def dates_from_range(start_date, num_days):
    # return [WeekdayIterator(self.start_date)[n]
            # for n in range(num_days)]


def next_date_with_given_weekday(weekday, from_date):
    offset = (int(weekday) - from_date.weekday()) % 7        
    return from_date + datetime.timedelta(days=offset)


def next_occurrence_from(time, weekday, date):
    occ_date = next_date_with_given_weekday(weekday, from_date)
    return occ_date.replace(hour=time.hour(), minute=time.minute())


# take weekday+time date, construct next instance from date
def occurrences_for_date_range(rule, from_date, to_date, exclusions=[]):
    return recurrence.Recurrence(
        dtstart = dtstart,
        dtend = to_date,
        exclusions = exclusions,
        rrules = [recurrence.Rule(recurrence.WEEKLY)])



# def most_recent_date_with_given_weekday(weekday, from_date):
    # return next_date_with_given_weekday(1, from_date) - datetime.timedelta(days=7)


def add_delta_to_time(time, timedelta):
    stupid_datetime = (datetime.datetime.combine(
        datetime.datetime.now().date(), time))
    return (stupid_datetime + timedelta).time()

def week_from(first_day):
    return [start_date + datetime.timedelta(days=i)
            for i in range(7)]


def week_of(date):
    return week_from(previous_date_with_given_weekday(1, date))


def weeks_for_month(year, month, outliers=False):
    month_calendar = calendar.monthcalendar(year, month)
    if outliers:
        start_date = previous_date_with_given_weekday(
            1, datetime.date(year, month, 1))
        weeks = [week_from(start_date + w * datetime.timedelta(days=7)) 
                 for w in month_calendar]
    else:
        weeks = [[datetime.date(year, month, d) if d > 0 else None
                  for d in w] for w in month_calendar]
    return weeks




def dates_in_range(start, end):
    date = start
    while date <= end:
        yield date
        date += datetime.timedelta(days=1)


# move to manager of CareDays
def caredays_in_range(start, end):
    holidays = Holiday.objects.filter(start_date__lte=end_date,
                                      end_date__gte=start_date)
    holiday_dates = [date for holiday in holidays
                     for date in date_range(holiday.start_date, holiday.end_date)]
    date = start
    while date <= end:
        if date not in holiday_dates and date.weekday() < 5:
            yield date
        date += datetime.timedelta(days=1)

def in_a_week():
    return timezone.now() + datetime.timedelta(days=7)

def serialize_datetime(dt):
    data = map(str, [dt.year, dt.month, dt.day,
             dt.hour, dt.minute,
             # dt.tzinfo()
    ])
    return "-".join(data)

def deserialize_datetime(dts):
    data = map(int, dts.split("-"))
    return timezone.datetime(*data)

def nearest_monday(dt):
    weekday = dt.weekday()
    offset = weekday if weekday < 5 \
        else weekday - 7
    return dt - datetime.timedelta(days=offset)
