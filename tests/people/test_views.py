from datetime import datetime

from django.urls import reverse

from notifications.signals import notify

from people.models import *
from people.roles import *
from people.forms import *

from tests.people.test_perms_for_views import *
from tests.people.test_base_classes import *

"""
class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

"""


    

class ClassroomViewTest(ClassroomMixinPermTestMixin,
                        PeopleTest):

    def vut_url(self):
        return reverse('classroom-roster',
                       kwargs = {'classroom_slug' : 'test_classroom'})

    def test_get(self):
        login = self.client.login(username='parent',
                                  password='parent_pw')
        response = self.client.get(self.vut_url())
        self.assertEqual(response.context['user'], self.parent)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'people/classroom_detail.html')
        self.assertEqual(response.context['object'],
                         Classroom.objects.get(slug='test_classroom'))


class ManageClassroomViewTest(ClassroomEditMixinPermTestMixin,
                              PeopleTest):

    def vut_url(self):
        return reverse('manage-classroom',
                       kwargs = {'classroom_slug' : 'test_classroom'})


class ClassroomCreateViewTest(AdminMixinPermTestMixin,
                              PeopleTest):

    def vut_url(self):
        return reverse('create-classroom')

    def test_get_if_admin(self):
        self.client.login(username='admin',
                          password='admin_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.admin)
        self.assertTemplateUsed(response,
                                'classroom_create.html')
        # todo how to verify form?
        # self.assertEqual(response.context['form']
        #                  CreateClassroomForm())

    def test_create_classroom(self):
        scheduler1 = User.objects.create_user(username='sched_user',
                                              password='sched_pw',
                                              email='sched1@abc.xyz')
        login = self.client.login(username='admin',
                                  password='admin_pw')
        response = self.client.post(
            self.vut_url(),
            {'scheduler_email_1' : 'sched1@abc.xyz',
             'scheduler_email_2' : 'sched2@abc.xyz',
             'slug' : 'new_classroom',
             'name' : 'New Classroom'})
        classroom = Classroom.objects.get(slug='new_classroom')
        self.assertRedirects(response,
                             classroom.get_absolute_url())
        self.assertTrue(scheduler1 in classroom.scheduler_set.all())
        reto = RelateEmailToObject.objects.get(
            # email='sched2.abc.xyz',
            relation_name='schedulers')
        self.assertEqual(reto.email, 'sched2@abc.xyz')
        scheduler2 = User.objects.create_user(username='sched_2',
                                              password='sched2_pw',
                                              email='sched2@abc.xyz')
        self.assertTrue(scheduler2 in classroom.scheduler_set.all())
        # self.assertTrue(Invitation.objects.filter(
            # email='sched2.abc.xyz').exists())
        
    
class ChildAddViewTest(ClassroomEditMixinPermTestMixin,
                       PeopleTest):

    def vut_url(self):
        return reverse('add-child',
                       kwargs = {'classroom_slug' : 'test_classroom'})
    
    def test_get_for_scheduler(self):
        self.client.login(username='scheduler',
                          password='scheduler_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.scheduler)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'child_create.html')

    def test_add_child(self):
        self.assertTrue(self.scheduler.has_perm('people.edit_classroom',
                                                 self.classroom))
        temp_parent1 = User.objects.create_user(username='temp_parent1',
                                           password='temp_parent1_pw',
                                           email='temp_parent1@abc.xyz')
        # self.scheduler.update_active_role(SCHEDULER)
        login = self.client.login(username='scheduler',
                                  password='scheduler_pw')
        self.assertTrue(login)
        response = self.client.post(
            self.vut_url(),
            {'nickname' : 'added_child',
             'shifts_per_month' : '2',
             'parent_email_1' : 'temp_parent1@abc.xyz',
             'parent_email_2' : 'temp_parent2@abc.xyz',
            })
        # self.assertEqual(response.context['user'],
                         # self.scheduler)
        self.assertRedirects(response,
                             reverse('manage-classroom',
                                     kwargs = {'classroom_slug' : self.classroom.slug}))
        child = Child.objects.get(slug='added_child')
        self.assertTrue(child in self.classroom.child_set.all())
        self.assertTrue(temp_parent1 in child.parent_set.all())
        reto = RelateEmailToObject.objects.get(
            relation_name='parents')
        self.assertEqual(reto.email, 'temp_parent2@abc.xyz')
        temp_parent2 = User.objects.create_user(username='temp_parent',
                                           password='temp_parent_pw',
                                           email='temp_parent2@abc.xyz')
        self.assertTrue(temp_parent2 in child.parent_set.all())
        # self.assertTrue(Invitation.objects.filter(
            # email='sched2.abc.xyz').exists())




class AddParentToChildViewTest(ChildEditMixinPermTestMixin,
                               PeopleTest):


    def vut_url(self):
        return reverse('add-parent',
                       kwargs = {'child_slug' : self.child.slug})
    
    def test_get_if_scheduler(self):
        self.client.login(username='scheduler',
                          password='scheduler_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.scheduler)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'add_parent_to_child.html')

    def test_add_parent(self):
        login = self.client.login(username='scheduler',
                                  password='scheduler_pw')
        response = self.client.post(
            self.vut_url(),
            {'email' : 'temp_parent@abc.xyz'},
        )
        self.assertRedirects(response,
                             reverse('child-profile',
                                     kwargs = {'child_slug' : self.child.slug}))
        temp_parent = User.objects.create_user(username='temp_parent',
                                               password='pw',
                                               email='temp_parent@abc.xyz')
        self.assertTrue(temp_parent in self.child.parent_set.all())






class ChildEditViewTest(ChildEditMixinPermTestMixin,
                        PeopleTest):

# fields = ['nickname', 'shifts_per_month', 'birthday', ]


    def vut_url(self, **kwargs):
        self.child.refresh_from_db()
        url_kwargs = kwargs.get('url_kwargs',
                                {'child_slug' : self.child.slug}) 
        return reverse('edit-child', kwargs=url_kwargs)
    
    def test_get_if_parent(self):
        self.client.login(username='parent',
                          password='parent_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.parent)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'generic_update.html')

    def test_post_if_parent(self):
        # temp_child = Child.objects.create(nickname='temp_child',
                                          # classroom=self.classroom)
        # temp_parent = User.objects.create_user(username='temp_parent',
                                               # password='temp_parent_pw')
        # temp_child.classroom = self.classroom
        # temp_child.parent_set.add(temp_parent)
        login = self.client.login(username='parent',
                                  password='parent_pw')
        post_url = self.vut_url(url_kwargs={'child_slug' : self.child.slug})
        # print("post_url", post_url)
        response = self.client.post(
            post_url,
            {'nickname' : 'altered child nickname',
             'birthday' : '2099-01-01',
             'shifts_per_month' : '2',
             # 'fish' : '2asdfkj'
            },
        )
        self.child.refresh_from_db()
        self.assertRedirects(response,
                             reverse('child-profile',
                                     kwargs = {'child_slug' : self.child.slug}))
        self.assertEqual(self.child.nickname, 'altered child nickname')
        self.assertEqual(self.child.birthday.year, 2099)
        self.assertEqual(self.child.shifts_per_month, 2)

    # def test_post_if_parent(self):
    #     temp_child = Child.objects.create(nickname='temp_child',
    #                                       classroom=self.classroom)
    #     temp_parent = User.objects.create_user(username='temp_parent',
    #                                            password='temp_parent_pw')
    #     temp_child.classroom = self.classroom
    #     temp_child.parent_set.add(temp_parent)
    #     login = self.client.login(username='temp_parent',
    #                               password='temp_parent_pw')
    #     print("vut_url", self.vut_url(url_kwargs={'child_slug' : temp_child.slug}))
    #     response = self.client.post(
    #         self.vut_url(url_kwargs={'child_slug' : temp_child.slug}),
    #         {'nickname' : 'altered_temp_child_nickname',
    #          'birthday' : '2014-01-01',
    #          'shifts_per_month' : '9'},
    #     )
    #     self.assertRedirects(response,
    #                          reverse('child-profile',
    #                                  kwargs = {'child_slug' : temp_child.slug}))
    #     self.assertTrue(temp_child.nickname == 'altered_test_child_nickname')
    #     self.assertTrue(temp_child.birthday == '2014-01-01')
    #     self.assertTrue(temp_child.shifts_per_month == '9')





class SchedulerAddViewTest(ClassroomEditMixinPermTestMixin,
                           PeopleTest):


    def vut_url(self):
        return reverse('add-scheduler',
                       kwargs = {'classroom_slug' : self.classroom.slug})
    
    def test_get_if_scheduler(self):
        self.client.login(username='scheduler',
                          password='scheduler_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'add_item_to_classroom.html')

    def test_add_scheduler(self):
        login = self.client.login(username='scheduler',
                                  password='scheduler_pw')
        response = self.client.post(
            self.vut_url(),
            {'email' : 'temp_scheduler@abc.xyz'},
        )
        self.assertRedirects(response,
                             reverse('manage-classroom',
                                     kwargs = {'classroom_slug' : self.classroom.slug}))
        temp_scheduler = User.objects.create_user(username='temp_scheduler',
                                                  password='pw',
                                                  email='temp_scheduler@abc.xyz')
        self.assertTrue(temp_scheduler in self.classroom.scheduler_set.all())




class TeacherAddViewTest(ClassroomEditMixinPermTestMixin,
                         PeopleTest):

    def vut_url(self):
        return reverse('add-teacher',
                       kwargs = {'classroom_slug' : self.classroom.slug})
    
    def test_get_if_scheduler(self):
        self.client.login(username='scheduler',
                          password='scheduler_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'add_item_to_classroom.html')

    def test_add_teacher(self):
        login = self.client.login(username='scheduler',
                                  password='scheduler_pw')
        response = self.client.post(
            self.vut_url(),
            {'email' : 'temp_teacher@abc.xyz'},
        )
        self.assertRedirects(response,
                             reverse('manage-classroom',
                                     kwargs = {'classroom_slug' : self.classroom.slug}))
        temp_teacher = User.objects.create_user(username='temp_teacher',
                                                  password='pw',
                                                  email='temp_teacher@abc.xyz')
        self.assertTrue(temp_teacher in self.classroom.teacher_set.all())



class PrivateProfileViewTest(PermittedForUserTestMixin,
                             PeopleTest):

    def vut_url(self):
        return reverse('profile')

    def test_get_if_user(self):
        self.client.login(username='user',
                          password='user_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'private_profile.html')


class PublicProfileViewTest(PermittedForUserTestMixin,
                            PeopleTest):

    def vut_url(self):
        return reverse('public-profile',
                       kwargs = {'username' : self.parent.username})

    def test_get_if_other_parent_same_classroom(self):
        self.client.login(username='parent_2',
                          password='parent_2_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'public_profile.html')


class ChildDetailViewTest(ChildMixinPermTestMixin,
                          PeopleTest):

    def vut_url(self):
        return reverse('child-profile',
                       kwargs = {'child_slug' : self.child.slug})

    def test_get_if_other_parent_same_classroom(self):
        self.client.login(username='parent_2',
                          password='parent_2_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'child_detail.html')

class ProfileEditViewTest(PermittedForUserTestMixin,
                          PeopleTest):

    def vut_url(self, **kwargs):
        return reverse('edit-profile')
    
    def test_get_for_parent(self):
        self.client.login(username='parent',
                          password='parent_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.parent)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'profile_update.html')

    def test_get_for_user(self):
        self.client.login(username='user',
                          password='user_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.context['user'],
                         self.user)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'profile_update.html')


    def test_post_for_parent(self):
        login = self.client.login(username='parent',
                                  password='parent_pw')
        post_url = self.vut_url()
        response = self.client.post(
            post_url,
            {'username' : 'altered-username-for-parent',
            },
        )
        self.parent.refresh_from_db()
        self.assertRedirects(response,
                             reverse('profile'))
        self.assertEqual(self.parent.username, 'altered-username-for-parent')


class NotificationsViewTest(PermittedForUserTestMixin,
                            PeopleTest):

    def vut_url(self, **kwargs):
        return reverse('notifications')

    def test_get_for_parent(self):
        notify.send(self.admin,
                    recipient=[self.parent],
                    verb='updated',
                    description="this is a test notification")
        notify.send(self.admin,
                    recipient=[self.parent],
                    verb='updated',
                    description="another test notification")
        notify.send(self.admin,
                    recipient=[self.user],
                    verb='updated',
                    description="a test notification for different user")
        self.client.login(username='parent',
                          password='parent_pw')
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'notifications.html')
        self.assertEqual(response.context['unread'][0].description,
                         "another test notification")
        self.assertEqual(response.context['unread'][1].description,
                         "this is a test notification")
        self.assertEqual(response.context['unread'].count(), 2)
         


