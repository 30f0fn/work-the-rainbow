 # work-the-rainbow/people/views.py

from django.http import Http404
from django.shortcuts import render
from django.views.generic import DetailView, ListView, FormView, CreateView, UpdateView, DeleteView, TemplateView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator

from collections import namedtuple

# from allauth.account.views import LoginView
# from allauth.account.views import SignupView as LocalSignupView
from allauth.account.models import EmailAddress
# from allauth.socialaccount.views import SignupView as SocialSignupView
from invitations.models import Invitation
from rules.contrib.views import PermissionRequiredMixin

from . import forms
from people.models import Classroom, Child, User, RelateEmailToObject
import main.models
from . import rules


########
# todo #
########

# the property-decorated methods should be genuine properties of the view, maybe set in dispatch()
# prune unused template files

#############
# utilities #
#############
 
class RelateEmailToObjectView(FormView):
    # subclass this with values for relation and get_related_object
    template_name = 'generic_create.html'
    form_class = forms.RelateEmailToObjectForm
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
class ClassroomMixin(LoginRequiredMixin, PermissionRequiredMixin):
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



class QuerysetInClassroomMixin(ClassroomMixin):
    def get_queryset(self):
        return self.model.objects.filter(classroom=self.classroom,
                                        slug=self.kwargs[item_slug])    



class ChildMixin(LoginRequiredMixin, PermissionRequiredMixin):
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






# # todo replace all references to family with references to child
# class FamilyMixin(object):

#     def dispatch(self, request, *args, **kwargs):
#         self.family = Child.objects.get(nickname=self.kwargs.get('nickname'))
#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context.update({'family' : self.family})
#         return context




########################
# Role-switching views #
########################

class SwitchRolesView(RedirectView):

    def new_role(self):
        return self.kwargs.pop('new_role')

    def get_redirect_url(self):
        return f'{self.new_role()}-home'

###################
# top-level views #
###################


# list all teachers and all children
# links to add a teacher or a child

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
    form_class = forms.CreateClassroomForm
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

class AddItemToClassroomTemplateMixin(object):
    template_name='add_item_to_classroom.html'


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
class ChildAddView(ClassroomEditMixin, FormView):
    template_name = 'child_create.html'
    form_class = forms.AddChildForm

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


class AddParentToChildView(RelateEmailToObjectView):
    def get_related_object(self):
        try:
            return Child.objects.get(slug=self.kwargs['child_slug'])
        except Child.DoesNotExist:
            raise Http404("Child does not exist")
        # return render(request, 'worktime/404.html', {'child': p})




# # edit child
class ChildEditView(ChildMixin, UpdateView):
    model = Child
    fields = ['nickname']
    template_name = 'generic_update.html'

    def get_object(self, *args, **kwargs):
        return self.child

    # form_class = EditChildForm



# # delete child from db
class ChildRemoveView(QuerysetInClassroomMixin, ClassroomEditMixin, DeleteView):
    model = Child


class RelateEmailToClassroomView(ClassroomEditMixin, RelateEmailToObjectView):

    def get_related_object(self):
        return self.classroom


#############################
# generic views - scheduler #
#############################

class SchedulerAddView(AddItemToClassroomTemplateMixin,
                       RelateEmailToClassroomView):
    relation = 'scheduler_set'
    relation_name = 'scheduler'


############################
# generic views - teacher  #
############################

class TeacherAddView(AddItemToClassroomTemplateMixin,
                     RelateEmailToClassroomView):
    relation = 'teacher_set'
    relation_name = 'teacher'


###########################
# generic views - parents #
###########################

# class ParentsListView(ListView):
#     model = Parent


# this is only to be seen by the user (and perhaps site admin)
# have ParentDetail for intra-classroom users
# shouldnt need permissions rule, since view should determine which profile to show based on current user
class PrivateProfileView(DetailView):

    template_name = 'profile_detail.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class PublicProfileView(DetailView):

    def get_object(self):
        try:
            username = self.kwargs.get('username')
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404("does not exist")



    template_name = 'profile_detail.html'


class ChildDetailView(ChildMixin, DetailView):
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

    def prefs_by_period(self):
        PbyP = namedtuple('PbyP', ['period', 'preferences'])
        periods = self.periods_soliciting_preferences()
        preferences = list(main.models.ShiftPreference.objects.filter(
            child=self.child,
            period__in=periods).select_related('shift').order_by('-period'))
        for period in periods:
            pp = PbyP(period, [])
            while preferences and preferences[-1].period:
                pp.preferences.append(preferences.pop())
            yield pp



    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['prefs_by_period'] = self.prefs_by_period()
        return context


class ProfileEditView(UpdateView):
    model = User
    fields = ['username', 'email']
    template_name = 'profile_update.html'
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)
    def get_object(self):
        return self.request.user


# class ParentRemoveView(ClassroomEditMixin, QuerysetInClassroomMixin, DetailView):
#     model = Parent
