#################
# generic setup #
#################

import rules
from people.models import *
from allauth.account.models import *
from invitations.models import *
from main.models import * 
from main.scheduler import *
from main.forms import *
import datetime 
from main.scheduler import *

user = User.objects.first()
child = Child.objects.first()
classroom = Classroom.objects.first()
period = Period.objects.filter(classroom=classroom).first()
shift = Shift.objects.first()
careday = CareDay.objects.first()
careday_assignment = CareDayAssignment.objects.filter(child=child).first()
# si = ShiftInstance.objects.first()

today = timezone.now().date()
next_month = today + datetime.timedelta(days=30)
today = timezone.now().date()
now = timezone.now()
inamonth = now + datetime.timedelta(days=30)

parent_role = Role.objects.get(name='parent')
teacher_role = Role.objects.get(name='teacher')
scheduler_role = Role.objects.get(name='scheduler')
admin_role = Role.objects.get(name='admin')

a_week = datetime.timedelta(days=7)

