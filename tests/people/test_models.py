from django.test import TestCase
from people.generate_samples import setup_sample_classroom
from people.models import *
from people.roles import *


#############################################################
# just do bare user/role/child/classroom functionality here #
# reserve scheduling stuff (caredays, worktimes) for main   #
#############################################################

class PeopleTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.classroom = Classroom.objects.create(name="test classroom",
                                                  slug="test_classroom")
        self.classroom2 = Classroom.objects.create(name="test classroom2",
                                                  slug="test_classroom2")
        self.child = Child.objects.create(nickname="test child",
                                         slug="test_child")
        self.user1 = User.objects.create_user(username="test_user1",
                                         password="user1pw")
        self.user2 = User.objects.create_user(username="test_user2",
                                         password="user2pw")

        self.user1.save()
        self.user2.save()

    def configure_family(self):
        self.child.parent_set.add(self.user1)
        self.child.classroom = self.classroom
        self.child.save()
    


        


######################
# testing Role model #
######################


class RoleAbsoluteUrlTest(PeopleTest):
    def test_teacher_url(self):
        self.assertEqual(TEACHER.get_absolute_url(), '/teacher')
    def test_admin_url(self):
        self.assertEqual(ADMIN.get_absolute_url(), '/admin')
    
class RoleMemPredIdentityTest(PeopleTest):
    def teacher_mem_pred(self):
        self.assertEqual(TEACHER._membership_predicate(),
                         '_is_teacher')

class RoleAcceptanceTest(PeopleTest):
    def test_teacher_accepts(self):
        self.assertFalse(TEACHER.accepts(self.user1))
        self.classroom.teacher_set.add(self.user1)
        self.assertTrue(TEACHER.accepts(self.user1))
    def test_scheduler_accepts(self):
        self.assertFalse(SCHEDULER.accepts(self.user1))
        self.classroom.scheduler_set.add(self.user1)
        self.assertTrue(SCHEDULER.accepts(self.user1))
    def test_parent_accepts(self):
        self.assertFalse(PARENT.accepts(self.user1))
        self.child.parent_set.add(self.user1)
        self.assertTrue(PARENT.accepts(self.user1))
    def test_admin_accepts(self):
        self.assertFalse(ADMIN.accepts(self.user1))
        self.user1.make_admin()
        self.assertTrue(ADMIN.accepts(self.user1))
        
class RoleUpdateMembershipTest(PeopleTest):
    def test_teacher_update(self):
        self.assertFalse(TEACHER in self.user1.roles())
        self.classroom.teacher_set.add(self.user1)        
        self.assertTrue(TEACHER in self.user1.roles())
        self.assertEqual(self.user1.active_role(), TEACHER)
    def test_scheduler_update(self):
        self.assertFalse(SCHEDULER in self.user1.roles())
        self.classroom.scheduler_set.add(self.user1)        
        self.assertTrue(SCHEDULER in self.user1.roles())
        self.assertEqual(self.user1.active_role(), SCHEDULER)
    def test_parent_update(self):
        self.assertFalse(PARENT in self.user1.roles())
        self.child.parent_set.add(self.user1)        
        self.assertTrue(PARENT in self.user1.roles())
        self.assertEqual(self.user1.active_role(), PARENT)
    def test_admin_update(self):
        self.assertFalse(ADMIN in self.user1.roles())
        self.user1._role_set.add(ADMIN)
        self.assertTrue(ADMIN in self.user1.roles())
        self.assertEqual(self.user1.active_role(), ADMIN)



######################
# testing User model #
######################


class UserIsTeacherTest(PeopleTest):
    def test_user_is_teacher(self):
        self.classroom.teacher_set.add(self.user1)
        self.assertTrue(self.user1._is_teacher())
        self.assertFalse(self.user2._is_teacher())

class UserIsParentTest(PeopleTest):
    def test_user_is_parent(self):
        self.child.parent_set.add(self.user1)
        self.assertTrue(self.user1._is_parent())
        self.assertFalse(self.user2._is_parent())

class UserIsSchedulerTest(PeopleTest):
    def test_user_is_scheduler(self):
        self.classroom.scheduler_set.add(self.user1)
        self.assertTrue(self.user1._is_scheduler())
        self.assertFalse(self.user2._is_scheduler())

class UserIsAdminTest(PeopleTest):
    def test_user_is_admin(self):
        self.user1.make_admin()
        self.assertTrue(self.user1._is_admin())
        self.assertFalse(self.user2._is_admin())

class UserClassroomsPerRole(PeopleTest):
    def test_as_parent(self):
        self.configure_family()
        self.user1.update_active_role(PARENT)
        self.assertTrue(self.classroom in self.user1.classrooms())
        self.assertFalse(self.classroom2 in self.user1.classrooms())
    def test_as_scheduler(self):
        self.classroom.scheduler_set.add(self.user1)
        self.user1.update_active_role(SCHEDULER)
        self.assertTrue(self.classroom in self.user1.classrooms())
        self.assertFalse(self.classroom2 in self.user1.classrooms())
    def test_as_teacher(self):
        self.classroom.teacher_set.add(self.user1)
        self.user1.update_active_role(TEACHER)
        self.assertTrue(self.classroom in self.user1.classrooms())
        self.assertFalse(self.classroom2 in self.user1.classrooms())
    def test_as_admin(self):
        self.user1.make_admin()
        self.user1.update_active_role(ADMIN)
        self.assertTrue(self.classroom in self.user1.classrooms())

class UserMultiRolesTest(PeopleTest):
    def test_multi_roles(self):
        self.assertTrue(self.user1.multi_roles() == [])
        self.user1._role_set.add(TEACHER)
        self.user1._role_set.add(SCHEDULER)
        self.assertTrue(TEACHER in self.user1.multi_roles())    
        self.assertTrue(SCHEDULER in self.user1.multi_roles())    

class UserSaveTest(PeopleTest):
    def test_save(self):
        user = User(username="new_user")
        self.assertTrue(user._active_role is None)
        user.save()
        self.assertTrue(user.active_role() == NULL_ROLE)



#####################
# testing classroom #
#####################

class ClassroomParentsTest(PeopleTest):
    def test(self):
        self.assertFalse(self.user1 in self.classroom.parents())
        self.configure_family()
        self.assertTrue(self.user1 in self.classroom.parents())

class CreateSampleClassroomTest(TestCase):

    def test(self):
        classroom = setup_sample_classroom(
            name="Test Sample Classroom")
        caredays = main.models.CareDay.objects.filter(classroom=classroom)
        self.assertEqual(caredays.count(), 10)
        shifts = main.models.Shift.objects.filter(classroom=classroom)
        self.assertEqual(shifts.count(), 15)
        periods = main.models.Period.objects.filter(classroom=classroom)
        self.assertEqual(periods.count(), 2)
        kids = Child.objects.filter(classroom=classroom)
        self.assertEqual(kids.count(), 10)
        prefs = [main.models.ShiftPreference.objects.filter(period=period)
             for period in periods]
        for p in range(periods.count()):
            self.assertEqual(prefs[p].count(), 20)
        for child in kids:
            commitments = main.models.WorktimeCommitment.objects.filter(child=child)
            self.assertTrue(commitments.count() >= 8)


###############################
# testing RelateEmailToObject #
###############################

class RetoTest(PeopleTest):
    def test_execute(self):
        u = User(username='sdfjewoj',
                 email='hmm@hmm.com')
        u.save()
        self.assertFalse(u in self.child.parent_set.all())
        reto = RelateEmailToObject(
            email = 'hmm@hmm.com',
            relation='parent_set',
            relation_name='parents',
            related_object = self.child)
        reto.execute()
        self.assertFalse(u in self.classroom.teacher_set.all())
        reto2 = RelateEmailToObject(
            email = 'hmm@hmm.com',
            relation='teacher_set',
            relation_name='teachers',
            related_object = self.classroom)
        reto2.execute()
        self.assertTrue(u in self.classroom.teacher_set.all())
        
