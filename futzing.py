import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.utilities import *

classroom = Classroom.objects.first()
period = Period(classroom=classroom, start_date=datetime.datetime(2019, 1, 1))
shift = Shift.objects.first()
for s in Shift.objects.all():
    s.create_instances_in_period(period)



Invitation.objects.all()
u = User.objects.all()[0]
c = Child.objects.first()
uuu = User.objects.all()[2]
lrb = Classroom.objects.all()[0]
