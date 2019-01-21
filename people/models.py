import functools

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy

import main.models

########
# todo #
########

# clean out the API for e.g. Classroom (want uniform access to parents/teachers/schedulers/children)


# class FakeQuerySet(object):
#     def __init__(self, entries):
#         super().__init__()
#         self.entries = entries
#     def all(self):
#         return self.entries



from people.email import send_invite_email
from invitations.models import Invitation
import random

class User(AbstractUser):

    # may have teacher without classroom
    is_teacher = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    @property
    def classrooms_as_parent(self):
        return Classroom.objects.filter(child__parents=self)

    @property
    def classrooms(self):
        if self.is_admin:
            return Classroom.objects.all()
        else:
            return (self.classrooms_as_parent.all() \
                    | self.classrooms_as_teacher.all()).distinct()

    @property
    def children(self):
        return self.child_set.all()

    @property
    def worktime_commitments(self):
        return self.child_set


class NamingMixin(object):
    def name(self):
        return self.__class__.__name__


class Classroom(NamingMixin, models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    teacher_set = models.ManyToManyField(User,
                                      related_name='classrooms_as_teacher')
    scheduler_set = models.ManyToManyField(User,
                                        related_name='classrooms_as_scheduler')

    @property
    def teachers(self):
        return self.teacher_set.all()

    @property
    def schedulers(self):
        return self.scheduler_set.all()

    @property
    def children(self):
        return self.child_set.all()

    @property
    def parents(self):
        return User.objects.filter(child__classroom=self)

    def worktime_commitments_by_date(self, date):
        return main.models.WorktimeCommitment.objects.filter(
            family__classroom=self,
            shift_instance__date=date)

    def get_absolute_url(self):
        return reverse_lazy('classroom-roster', kwargs={'slug':self.slug})

    def __str__(self):
        return f"<Classroom {self.pk}: {self.name}>"        


class Child(NamingMixin, models.Model):
    # first_name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
    shifts_per_month = models.IntegerField(default=2)
    parents = models.ManyToManyField(User)

    @property
    def caredays(self):
        return main.models.CareDay.objects.filter(caredayassignment__child=self)


    # below is hideous...
    # want the union, for each careday of child, of the shifts of that careday
    # how to do it in one query?
    @property
    def shifts(self):
        caredays = self.caredays.all()
        def get_q(careday):
            return Q(weekday=careday.weekday, 
                     time_span__start_time__gte=careday.time_span.start_time,
                     time_span__end_time__lte=careday.time_span.end_time)
        return main.models.Shift.objects.filter(
            functools.reduce(lambda x, y : x | y, map(get_q, caredays)))

    @property
    def worktime_commitments(self):
        return main.models.WorktimeCommitment.objects.filter(family=self)

    def __str__(self):
        return f"<Child {self.pk}: {self.nickname}>"

    class Meta:
        pass



        # unique_together = (('first_name', 'last_name', 'classroom'),
                           # ('short_name', 'classroom'))


# class Teacher(NamingMixin, models.Model):
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
#     class Meta:
#         pass
#         # unique_together = (('first_name', 'last_name', 'classroom'))


# class Parent(NamingMixin, models.Model):
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
#     class Meta:
#         pass
#     def __str__(self):
#         return f"<Parent {self.pk}: {self.first_name} {self.last_name} {self.classroom}>"

        # unique_together = (('first_name', 'last_name', 'classroom'))


# class ParentInvite(models.Model):
#     email = models.EmailField(unique=True)
#     child = models.ForeignKey(Child, on_delete=models.DO_NOTHING, null=True)
#     accepted = False
#     token = models.CharField(max_length=50)
#     def save(self, *args, **kwargs):
#         self.token = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
#                               for i in range(50)])
#         send_invite_email(self.email, self.token)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"<Invite object {self.pk}: {self.email}>"

# when user is created, check if it has this email address, and if so, configure the user to be parent of this child
# class EmailLinkFromChild(models.Model):
#      child = models.ForeignKey(Child, on_delete=models.CASCADE)
#      email = models.EmailField()
#      def __str__(self):
#          return f"<EmailLinkFromChild: child={self.child}, email={self.email}>"


class RelateEmailToObject(models.Model):
    email = models.EmailField()
    relation = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey()

    def execute(self):
        related_user = User.objects.get(models.Q(emailaddress__email=self.email)
                                       | models.Q(email=self.email))
        getattr(self.related_object, self.relation).add(related_user)
        self.related_object.save()
        if self.pk:
            self.delete()
        return related_user

    def __str__(self):
        return f"<relating {self.email} to {self.related_object} under {self.relation}>"

            

"""
need to link user who owns emailaddress to object obj
also need to specify nature of the link
e.g., is the user a parent of child, scheduler of classroom, ...?
typically, the link is represented by obj.<owners>.all(), effected by obj.<owners>.add(), etc, for some ManyToManyField <owners>
it works to do getattr(obj, <owners>).add(user)
"""
