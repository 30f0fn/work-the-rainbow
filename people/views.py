# work-the-rainbow/people/views.py
from django.views.generic import DetailView, ListView, FormView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from allauth.account.views import LoginView
from allauth.account.views import SignupView as LocalSignupView
from allauth.socialaccount.views import SignupView as SocialSignupView

from . import forms, models
from . import decorators

# from . import models

# easy-to-implement classroom management flow
# create classroom
# from classroom management, use links to AddChild and AddTeacher
# AddChild simply asks for child name and parents' email
# AddTeacher asks for teacher name and teacher's email


#############
# utilities #
#############


class ClassroomMixin(object):
    def get_classroom(self):
        slug = self.kwargs['classroom_slug']
        return models.Classroom.objects.get(slug=slug)

class ClassroomEditMixin(ClassroomMixin):
    def get_success_url(self):
        return reverse_lazy('manage-classroom',
                            kwargs={'slug':self.get_classroom().slug})

class GetObjectInClassroomMixin(ClassroomMixin):
    def get_queryset(self):
        obj = self.model.objects.filter(classroom=self.get_classroom(),
                                        slug=self.kwargs[item_slug])    


###################
# top-level views #
###################

class ClassroomCreateView(CreateView):
    model = models.Classroom
    fields = ['name', 'slug']
    template_name = 'people/classroom_create.html'
    # form_class = CreateClassroomForm
    def get_success_url(self):
        return reverse_lazy('manage-classroom', kwargs={'slug':self.object.slug})
# , slug=self.object.slug)

# list all teachers and all children
# links to add a teacher or a child
class ClassroomView(DetailView):
    model = models.Classroom


#########################
# invitation and signup #
#########################

# verify that url token matches invite
# offer either social login, or password entry

# try to get the invite
# redirect if unsuccessful
# if successful, show the template, with links
class InviteAcceptView(TemplateView):
    template_name = 'invited_signup_choice.html'
    def get(self, *args, **kwargs):
        try:
            invite = models.ParentInvite.objects.get(token = self.kwargs['token'])
            # if invite.is_active():
            user, created = models.User.objects.get_or_create(email=invite.email)
            if created:
                user.username = invite.email
            user.save()
            invite.delete()
            return super().get(self, *args, **kwargs)
            # else:
                # raise DoesNotExist
        except models.ParentInvite.DoesNotExist:
            # message "sorry, I couldn't validate the required signup invitation"
            return redirect('index')




class InvitedSignupMixin(object):

    @decorators.validate_invite_token
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(self, form)
        token = self.kwargs.get('token')
        invite = models.ParentInvite.objects.get(token=token)        
        profile = Profile(user=self.user, is_parent=True)
        profile.save()
        invite.child.parents.add(profile)
        return response

class InvitedSignupView(InvitedSignupMixin, LocalSignupView):
    pass
    
# user gets this view after linking social account for initial signup
class InvitedSocialSignupView(InvitedSignupMixin, SocialSignupView):
    pass 
    

#########################
# generic views - child #
#########################


class ChildrenListView(ListView):
    model = models.Child

# create child, invite parents by email 
# todo: prevent duplicates
class ChildAddView(ClassroomEditMixin, FormView):
    template_name = "child_create.html"
    form_class = forms.AddChildForm

    def form_valid(self, form):
        classroom = self.get_classroom()
        child = models.Child(**{key:form.cleaned_data[key]
                                for key in dir(models.Child)
                                if key in form.cleaned_data})
        child.classroom = classroom
        child.save()
        emails = [form.cleaned_data[email_field]
                  for email_field in ['parent_email_1', 'parent_email_2']]
        [models.ParentInvite.objects.get_or_create(email=email)[0].save()
         for email in emails if email]
        return super().form_valid(form)

class ChildDetailView(GetObjectInClassroomMixin, FormView):
    model = models.Child

# # edit child
class ChildEditView(GetObjectInClassroomMixin, ClassroomEditMixin, UpdateView):
    model = models.Child
    # form_class = EditChildForm

# create child, invite parents by email
class ChildRemoveView(GetObjectInClassroomMixin, ClassroomEditMixin, DeleteView):
    model = models.Child


############################
# generic views - teacher  #
############################

class TeachersListView(ListView):
    model = models.Teacher

class TeacherAddView(ClassroomEditMixin, CreateView):
    model = models.Teacher
    fields = ['first_name', 'last_name', 'classroom']

class TeacherDetailView(GetObjectInClassroomMixin, DetailView):
    model = models.Teacher

class TeacherEditView(ClassroomEditMixin, GetObjectInClassroomMixin, UpdateView):
    model = models.Teacher

class TeacherRemoveView(ClassroomEditMixin, GetObjectInClassroomMixin, DeleteView):
    model = models.Teacher


###########################
# generic views - parents #
###########################

class ParentsListView(ListView):
    model = models.Parent

class ParentDetailView(GetObjectInClassroomMixin, DetailView):
    model = models.Parent

class ParentEditView(ClassroomEditMixin, GetObjectInClassroomMixin, DetailView):
    model = models.Parent

class ParentRemoveView(ClassroomEditMixin, GetObjectInClassroomMixin, DetailView):
    model = models.Parent

    
