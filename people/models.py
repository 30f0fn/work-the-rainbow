import functools

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.text import slugify

from invitations.models import Invitation

import main.models


########
# todo #
########

# todo need roles parent, teacher, etc. to track the corresponding relations to objects child, classroom, etc
# need to retrieve all roles of user
# have logical and database relationzations, seems weird... do i need the data realization?
# todo need to ensure admin role automatically added
# todo use special methods for child.add_parent(u) which sets u.is_parent=True


# todo how to ensure these exist?
# parent_role, _ = Role.objects.get_or_create(name='parent')
# teacher_role, _ = Role.objects.get_or_create(name='teacher')
# scheduler_role, _ = Role.objects.get_or_create(name='scheduler')
# admin_role, _ = Role.objects.get_or_create(name='admin')

# todo the methods user.classrooms_as_X could instead be user.active_role.classrooms(user)



class Role(Group):

    def get_absolute_url(self):
        return self.name+'-home'

    def _membership_predicate(self):
        return f'is_{self.name}'

    def accepts(self, user):
        return getattr(user, self._membership_predicate())

    class Meta:
        proxy = True


class User(AbstractUser):

    # todo what if this is null? yuck
    active_role = models.ForeignKey(Role, null=True,
                                    on_delete=models.PROTECT,
                                    related_name='active_for')

    # doesn't allow teacher without classroom
    @property
    def is_teacher(self):
        # change by adding/removing self from classroom.teacher_set for some classroon
        return self.classrooms_as_teacher().exists()

    @property
    def is_scheduler(self):
        # change by adding/removing self from classroom.scheduler_set for some classroom
        return self.classrooms_as_scheduler().exists()

    @property
    def is_parent(self):
        # change by adding/removing self from child.parent_set for some child
        return self.child_set.exists()

    @property
    def is_admin(self):
        # change primitively
        return self.is_superuser

    def classrooms_as_parent(self):
        return Classroom.objects.filter(
            child__parent_set=self).distinct()

    def classrooms_as_admin(self):
        return Classroom.objects.all()

    def classrooms_as_teacher(self):
        return self._classrooms_as_teacher.all()

    def classrooms_as_scheduler(self):
        return self._classrooms_as_scheduler.all()

    @property
    def classrooms(self):
        return getattr(self, f'classrooms_as_{self.active_role.name}')()

    @property
    def children(self):
        return self.child_set.all()

    # todo remove this decorator!!
    @property
    def roles(self):
        # todo must be better way to ensure role membership is correct
        return [role for role in Role.objects.all()
                if role.accepts(self)]

    @property
    def multi_roles(self):
        roles = self.roles
        return roles if len(roles) > 1 else []

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.active_role and self.roles:
            self.active_role = self.roles[0]
            # todo what if user has no roles?
        super().save(*args, **kwargs)

    # @property
    # def worktime_commitments(self):
        # return self.child_set


class NamingMixin(object):
    def name(self):
        return self.__class__.__name__


class Classroom(NamingMixin, models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    teacher_set = models.ManyToManyField(User,
                                      related_name='_classrooms_as_teacher')
    scheduler_set = models.ManyToManyField(User,
                                        related_name='_classrooms_as_scheduler')
    # solicits_preferences = models.BooleanField(default=True)

    # todo needed?
    @property
    def parents(self):
        return User.objects.filter(child__classroom=self)

    #todo needed?
    def worktime_commitments_by_date(self, date):
        return main.models.WorktimeCommitment.objects.filter(
            child__classroom=self,
            shift_instance__date=date)
        

    def get_absolute_url(self):
        return reverse_lazy('classroom-roster', kwargs={'classroom_slug':self.slug})

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Classroom {self.pk}: {self.name}>"        


# class ClassroomSettings(models.Model):
    # classroom = models.ForeignKey(Classroom)
    # commitment_change_notice_min_days = models.IntegerField(default=2)
    # shiftpreference_min = 2


class Child(NamingMixin, models.Model):
    # first_name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, unique=True)
    classroom = models.ForeignKey(Classroom, null=True, blank=True,
                                  on_delete=models.PROTECT)
    shifts_per_month = models.IntegerField(default=2)
    slug = models.SlugField(unique=True, null=True)
    parent_set = models.ManyToManyField(User)
    birthday = models.DateField(blank=True, null=True)

    # todo test this
    def has_careday_occurrence(self, occ):
        return main.models.CareDayAssignment.objects.filter(
            child=child,
            start__lte=occ.start,
            end__gte=self.start,
            caredays=self.careday).exists()


    def careday_occurrences(self, start, end):
        for careday in main.models.CareDayAssignment.objects.careday_occurrences_for_child(
                child=self, start=start, end=end):
            yield careday

    def possible_shifts(self, start, end):
        # commitments = [] if not include_commitments else \
            # WorktimeCommitment.objects.filter(start__range=(start, end),
                                              # child__classroom=child.classroom)
        for careday_occurrence in self.careday_occurrences(start, end):
            for shift_occurrence in careday_occurrence.shift_occurrences():
                yield shift_occurrence

    def careday_assignments(self):
        return self.caredayassignment_set.all().distinct().select_related('careday')

    @property
    def worktime_commitments(self):
        return main.models.WorktimeCommitment.objects.filter(child=self)

    def __str__(self):
        return f"{self.nickname}"

    def __repr__(self):
        return f"<Child {self.pk}: {self.nickname}>"

    def get_absolute_url(self):
        return reverse('child-profile',
                       kwargs={'child_slug' : self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.nickname)
        super(Child, self).save(*args, **kwargs)

    class Meta:
        ordering = ['nickname']


# admin wants to add person x as e.g. parent of c regardless of whether x has account
# so, enter email of x; if account exists for it simply add it as parent
# else, send invite and listen for save of user account with that address
# upon save, then add account as parent of c
class RelateEmailToObject(models.Model):
    email = models.EmailField()
    relation = models.CharField(max_length=50)
    relation_name = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.relation_name:
            self.relation_name = self.relation

    def activate(self, request):
        try:
            related_user = self.execute()
            message = f"added user {related_user} to {self.related_object}'s {self.relation_name}"
            messages.add_message(request, messages.SUCCESS, message)
        except User.DoesNotExist:
            self.save()
            Invitation.objects.filter(email=self.email).delete()
            invite = Invitation.create(self.email)
            invite.send_invitation(request)
            message = f"sent invite to {self.email}; upon signup the resulting user will be added to {self.related_object}'s {self.relation_name}"
            messages.add_message(request, messages.SUCCESS, message)

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
