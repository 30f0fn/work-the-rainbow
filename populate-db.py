import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.scheduler import *

from main.model_fields import WEEKDAYS

def randy_str(len=3):
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(len)])

# classroom
# cr_name = randy_str().upper()
classroom = Classroom(name='XCK', slug='XCK')
classroom.save()

# kids
for i in range(10):
    Child.objects.create(nickname=randy_str(), classroom=classroom)

child = Child.objects.first()



####################
# scheduling stuff #
####################

# shifttimes
# s1, _ = ShiftTimeSpan.objects.get_or_create(name='morning', start_time='08:30', end_time='10:30')
# s2, _ = ShiftTimeSpan.objects.get_or_create(name='afternoon', start_time='13:30', end_time='15:30')
# s3, _ = ShiftTimeSpan.objects.get_or_create(name='late stay', start_time='15:30', end_time='17:30')

period, _ = Period.objects.get_or_create(classroom=classroom, start=timezone.now()-datetime.timedelta(days=30), end = timezone.now()+datetime.timedelta(days=90))

shift_timespans = [('8:30', '10:30'), ('13:30', '15:30'), ('15:30', '17:30')]

# shifts
for w in WEEKDAYS:
    if int(w) < 5:
        for st in shift_timespans:
            s = Shift.objects.get_or_create(weekday=w,
                                            start_time = st[0],
                                            end_time=st[1],
                                            classroom=classroom)
            print(f"created {s}")


# cdts, created = CareDayTimeSpan.objects.get_or_create(name='regular', start_time='08:30', end_time='15:30', extended_endtime='17:30')

for w in WEEKDAYS:
    if int(w) < 5:
        CareDay.objects.get_or_create(weekday=w,
                                      start_time='8:30',
                                      end_time='15:30',)
        CareDay.objects.get_or_create(weekday=w,
                                      start_time='15:30',
                                      end_time='17:30',)


for c in classroom.child_set.all():
    num_days = random.randrange(2,6)
    days = random.sample(list(range(5)), num_days)
    caredays = [CareDay.objects.filter(start_time__hour=8)[day] for day in days]
    # ext_caredays = CareDay.objects.filter(start_time.hour=15)
    for i in range(num_days):
        careday = caredays[i]
        CareDayAssignment.objects.create(child=c,
                                         careday=careday,
                                         start=period.start,
                                         end=period.end)
        if random.randrange(2):
            ext_careday = CareDay.objects.get(
                start_time__hour=15,
                weekday=careday.weekday)
            CareDayAssignment.objects.create(child=c,
                                             careday=ext_careday,
                                             start=period.start,
                                             end=period.end)
            


# shiftpreferences
for c in classroom.child_set.all():
    caredays = CareDay.objects.filter(caredayassignment__child=child)
    shifts = list(itertools.chain.from_iterable([
        careday.shifts for careday in caredays]))
    s = random.choice(shifts)
    sp = ShiftPreference.objects.get_or_create(family=c, shift=s, rank=1)
    print(sp)
     
    
from main.scheduler import *

create_optimal_shift_assignments(classroom, period)
create_commitments(classroom, period)


# def get_q(careday):
#     return Q(weekday=careday.weekday, 
#              start_time__gte=careday.start_time,
#              end_time__lte=careday.end_time)

# run below after creating superuser mw
