import datetime
import calendar
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict


from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q

from rules.contrib.views import PermissionRequiredMixin

from main import rules
from people.models import Child, Classroom
from people.views import ClassroomMixin, ClassroomEditMixin
import main.utilities
import main.models
import main.forms


def method_with_setters(method, **properties):
    def new_method(self, *args, **kwargs):
        for key, value in properties.items():
            if key not in dir(self):
                setattr(self, key, value)
        getattr(self.__class__.mro()[1], method)(self, *args, **kwargs)
    return new_method


def dispatch_with_setters(**items):
    return method_with_setters('dispatch', **items)


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
    unit_dict = {'daily':'days', 'weekly':'weeks', 'monthly':'months'}    

    def instance_vars(self):
        try:
            date = datetime.date(self.kwargs.pop('year'),
                                 self.kwargs.pop('month'),
                                 self.kwargs.pop('day'))
        except KeyError:
            date = datetime.datetime.now().date()
        unit_name = self.kwargs.pop('unit_name', 'weekly')
        unit = self.unit_dict[unit_name] # for CalendarMixin
        if unit == 'days':
            num_weeks = 0
            start_date = date
            end_date = start_date
        elif unit == 'weeks':
            num_weeks = 1
            most_recent_monday = date -\
                                 datetime.timedelta(days = date.weekday())
            start_date = most_recent_monday
            end_date = start_date +\
                            num_weeks * datetime.timedelta(days=7)
        else:
            assert(unit=='months')
            num_weeks = len(calendar.monthcalendar(date.year, date.month))
            first_of_month = datetime.date(date.year, date.month, 1)
            previous_monday = first_of_month -\
                              datetime.timedelta(days = first_of_month.weekday())
            start_date = previous_monday
            end_date = start_date +\
                            datetime.timedelta(days = 7 * num_weeks - 1)
        weeks = [[(start_date + datetime.timedelta(days=week*7+day))
                       for day in range(5)]
                      for week in range(num_weeks)]
        return locals()

    def dispatch(self, request, *args, **kwargs):
        return dispatch_with_setters(**self.instance_vars())(
            self, request, *args, **kwargs)

    # def dispatch(self, request, *args, **kwargs):
    #     try:
    #         self.date = datetime.date(self.kwargs.pop('year'),
    #                                   self.kwargs.pop('month'),
    #                                   self.kwargs.pop('day'))
    #     except TypeError:
    #         self.date = datetime.datetime.now().date()
    #     self.unit_name = self.kwargs.pop('unit_name', 'weekly')
    #     self.unit = self.unit_dict[self.unit_name] # for CalendarMixin
    #     if self.unit == 'days':
    #         self.num_weeks = 0
    #         self.start_date = self.date
    #         self.end_date = self.start_date
    #     elif self.unit == 'weeks':
    #         self.num_weeks = 1
    #         most_recent_monday = self.date -\
    #                              datetime.timedelta(days = self.date.weekday())
    #         self.start_date = most_recent_monday
    #         self.end_date = self.start_date +\
    #                         self.num_weeks * datetime.timedelta(days=7)
    #     else:
    #         self.num_weeks = len(calendar.monthcalendar(self.date.year, self.date.month))
    #         first_of_month = datetime.date(self.date.year, self.date.month, 1)
    #         previous_monday = first_of_month -\
    #                           datetime.timedelta(days = first_of_month.weekday())
    #         self.start_date = previous_monday
    #         self.end_date = self.start_date +\
    #                         datetime.timedelta(days = 7 * self.num_weeks - 1)
    #     self.weeks = [[(self.start_date + datetime.timedelta(days=week*7+day))
    #                    for day in range(5)]
    #                   for week in range(self.num_weeks)]
    #     return super().dispatch(request, *args, **kwargs)



    def jump_date(self, increment):
        assert(increment != 0)
        sign = 1 if increment > 0 else -1 if increment < 0 else 0
        date = self.date + sign * relativedelta.relativedelta(**{self.unit:1})
        return date

    def jump_url(self, increment):
        date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'unit_name' : self.unit_name,
                 'year':date.year, 'month':date.month, 'day':date.day}
        return reverse_lazy(f'classroom-calendar',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(1)

    def previous(self):
        return self.jump_url(-1)


# class WeekApportioningMixin(object):
#     # for weekly, monthly, and period calendars
#     # requires self.date (e.g. from CalendarMixin)
#     # needs self.num_weeks (e.g. as class variable of MonthlyCalendarView)
    
    # def dispatch(self, request, *args, **kwargs):
    #     self.weeks = [[(self.start_date() + datetime.timedelta(days=week*7+day))
    #                    for day in range(5)]
    #                   for week in range(self.num_weeks)]
    #     return super().dispatch(request, *args, **kwargs)


class ShiftsByWeekMixin(object):
    # for weekly, monthly, and period calendars
    # requires self.date (e.g. from CalendarMixin)
    # needs self.num_weeks (e.g. as class variable of MonthlyCalendarView)
    
    def dispatch(self, request, *args, **kwargs):
        shifts_by_day = defaultdict(list)
        for si in self.shifts():
            shifts_by_day[si.date].append(si)
        self.shifts_by_week = [{day: shifts_by_day[day] for day in week}
                               for week in self.weeks]
        return super().dispatch(request, *args, **kwargs)


# not in use
# use dispatch-overriding technique?
class HolidayMixin(object):
    @property
    def holidays(self):
        return main.models.Holiday.objects.filter(
            classroom=classroom,
            date__gte=self.start_date,
            date__lte=self.end_date)


class ClassroomWorktimeMixin(object):
    # requires ClassroomMixin

    # invoked to evaluate shifts_by_day, available_shifts
    def shifts(self):
        return main.models.ShiftInstance.objects.filter(
            classroom=self.classroom,
            date__gte=self.start_date,
            date__lte=self.end_date).select_related('commitment')

    def dumb_dict(self):
        d = defaultdict(list)
        d[datetime.datetime.now().date()] = 123454321
        return d

    # maybe better a class method?
    @property # invoked in template
    def shifts_by_day(self):
        d = dict()
        for si in self.shifts():
            if si.date in d:
                d[si.date].append(si)
            else:
                d[si.date] = [si]
        return d


class FamilyMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.family = Child.objects.get(classroom=self.classroom,
                                        nickname=self.kwargs.get('child_slug'))
        return super().dispatch(request, *args, **kwargs)


class PerFamilyEditWorktimeMixin(object):
    # requires shifts e.g. from ClassroomWorktimeMixin 
    def dispatch(self, request, *args, **kwargs):
        self.available_shifts = self.shifts().all().filter(
            Q(commitment=None) | Q(commitment=self.family),
            shift__in=self.family.shifts)
        return super().dispatch(request, *args, **kwargs)


############################
# classroom calendar views #
############################

class ClassroomCalendarView(ClassroomMixin,
                            ClassroomWorktimeMixin,
                            # HolidayMixin,
                            CalendarMixin,
                            # WeekApportioningMixin,
                            ShiftsByWeekMixin,
                            TemplateView):

    def get_template_names(self):
        return [ f'{self.unit_name}_calendar.html']




class DailyClassroomCalendarView(ClassroomMixin,
                                 ClassroomWorktimeMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit = 'days'
    unit_name = 'daily'

    def start_date(self):
        return self.date

    def end_date(self):
        return self.date


class WeeklyClassroomCalendarView(ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                  CalendarMixin,
                                  # WeekApportioningMixin,
                                  ShiftsByWeekMixin,
                                  TemplateView):
    template_name = 'weekly_calendar.html'
    unit = 'weeks' # for CalendarMixin
    unit_name = 'weekly' # for CalendarMixin
    num_weeks = 1 # for WeekApportioningMixin

    def start_date(self):
        # print("computing start date")
        most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return most_recent_monday

    def end_date(self):
        return self.start_date() + self.num_weeks * datetime.timedelta(days=7)


class MonthlyClassroomCalendarView(ClassroomMixin,
                                   ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                   CalendarMixin,
                                   # WeekApportioningMixin,
                                   ShiftsByWeekMixin,
                                   TemplateView):
    template_name = 'monthly_calendar.html'
    unit = 'months' # for CalendarMixin
    unit_name = 'monthly' # for CalendarMixin

    @property
    def num_weeks(self):
        return len(calendar.monthcalendar(self.date.year, self.date.month))

    def start_date(self):
        first_of_month = datetime.date(self.date.year, self.date.month, 1)
        most_recent_monday = first_of_month - datetime.timedelta(days = first_of_month.weekday())
        return most_recent_monday

    def end_date(self):
        return self.start_date() + datetime.timedelta(days = 7 * self.num_weeks - 1)
            

################
# rescheduling #
################

"""
workflow:
link from the commitment to a rescheduling form
form is a weekly calendar, oriented around the to-be-scheduled commitment
on implementation side, it is basically a modelchoicefield 
"""

# # BELOW IS BROKEN!
# # inheritance?
# # below should come from calendarview, mimicking makeworktimecommitmentsview
# class WorktimeCommitmentRescheduleView(LoginRequiredMixin,
#                                        PermissionRequiredMixin,
#                                        FormView):
#     permission_required = 'main.edit_worktimecommitment'
#     # model = main.models.WorktimeCommitment
#     # fields = ['shift_instance']
#     form_class = main.forms.WorktimeCommitmentRescheduleForm
#     template_name = "worktimecommitment_reschedule.html"
#     success_url = reverse_lazy('home')

#     def get_initial(self, *args, **kwargs):
#         raise Exception("broken, refactor without worktimecommitment object")
#         initial = super().get_initial(*args, **kwargs)
#         committed = ShiftI
#         data = {'shift_instance': ShiftInstance.objects}
#         initial.update(data)
#         return initial


#########################
# family calendar views #
#########################

class UpcomingEventsView(LoginRequiredMixin, TemplateView):
    template_name = "upcoming_for_user.html"

    def holidays(self):
        return main.models.Holiday.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))

    def worktime_commitments(self):
        return main.models.ShiftInstance.objects.filter(
            commitment__parent_set=self.request.user)

    def events(self):
        return main.models.Happening.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))


################################
# Worktime preference handling #
################################


# require selection of at least n shifts, for some n fixed by settings
# change form so that the fields are the shift instances and the options are the ranks (rather than vice versa)
class WorktimePreferencesSubmitView(ClassroomEditMixin, FormView): 
    template_name = 'preferences_submit.html'
    form_class = main.forms.PreferenceSubmitForm

    @property
    def child(self):
        return Child.objects.get(nickname=self.kwargs.get('child_slug'),
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


class MakeWorktimeCommitmentsView(ClassroomEditMixin,
                                  ClassroomWorktimeMixin,
                                  CalendarMixin,
                                  # WeekApportioningMixin,
                                  ShiftsByWeekMixin,
                                  FamilyMixin,
                                  PerFamilyEditWorktimeMixin,
                                  FormView):
    # todo evaluate start_date based on whether mode is monthly
    num_weeks = 4
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeFamilyCommitmentsForm

    # this makes sense only if link sends to first day of month
    # else, try to extract this from a period
    def start_date(self):
        # print("computing start date")
        most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return most_recent_monday

    def end_date(self):
        return self.start_date() + self.num_weeks * datetime.timedelta(days=7)

    # post is idempotent so ok to return the same url
    def get_success_url(self):
        return self.request.path

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'family' : self.family,
                       'available_shifts' : self.available_shifts()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        # data = {}
        data = {str(si.pk): si.commitment == self.family 
                for si in self.available_shifts()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.revise_commitments()
        message1 = f"shifts added: ', '.join({revisions['added']})"
        messages.add_message(self.request, messages.SUCCESS, message1)
        message2 = f"shifts removed: ', '.join({revisions['removed']})"
        messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)




class EditWorktimeCommitmentView(ClassroomEditMixin,
                                 ClassroomWorktimeMixin,
                                 CalendarMixin,
                                 ShiftsByWeekMixin,
                                 FamilyMixin,
                                 PerFamilyEditWorktimeMixin,
                                 FormView):
    permission_required = 'people.edit_child'
    form_class = main.forms.MakeFamilyCommitmentsForm


    def dispatch(self, request, *args, **kwargs):
        self.shift_instance = ShiftInstance.objects.get(
            pk=self.kwargs.pop(shiftinstance_pk))
        return super().dispatch(request, *args, **kwargs)

 
    def jump_url(self, increment):
        date = self.jump_date(increment)
        kwargs= {'shift_pk' : self.shift_pk,
                 'unit_name' : self.unit_name,
                 'year' : date.year,
                 'month' : date.month,
                 'day' : date.day}
        return reverse_lazy('edit-worktime-commitments',
                            kwargs=kwargs)

    def get_template_names(self):
        return f'{self.unit_name}_reschedule_worktime_commitments.html'

    def get_success_url(self):
        return self.request.path

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'family' : self.family,
                       'available_shifts' : self.available_shifts})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        # data = {}
        data = {'shift': self.shift_instance}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.revise_commitments()
        message1 = f"shifts added: ', '.join({revisions['added']})"
        messages.add_message(self.request, messages.SUCCESS, message1)
        message2 = f"shifts removed: ', '.join({revisions['removed']})"
        messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)
