from django.test import TestCase
from people.models import *
from people.roles import *


# #############################################################
# # just do bare user/role/child/classroom functionality here #
# # reserve scheduling stuff (caredays, worktimes) for main   #
# #############################################################


class PeopleTest(TestCase):

    # none of below created objects should be modified in a test
    # to create in this method an object, e.g., scheduler, for modification in a test, add to make sure changes aren't carried over to next test
    # def setUp(self):
        # self.scheduler.refresh_from_db()

    @classmethod
    def setUpTestData(cls):
        cls.classroom = Classroom.objects.create(name="test classroom",
                                                  slug="test_classroom")
        cls.child = Child.objects.create(nickname="test child",
                                         slug="test_child",
                                         classroom=cls.classroom)
        cls.parent = User.objects.create_user(username="parent",
                                              password="parent_pw")
        cls.child.parent_set.add(cls.parent)
        cls.child2 = Child.objects.create(nickname="test child_2",
                                          slug="test_child_2",
                                          classroom=cls.classroom)
        cls.parent2 = User.objects.create_user(username="parent_2",
                                               password="parent_2_pw")
        cls.child2.parent_set.add(cls.parent2)
        cls.scheduler = User.objects.create_user(username="scheduler",
                                                  password="scheduler_pw")
        cls.classroom.scheduler_set.add(cls.scheduler)
        cls.teacher = User.objects.create_user(username="teacher",
                                              password="teacher_pw")
        cls.classroom.teacher_set.add(cls.teacher)
        cls.admin = User.objects.create_user(username="admin",
                                              password="admin_pw")
        cls.admin.make_admin()

        cls.user = User.objects.create_user(username="user",
                                             password="user_pw")
        cls.classroom2 = Classroom.objects.create(name="test classroom 2",
                                                   slug="test_classroom_2")
        cls.child3 = Child.objects.create(nickname="child 3",
                                          classroom=cls.classroom2)
        cls.parent3 = User.objects.create_user(username="parent_3",
                                               password="parent_3_pw")
        cls.child3.parent_set.add(cls.parent3)
        cls.teacher2 = User.objects.create_user(username="teacher_2",
                                                password="teacher_2_pw")
        cls.classroom2.teacher_set.add(cls.teacher2)
        cls.scheduler2 = User.objects.create_user(username="scheduler_2",
                                                  password="scheduler_2_pw")
        cls.classroom2.scheduler_set.add(cls.scheduler2)










