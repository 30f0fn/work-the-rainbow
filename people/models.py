import functools

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from invitations.models import Invitation

import main.models


########
# todo #
########

# todo need roles parent, teacher, etc. to track the corresponding relations to objects child, classroom, etc
# need to retrieve all roles of user
# have logical and database relationzations, seems weird... do i need the data realization?


"""
role re-implementation

roles of a user are determined by other database entries
mainly needed for perspective navigator - want to return list of roles of given user, to generate series of links
also need to maintain one role as the 'active' one for a given user, defining current perspective (maybe this should be recorded as a session variable?)

without many-to-many relation to roles, how to determine that a user has several roles?  

is it possible to use groups instead?
"""

# todo how to ensure these exist?
# parent_role, _ = Role.objects.get_or_create(name='parent')
# teacher_role, _ = Role.objects.get_or_create(name='teacher')
# scheduler_role, _ = Role.objects.get_or_create(name='scheduler')
# admin_role, _ = Role.objects.get_or_create(name='admin')




class Role(Group):

    def get_absolute_url(self):
        return self.name+'-home'

    def _membership_predicate(self):
        return f'is_{self.name}'

    def _accepts(self, user):
        return getattr(user, self._membership_predicate())

    # todo seems sketchy
    def update_membership(self, user):
        if self._accepts(user):
            self.user_set.add(user)
        else:
            self.user_set.remove(user)
        self.save()

    class Meta:
        proxy = True



class User(AbstractUser):

    active_role = models.ForeignKey(Role, null=True,
                                     on_delete=models.PROTECT,
                                     related_name='active_for')

    # may have teacher without classroom
    @property
    def is_teacher(self):
        return self.classrooms_as_teacher.exists()

    @property
    def is_scheduler(self):
        return self.classrooms_as_scheduler().exists()

    @property
    def is_parent(self):
        return self.child_set.exists()

    @property
    def is_admin(self):
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

    @property
    def roles(self):
        # return Role.objects.filter()
        return self.groups.all()

    @property
    def has_multi_roles(self):
        return len(list(self.roles)) > 1

    def save(self, *args, **kwargs):
        if not self.active_role:
            self.active_role = self.roles.first()
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
        return self.name

    def __repr__(self):
        return f"<Classroom {self.pk}: {self.name}>"        


class Child(NamingMixin, models.Model):
    # first_name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    shifts_per_month = models.IntegerField(default=2)

    parent_set = models.ManyToManyField(User)

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

    def possible_shifts(self, start, end, include_commitments=False):
        # commitments = [] if not include_commitments else \
            # WorktimeCommitment.objects.filter(start__range=(start, end),
                                              # family__classroom=child.classroom)
        for careday_occurrence in self.careday_occurrences(start, end):
            for shift_occurrence in careday_occurrence.shift_occurrences():
                yield shift_occurrence
        

    # # below is hideous...
    # # want the union, for each careday of child, of the shifts of that careday
    # # how to do it in one query?
    # @property
    # def shifts(self):
    #     caredays = self.caredays.all()
    #     def get_q(careday):
    #         return Q(weekday=careday.weekday, 
    #                  start_time__gte=careday.start_time,
    #                  end_time__lte=careday.end_time)
    #     return main.models.Shift.objects.filter(
    #         functools.reduce(lambda x, y : x | y, map(get_q, caredays)))

    @property
    def worktime_commitments(self):
        return main.models.WorktimeCommitment.objects.filter(family=self)

    def __str__(self):
        return f"{self.nickname}"

    def __repr__(self):
        return f"<Child {self.pk}: {self.nickname}>"

    class Meta:
        pass


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
            Invitation.objects.filter(email=email).delete()
            invite = Invitation.create(email)
            invite.send_invitation(self.request)
            message = f"sent invite to {self.email}; upon signup the resulting user will be added to {self.related_object}'s {self.relation_name}"
            messages.add_message(self.request, messages.SUCCESS, message)

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
