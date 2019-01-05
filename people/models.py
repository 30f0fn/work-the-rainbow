from django.db import models
from django.contrib.auth.models import AbstractUser
from people.email import send_invite_email
import random

class User(AbstractUser):
    pass

class NamingMixin(object):
    def name(self):
        return self.__class__.__name__


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_parent = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)


class Classroom(NamingMixin, models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    teachers = models.ManyToManyField(Profile)
    def add_teacher(self, user_profile):
        self.teachers.add(user_profile)
        user_profile.is_teacher = true
    def add_pupil(self, kid):
        kid.classroom = self
    def __repr__(self):
        return f"<Classroom object {self.pk}: {self.name}>"        



class Child(NamingMixin, models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
    shifts_per_month = models.IntegerField(default=2)
    parents = models.ManyToManyField(Profile)
    def add_parent(self, user_profile):
        self.parents.add(user_profile)
        user_profile.is_parent = True
    class Meta:
        pass
    def __repr__(self):
        return f"<Child object {self.pk}: {self.short_name}>"


        # unique_together = (("first_name", "last_name", "classroom"),
                           # ("short_name", "classroom"))


class Teacher(NamingMixin, models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
    class Meta:
        pass
        # unique_together = (("first_name", "last_name", "classroom"))


class Parent(NamingMixin, models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.DO_NOTHING)
    class Meta:
        pass
    def __repr__(self):
        return f"<Parent object {self.pk}: {self.first_name} {self.last_name} {self.classroom}>"

        # unique_together = (("first_name", "last_name", "classroom"))


class ParentInvite(models.Model):
    email = models.EmailField(unique=True)
    child = models.ForeignKey(Child, on_delete=models.DO_NOTHING)
    accepted = False
    token = models.CharField(max_length=50)
    def save(self, *args, **kwargs):
        self.token = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
                              for i in range(50)])
        send_invite_email(self.email, self.token)
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"<Invite object {self.pk}: {self.email}>"
