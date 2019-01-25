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

user = User.objects.first()
child = Child.objects.first()
classroom = Classroom.objects.first()
period = Period.objects.filter(classroom=classroom).first()
shift = Shift.objects.first()
careday = CareDay.objects.first()
caredaytimespan = CareDayTimeSpan.objects.first()
si = ShiftInstance.objects.first()
# wcrf = WorktimeCommitmentRescheduleForm(si)


from django.forms import Form, BooleanField

class FutzForm(Form):
    boo = BooleanField()

ff = FutzForm({'boo':0})

from django.utils import unittest
from django.test.client import RequestFactory

class SimpleTest(unittest.TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

    def test_details(self):
        # Create an instance of a GET request.
        request = self.factory.get('/customer/details')

        # Test my_view() as if it were deployed at /customer/details
        response = my_view(request)
        self.assertEqual(response.status_code, 200)
