# work-the-rainbow/people/views.py

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView, FormView, CreateView, UpdateView, DeleteView, TemplateView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils import timezone
# from django.template.response import TemplateResponse

from collections import namedtuple

# from allauth.account.views import LoginView
# from allauth.account.views import SignupView as LocalSignupView
from allauth.account.models import EmailAddress
# from allauth.socialaccount.views import SignupView as SocialSignupView
from invitations.models import Invitation
from rules.contrib.views import PermissionRequiredMixin

from people.forms import RelateEmailToObjectForm, CreateClassroomForm, AddChildForm, ChildUpdateForm
from people.models import Classroom, Child, User, RelateEmailToObject
from people.roles import *
from people import skins
import main.models
from . import rules



#############
# utilities #
#############
 
class RelateEmailToObjectView(FormView):
    # subclass this with values for relation and get_related_object
    template_name = 'generic_create.html'
    form_class = RelateEmailToObjectForm
    relation = None
    relation_name = None

    def get_related_object(self, *args, **kwargs):
        raise NotImplementedError("you need to implement get_related_object")

    # should this be a method of the related_object value? 
    def form_valid(self, form):
        email = form.cleaned_data['email']
        related_object = self.get_related_object()
        leto = RelateEmailToObject(email=email,
                                   relation=self.relation,
                                   relation_name=self.relation_name,
                                   related_object=related_object)
        leto.activate(self.request)
        return super().form_valid(form)


# class ClassroomMixin(LoginRequiredMixin, object):
class ClassroomMixin(LoginRequiredMixin,
                     PermissionRequiredMixin):
    permission_required = 'people.view_classroom'

    def get_permission_object(self):
        return self.classroom

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.pop('classroom_slug')
        self.classroom = Classroom.objects.get(slug=slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'classroom' : self.classroom})
        return context


class ClassroomEditMixin(ClassroomMixin):
    permission_required = 'people.edit_classroom'

    def get_success_url(self):
        return reverse_lazy('manage-classroom',
                            kwargs={'classroom_slug':self.classroom.slug})



class ChildMixin(LoginRequiredMixin,
                 PermissionRequiredMixin):
    permission_required = 'people.view_child_profile'

    def get_permission_object(self):
        return self.child

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.pop('child_slug')
        self.child = Child.objects.get(slug=slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'child' : self.child})
        return context


class ChildEditMixin(ChildMixin):
    permission_required = 'people.edit_child'

    def get_success_url(self):
        return reverse_lazy('child-profile',
                            kwargs={'child_slug':self.child.slug})


class AdminMixin(object):
    permission_required = 'people.admin'






###################
# top-level views #
###################


# list all teachers and all children
# links to add a teacher or a child
# todo finish this
class ClassroomView(ClassroomMixin, DetailView):
    def get_object(self):
        return self.classroom
    permission_required='people.view_classroom'
    model = Classroom


class ManageClassroomView(ClassroomMixin, DetailView):
    def get_object(self):
        return self.classroom
    permission_required='people.edit_classroom'
    template_name = 'manage_classroom.html'
    model = Classroom


class ClassroomCreateView(PermissionRequiredMixin, FormView):
    permission_required = 'people.create_classroom'
    template_name = 'classroom_create.html'
    form_class = CreateClassroomForm

    def get_success_url(self, *args, **kwargs):
        return self.classroom.get_absolute_url()

    def form_valid(self, form):
        classroom = Classroom(**{key:form.cleaned_data[key]
                                 for key in dir(Classroom)
                                 if key in form.cleaned_data})
        classroom.save()
        for email in form.cleaned_emails():
            RelateEmailToObject(email=email,
                                relation='scheduler_set',
                                relation_name='schedulers',
                                related_object=classroom).activate(self.request)
        self.classroom = classroom
        message = f"created the {classroom.name} classroom"
        messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)
    

##########
# Mixins #
##########

# class AddItemToClassroomTemplateMixin(object):
    # template_name='add_item_to_classroom.html'


#########################
# generic views - child #
#########################

"""
create child, invite parents by email
if user already exists (i.e., no user has the listed email)
then configure user's profile as parent of child
else, check if invite exists to this email;
if not, then send invite
upon user creation, receiver attaches user to child as parent
"""
class ChildAddView(ClassroomEditMixin,
                   FormView):
    template_name = 'child_create.html'
    form_class = AddChildForm

    def form_valid(self, form):
        form.cleaned_data['classroom'] = self.classroom
        child = Child(**{key:form.cleaned_data[key]
                                for key in dir(Child)
                                if key in form.cleaned_data})
        child.save()
        for email in form.cleaned_emails():
            RelateEmailToObject(email=email,
                                relation='parent_set',
                                relation_name='parents',
                                related_object=child).activate(self.request)
            self.child = child
        message = f"added the kid {child.nickname}"
        messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)


class AddParentToChildView(ChildEditMixin, RelateEmailToObjectView):
    template_name = 'add_parent_to_child.html'
    relation = 'parent_set'

    def get_related_object(self):
        try:
            return Child.objects.get(slug=self.kwargs['child_slug'])
        except Child.DoesNotExist:
            raise Http404("Child does not exist")
        # return render(request, 'worktime/404.html', {'child': p})




# # edit child
class ChildEditView(ChildEditMixin,
                    UpdateView):
    # support move child to other classroom?
    model = Child
    form_class = ChildUpdateForm
    template_name = 'generic_update.html'

    def get_object(self, *args, **kwargs):
        return self.child

    # def post(self, *args, **kwargs):
    #     print(self.request.POST)
    #     return super().post(*args, **kwargs)


# # # delete child from db
# class ChildRemoveView(ClassroomEditMixin,
#                       DeleteView):
#     model = Child


class RelateEmailToClassroomView(ClassroomEditMixin,
                                 RelateEmailToObjectView):

    def get_related_object(self):
        return self.classroom



class SchedulerAddView(RelateEmailToClassroomView):
    template_name='add_item_to_classroom.html'
    relation = 'scheduler_set'
    relation_name = 'scheduler'



class TeacherAddView(RelateEmailToClassroomView):
    template_name='add_item_to_classroom.html'
    relation = 'teacher_set'
    relation_name = 'teacher'





class ProfileDataMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        profilee = self.get_object()
        if TEACHER in profilee.roles():
            context['classrooms_as_teacher'] = \
                Classroom.objects.filter(
                           teacher_set=profilee)
        if PARENT in profilee.roles():
            context['children_as_parent'] = profilee.child_set.all()
        return context
    

# this is only to be seen by the user (and perhaps site admin)
# have ParentDetail for intra-classroom users
# shouldnt need permissions rule, since view should determine which profile to show based on current user

class PrivateProfileView(LoginRequiredMixin,
                         ProfileDataMixin,
                         DetailView):

    template_name = 'private_profile.html'

    def get_object(self):
        return self.request.user


class PublicProfileView(LoginRequiredMixin,
                        ProfileDataMixin,
                        DetailView):

    template_name = 'public_profile.html'
    model = User
    context_object_name = 'user_object'

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)


class ProfileEditView(LoginRequiredMixin,
                      UpdateView):
    model = User
    fields = ['username']
    template_name = 'profile_update.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('profile')


class RecolorView(LoginRequiredMixin,
                  RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        self.request.user.recolor()
        return kwargs.pop('referring_url')
    
# class ParentRemoveView(ClassroomEditMixin, QuerysetInClassroomMixin, DetailView):
#     model = Parent


class ChildDetailView(ChildMixin,
                      DetailView):
    model = Child
    template_name = 'child_detail.html'

    # can I use the child property from dispatch of ChildMixin?
    def get_object(self):
        try:
            slug = self.kwargs.get('child_slug')
            return Child.objects.get(slug=slug)
        except Child.DoesNotExist:
            raise Http404("Item does not exist")

    def periods_soliciting_preferences(self):
        return main.models.Period.objects.filter(
            classroom=self.child.classroom,
            solicits_preferences=True)

    def periods(self):
        try:
            return self._periods
        except AttributeError:
            self._periods = main.models.Period.objects.filter(
                classroom_id=self.child.classroom_id,
                end__gte=timezone.now())
            return self._periods

    def commitments_by_period(self):
        retval = {}
        periods = main.models.Period.objects.filter(classroom=self.child.classroom,
                                        end__gte=timezone.now())
        for period in periods:
            commitments = main.models.WorktimeCommitment.objects.filter(
                child=self.child,
                start__date__gte=period.start.date(),
                start__date__lte=period.end.date())
            if commitments:
                retval[period] = commitments
        return retval
        # CbyP = namedtuple('CbyP', ['period', 'commitments'])        
        # commitments = WorktimeCommitment.objects.filter(
            # child=self.child)
        # for commitment in commitments:

    def prefs_by_period(self):
        return main.models.ShiftPreference.objects.for_child_by_period(
            self.child,
            [period for period in self.periods() if period.solicits_preferences])
        

    def careday_assignments(self):
        return self.child.caredayassignment_set.filter(end__gte=timezone.now()).\
            distinct().select_related('careday').order_by('start')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['prefs_by_period'] = self.prefs_by_period()
        context['commitments_by_period'] = self.commitments_by_period()
        context['now'] = timezone.now()
        context['careday_assignments'] = self.careday_assignments()
        return context





class NotificationsView(LoginRequiredMixin,
                        TemplateView):

    template_name = 'notifications.html'

    def get(self, *args, **kwargs):
        def mark_as_read(response):
            context = self.get_context_data(**kwargs)
            context['unread'].mark_all_as_read()
        response = super().get(*args, **kwargs)
        response.add_post_render_callback(mark_as_read)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            unread = self.request.user.notifications.unread()
            read = self.request.user.notifications.read()
            context.update({'unread' : unread,
                            'read' : read})
        return context
