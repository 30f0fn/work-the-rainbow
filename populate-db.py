import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.scheduler import *

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


# shifttimes
s1, _ = ShiftTime.objects.get_or_create(name='morning', start_time='08:30')
s2, _ = ShiftTime.objects.get_or_create(name='afternoon', start_time='13:30')
s3, _ = ShiftTime.objects.get_or_create(name='late stay', start_time='15:30')

period, _ = Period.objects.get_or_create(classroom=classroom, start_date=datetime.datetime(2019, 1, 1))


# shifts
for w in WEEKDAYS:
    if int(w) < 5:
        for st in ShiftTime.objects.all():
            Shift.objects.get_or_create(weekday=w, shift_time = st)
            print(f"created {s}")

# shiftinstances
for s in Shift.objects.all():
    s.create_instances_in_period(period)

# shiftpreferences
for c in classroom.child_set.all():
    s = random.choice(Shift.objects.all())
    sp = ShiftPreference.objects.get_or_create(family=c, shift=s, rank=1)
    print(sp)






