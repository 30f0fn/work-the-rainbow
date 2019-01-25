import datetime
import calendar
# import dateutil
from dateutil import parser as dateutil_parser, relativedelta
# from dateutil import relativedelta

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q

from rules.contrib.views import PermissionRequiredMixin

from main import rules
from people.models import Child, Classroom
from people.views import ClassroomEditMixin
import main.utilities
import main.models
import main.forms


########
# todo #
########


# rescheduling
# workflow for scheduler

class HomeView(TemplateView):
    template_name = 'home.html'
    
# this just handles general time structuring stuff..
# for content, use mixins below

class CalendarMixin(object):
    
    @property
    def date(self):
        try:
            return datetime.datetime(self.kwargs.get('year', None),
                                     self.kwargs.get('month', None),
                                     self.kwargs.get('day', None))
        except TypeError:
            return datetime.datetime.now()

    def jump_url(self, increment):
        date = self.date + relativedelta.relativedelta(**{self.unit:increment})
        kwargs= {'classroom_slug':self.classroom.slug,
                 'year':date.year, 'month':date.month, 'day':date.day}
        return reverse_lazy(f'{self.unit_name}-classroom-calendar',
                            kwargs=kwargs)
 
    @property
    def next(self):
        return self.jump_url(1)

    @property
    def previous(self):
        return self.jump_url(-1)


class HolidayMixin(object):
    @property
    def holidays(self):
        return main.models.Holiday.objects.filter(
            classroom=classroom,
            date__gte=self.start_date,
            date__lte=self.start_date+self.duration)


############################
# classroom calendar views #
############################

class BaseCalendarView(main.models.ClassroomWorktimeMixin, HolidayMixin, CalendarMixin, TemplateView):
    pass

class DailyClassroomCalendarView(BaseCalendarView):
    template_name = 'daily_calendar.html'
    unit = 'days'
    unit_name = 'daily'

    @property
    def start_date(self):
        return self.date

    @property
    def worktimes_struct(self):
        return self.shifts_dict(self.date)



class WeeklyClassroomCalendarView(BaseCalendarView):
    template_name = 'weekly_calendar.html'
    unit = 'weeks'
    unit_name = 'weekly'

    @property
    def start_date(self):
        return (main.utilities.next_date_with_given_weekday(0, self.date) \
                - datetime.timedelta(days=7))

    @property
    def worktimes_struct(self):
        return self.days_dict(self.start_date, 5)


class MonthlyClassroomCalendarView(BaseCalendarView):
    template_name = 'monthly_calendar.html'
    unit = 'months'
    unit_name = 'monthly'

    @property
    def start_date(self):
        first_of_month = datetime.date(self.date.year, self.date.month, 1)
        return (main.utilities.next_date_with_given_weekday(0, first_of_month) -
                datetime.timedelta(days=7))

    @property
    def worktimes_struct(self):
        num_weeks = len(main.utilities.weeks_for_month(self.date.year, self.date.month))
        return list(self.weeks_list(self.start_date, num_weeks))

            

################
# rescheduling #
################

"""
workflow:
link from the commitment to a rescheduling form
form is a weekly calendar, oriented around the to-be-scheduled commitment
on implementation side, it is basically a modelchoicefield 
"""

# inheritance?
class WorktimeCommitmentRescheduleView(LoginRequiredMixin,
                                       PermissionRequiredMixin,
                                       UpdateView):
    permission_required = 'main.edit_worktimecommitment'
    model = main.models.WorktimeCommitment
    # fields = ['shift_instance']
    form_class = main.forms.WorktimeCommitmentRescheduleForm
    template_name = "worktimecommitment_reschedule.html"
    success_url = reverse_lazy('home')
    

    # def get_initial(self, *args, **kwargs):
    #     initial = super().get_initial(*args, **kwargs)
    #     data = {'shift_instance': ShiftInstance.objects}
    #     initial.update(data)
    #     return initial


#########################
# family calendar views #
#########################

class UpcomingEventsView(LoginRequiredMixin, CalendarMixin, TemplateView):
    template_name = "upcoming_for_user.html"

    def holidays(self):
        return main.models.Holiday.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))

    def worktime_commitments(self):
        return main.models.WorktimeCommitment.objects.filter(
            family__parent_set=self.request.user)

    def events(self):
        return main.models.Happening.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))


################################
# Worktime preference handling #
################################

# class ClassroomMixin(LoginRequiredMixin, object):
# class ClassroomMixin(LoginRequiredMixin, PermissionRequiredMixin, object):
    # permission_required = 'people.view_classroom'
    # @property


# require selection of at least n shifts, for some n fixed by settings
# change form so that the fields are the shift instances and the options are the ranks (rather than vice versa)
class WorktimePreferencesSubmitView(ClassroomEditMixin, FormView): 
    template_name = 'preferences_submit.html'
    form_class = main.forms.PreferenceSubmitForm

    @property
    def child(self):
        return Child.objects.get(nickname=self.kwargs.get('child'),
                                 classroom=self.classroom)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['child'] = self.child
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {rank: main.models.Shift.objects.filter(
            shiftpreference__family=self.child,
            shiftpreference__rank=i) 
                for i, rank in enumerate(self.get_form_class().ranks)}
        initial.update(data)
        return initial

    def form_valid(self, form):
        form.save_prefs()
        return super().form_valid(form)


class MakeWorktimeCommitmentsMixin(object):
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.pop('classroom_slug')
        self.classroom = Classroom.objects.get(slug=slug)
        self.family = Child.objects.get(nickname=self.kwargs.get('child_slug'),
                                        classroom=self.classroom)
        self.start_date = (main.utilities.next_date_with_given_weekday(0, self.date) \
                           - datetime.timedelta(days=7))
        # above code used in weeklyclassroomcalendarview, also resembles monthly
        self.end_date = self.start_date + self.duration
        self.existing_commitments = main.models.ShiftInstance.objects.filter(
            worktimecommitment__family=self.family,
            date__gte=self.start_date,
            date__lte=self.end_date)
        self.available_shifts = main.models.ShiftInstance.objects.filter(
            date__range=(self.start_date, self.end_date),
            shift__in=self.family.shifts).filter(
                Q(worktimecommitment=None) | Q(worktimecommitment__family=self.family))
        handler = super().dispatch(request, *args, **kwargs)
        return handler


class MakeWorktimeCommitmentsView(MakeWorktimeCommitmentsMixin,
                                  HolidayMixin,
                                  main.models.ClassroomWorktimeMixin,
                                  CalendarMixin,
                                  FormView):
    # todo evaluate start_date based on whether mode is monthly
    duration = datetime.timedelta(days=28)
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeFamilyCommitmentsForm

    def get_success_url(self):
        kwargs= {'classroom_slug':self.classroom.slug,
                 'year':self.date.year, 'child_slug': self.family.nickname, 'month':self.date.month, 'day':self.date.day}
        return reverse_lazy('make-worktime-commitments',
                            kwargs=kwargs)

    @property
    def worktimes_struct(self):
        num_weeks = 4
        return list(self.weeks_list(self.start_date, num_weeks))
    # above code resembles monthlyclassroomcalendarview

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({key : getattr(self, key)
                      for key in ['family',
                                  'start_date',
                                  'end_date',
                                  'existing_commitments',
                                  'available_shifts'
]})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        # data = {}
        data = {str(si.pk): (si in self.existing_commitments)
                for si in self.available_shifts}
# move shift_instances from form to view?
        initial.update(data)
        return initial

    def form_valid(self, form):
        to_add = form.shifts_to_add()
        to_remove = form.shifts_to_remove()
        form.revise_commitments(to_add, to_remove)
        message1 = f"shifts added: {to_add}"
        messages.add_message(self.request, messages.SUCCESS, message1)
        message2 = f"shifts removed: {to_remove}"
        messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)




