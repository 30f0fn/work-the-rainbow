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
from people import skins


########
# todo #
########


class Role(Group):

    @staticmethod
    def _update_all_membership():
        for role in Role.objects.all():
            for user in User.objects.all():
                role.update_membership(user)

    def _url_name(self):
        return self.name+'-home'

    def get_absolute_url(self):
        return reverse(self._url_name())


    def _membership_predicate(self):
        return f'_is_{self.name}'

    # this calls the definition of belonging to a particular role
    # its return value is maintained by presence of role in user.roles
    def accepts(self, user):
        return getattr(user, self._membership_predicate())()

    # update cache to match normative definitions of role membership
    def update_membership(self, user):
        if self.accepts(user) and self not in user._role_set.all():
            user._role_set.add(self)
            from people.roles import NULL_ROLE
            if user.active_role() == NULL_ROLE:
                user.update_active_role(self)
        if self in user._role_set.all() and not self.accepts(user):
            user._role_set.remove(self)
            if user._active_role == self and user.roles():
                user.update_active_role(user.roles()[0])
    
    class Meta:
        proxy = True


class User(AbstractUser):

    # todo what if this is null? yuck
    # make model field private, use getters and setters
    # have getter return default role (or something) if field is null
    _active_role = models.ForeignKey(Role, null=True,
                                    on_delete=models.PROTECT,
                                    related_name='active_for')

    _role_set = models.ManyToManyField(Role,
                                      related_name='_bearers')
    
    skin = models.TextField(default=skins.date_seeded_skin)

    # these are the four normative definitions of role membership
    def _is_teacher(self):
        return self._classrooms_as_teacher.all()

    def _is_scheduler(self):
        return self._classrooms_as_scheduler.all()

    def _is_parent(self):
        return self.child_set.exists()

    def _is_admin(self):
        from people.roles import ADMIN
        return ADMIN in self.roles()

    # these are the public, cached role possession access methods
    def is_teacher(self):
        from people.roles import TEACHER
        return TEACHER in self.roles()

    def is_parent(self):
        from people.roles import PARENT
        return PARENT in self.roles()

    @property
    def _classrooms_as_parent(self):
        return Classroom.objects.filter(
            child__parent_set=self).distinct()

    @property
    def _classrooms_as_admin(self):
        return Classroom.objects.all()

    @property
    def _classrooms_as_null(self):
        return Classroom.objects.none()

    def recolor(self):
        skins.recolor(self)

    def classrooms(self):
        role = self.active_role()
        return getattr(self, f'_classrooms_as_{role.name}').all()

    def make_admin(self):
        from people.roles import ADMIN
        self._role_set.add(ADMIN)
        self.update_active_role(ADMIN)
        
    def active_role(self):
        try:
            return self._active_role or self.roles()[0]
        except IndexError:
            from people.roles import NULL_ROLE
            return NULL_ROLE

    def update_active_role(self, role):
        assert role in self.roles()
        self._active_role = role
        super().save()

    def roles(self):
        return self._role_set.all()

    # to format navigation panels... could be in views?
    def multi_roles(self):
        roles = self.roles()
        return roles if len(roles) > 1 else []

    def save(self, *args, **kwargs):
        # need an initial save before accessing self.roles()
        if not self.pk:
            super().save(*args, **kwargs)
            if not self._active_role:
                roles = self.roles()
                if roles:
                    self._active_role = roles[0]
        super().save(*args, **kwargs)


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

    # used only in people.rules.py
    def parents(self):
        return User.objects.filter(child__classroom=self)

    #todo needed?
    def worktime_commitments_by_date(self, date):
        return main.models.WorktimeCommitment.objects.filter(
            child__classroom=self,
            shift_instance__date=date)
    
    def periods_soliciting_preferences(self):
        return self.period_set.filter(solicits_preferences=True)

    def get_absolute_url(self):
        return reverse_lazy('classroom-roster', kwargs={'classroom_slug':self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Classroom {self.pk}: {self.name}>"        


# class ClassroomSettings(models.Model):
    # classroom = models.OneToOneField(Classroom)
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

    # # todo test this
    # def has_careday_occurrence(self, occ):
    #     return main.models.CareDayAssignment.objects.filter(
    #         child=child,
    #         start__lte=occ.start,
    #         end__gte=self.start,
    #         caredays=self.careday).exists()


    # def careday_occurrences(self, start, end):
        # for careday in main.models.CareDayAssignment.objects.careday_occurrences_for_child(
                # child=self, start=start, end=end):
            # yield careday

    # # todo move to main.models.ShiftManager
    # def possible_shifts(self, start, end):
    #     # commitments = [] if not include_commitments else \
    #         # WorktimeCommitment.objects.filter(start__range=(start, end),
    #                                           # child__classroom=child.classroom)
    #     for careday_occurrence in self.careday_occurrences(start, end):
    #         for shift_occurrence in careday_occurrence.shift_occurrences():
    #             yield shift_occurrence


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
# upon save, then add account as parent of child
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
