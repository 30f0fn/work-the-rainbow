import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.scheduler import *

from main.model_fields import WEEKDAYS

def randy_str():
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(3)])

# classroom
cr_name = randy_str().upper()
classroom = Classroom(name=cr_name, slug=cr_name)
classroom.save()

# kids
for i in range(10):
    Child.objects.create(nickname=randy_str(), classroom=classroom)
child = Child.objects.first()



####################
# scheduling stuff #
####################

# shifttimes
s1, _ = ShiftTimeSpan.objects.get_or_create(name='morning', start_time='08:30', end_time='10:30')
s2, _ = ShiftTimeSpan.objects.get_or_create(name='afternoon', start_time='13:30', end_time='15:30')
s3, _ = ShiftTimeSpan.objects.get_or_create(name='late stay', start_time='15:30', end_time='17:30')

period, _ = Period.objects.get_or_create(classroom=classroom, start_date=datetime.datetime(2019, 1, 1))


# shifts
for w in WEEKDAYS:
    if int(w) < 5:
        for st in ShiftTimeSpan.objects.all():
            s = Shift.objects.get_or_create(weekday=w, time_span = st)
            print(f"created {s}")

# shiftinstances
for s in Shift.objects.all():
    s.create_instances_in_period(period)

# shiftpreferences
for c in classroom.child_set.all():
    s = random.choice(Shift.objects.all())
    sp = ShiftPreference.objects.get_or_create(family=c, shift=s, rank=1)
    print(sp)


cdts, created = CareDayTimeSpan.objects.get_or_create(name='regular', start_time='08:30', end_time='15:30', extended_endtime='17:30')

for w in WEEKDAYS:
    if int(w) < 0:
        CareDay.objects.get_or_create(weekday=w,
                                      time_span=cdts)

for c in classroom.children:
    num_days = random.randrange(2,5)
    days = random.sample(list(range(5)), num_days)
    caredays = [CareDay.objects.all()[day] for day in days]
    lengths = [random.randrange(2) for i in range(num_days)]
    for i in range(num_days):
        CareDayAssignment.objects.create(child=c,
                                         extended=lengths[i],
                                         careday=caredays[i])
