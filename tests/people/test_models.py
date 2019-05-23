from django.test import TestCase
from people.models import *
# from django.utils import timezone
# from django.core.urlresolvers import reverse

"""
# models test
class ExampleTest(TestCase):

    def create_whatever(self, title="only a test", body="yes, this is only a test"):
        return Whatever.objects.create(title=title, body=body, created_at=timezone.now())

    def test_whatever_creation(self):
        w = self.create_whatever()
        self.assertTrue(isinstance(w, Whatever))
        self.assertEqual(w.__unicode__(), w.title)
"""

class PeopleTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        print("setUpTestData: Run once to set up non-modified data for all class methods.")
        cls.classroom = Classroom.objects.create(name="test classroom",
                                                  slug="test_classroom")
        cls.child = Child.objects.create(nickname="test child",
                                                  slug="test_child")
        cls.user1 = User.objects.create(username="test_user1", pk=99)
        cls.user2 = User.objects.create(username="test_user2", pk=100)


    def setUp(self):
        print("setUp: Run once for every test method to setup clean data.")
    


"""
upon adding user u to teachers of classroom, u.is_teacher should return True
"""

class UserIsTeacherTest(PeopleTest):
    def test_user_is_teacher(self):
        self.classroom.teacher_set.add(self.user1)
        self.assertTrue(self.user1.is_teacher)
        self.assertFalse(self.user2.is_teacher)

class UserIsParentTest(PeopleTest):
    def test_user_is_parent(self):
        self.child.parent_set.add(self.user1)
        self.assertTrue(self.user1.is_parent)
        self.assertFalse(self.user2.is_parent)

class UserIsSchedulerTest(PeopleTest):
    def test_user_is_scheduler(self):
        self.classroom.scheduler_set.add(self.user1)
        self.assertTrue(self.user1.is_scheduler)
        self.assertFalse(self.user2.is_scheduler)
    
