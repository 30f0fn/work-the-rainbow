
def dates_in_range(start, end):
    date = start
    while date <= end:
        yield date
        date += datetime.timedelta(days=1)

def instances_in_date_range(shift, start_date, end_date):
    holidays = Holiday.objects.filter(start_date__lte=end_date,
                                      end_date__gte=start_date)
    holiday_dates = [date for holiday in holidays
                     for date in date_range(holiday.start_date, holiday.end_date)]
    date = next_date_with_given_weekday(int(shift.weekday), start_date)
    while date <= end_date:
        if date not in holiday_dates:
            yield ShiftInstance.from_shift(shift, date)
        date += datetime.timedelta(days=7)
 
def even_nums_in_range(min, max):
    num = min
    while num <= max:
        if num % 2 == 0:
            yield num
        num += 1

idr = instances_in_date_range(shift, today, next_month)
for i in idr:
    print(i)
