import calendar
import datetime

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
    offset = (weekday - from_date.weekday()) % 7        
    return from_date + datetime.timedelta(days=offset)


# def most_recent_date_with_given_weekday(weekday, from_date):
    # return next_date_with_given_weekday(1, from_date) - datetime.timedelta(days=7)


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



