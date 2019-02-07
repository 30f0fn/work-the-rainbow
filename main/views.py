import datetime
import calendar
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView, RedirectView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin

from rules.contrib.views import PermissionRequiredMixin

from main import rules
from people.models import Child, Classroom, teacher_role, scheduler_role, parent_role, admin_role
from people.views import ClassroomMixin, ClassroomEditMixin
import main.utilities
import main.models
import main.forms

# use instance variables for frequently used attributes whose computation hits the db?

# def method_with_setters(method, **properties):
#     def new_method(self, *args, **kwargs):
#         for key, value in properties.items():
#             if key not in dir(self):
#                 setattr(self, key, value)
#         getattr(self.__class__.mro()[1], method)(self, *args, **kwargs)
#     return new_method


# def dispatch_with_setters(**items):
#     return method_with_setters('dispatch', **items)




########
# todo #
########

# rescheduling
# workflow for scheduler


class UpcomingEventsMixin(object):
    # template_name = "upcoming_for_user.html"
    def date_range(self):
        today = datetime.datetime.now().date()
        return (today, today+datetime.timedelta(weeks=4))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {'events' : self.events(),
                'holidays' : self.holidays()}
        context.update(data)
        return context

    def holidays(self):
        return main.models.Holiday.objects.filter(
            start_date__range = self.date_range())

    def worktime_commitments(self):
        today = datetime.datetime.now().date(),
        return main.models.ShiftInstance.objects.filter(
            commitment__parent_set=self.request.user,
            date__range = self.date_range()).select_related(
                'classroom', 'commitment')

    def events(self):
        return main.models.Happening.objects.filter(
            start_date__range = self.date_range())



class CalendarMixin(object):
    unit_dict = {'daily':'days', 'weekly':'weeks', 'monthly':'months'}    

    @property
    def unit(self):
        return self.unit_dict[self.unit_name]

    @property
    def date(self):
        try:
            return self._date
        except AttributeError:
            try:
                self._date = datetime.date(self.kwargs.pop('year'),
                                     self.kwargs.pop('month'),
                                     self.kwargs.pop('day'))
                print(f"got date {self._date} from URL!")
            except KeyError:
                print("failed to get date from URL!!!")
                self._date = datetime.datetime.now().date()
        return self._date

    @property
    def weeks(self):
        return [[(self.start_date + datetime.timedelta(days=week*7+day))
                 for day in range(5)]
                for week in range(self.num_weeks)]

    def jump_date(self, increment):
        assert(increment != 0)
        sign = 1 if increment > 0 else -1 if increment < 0 else 0
        new_date = self.date + sign * relativedelta.relativedelta(
            **{self.unit:sign*increment})
        return new_date

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy(f'{self.unit_name}-classroom-calendar',
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


class ShiftsByDayMixin(object):

    def shifts_by_day(self):
        shifts_dict = defaultdict(list)
        for si in self.shifts():
            shifts_dict[si.date].append(si)
        return shifts_dict
    

class ShiftsByWeekMixin(ShiftsByDayMixin):
    # for weekly, monthly, and period calendars
    # requires self.date (e.g. from CalendarMixin)
    # needs self.num_weeks (e.g. as class variable of MonthlyCalendarView)

    def shifts_by_week(self):
        return [{day: self.shifts_by_day()[day] for day in week}
                for week in self.weeks]


# not in use
# use dispatch-overriding technique?
class HolidayMixin(object):

    @property
    def holidays(self):
        return main.models.Holiday.objects.filter(
            classroom=classroom,
            start_date__gte=self.date,
            end_date__lte=self.date+datetime.timedelta(years=1))


class ClassroomWorktimeMixin(object):
    # requires ClassroomMixin
    # requires view attributes start_date and end_date

    def shifts(self):
        return main.models.ShiftInstance.objects.filter(
            classroom=self.classroom,
            date__gte=self.start_date,
            date__lte=self.end_date).select_related('commitment')

class FamilyMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.family = Child.objects.get(classroom=self.classroom,
                                        nickname=self.kwargs.get('child_slug'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'family' : self.family})
        return context
        


class PerFamilyEditWorktimeMixin(object):
    # requires shifts e.g. from ClassroomWorktimeMixin 
    def available_shifts(self):
        tomorrow = datetime.datetime.now()+datetime.timedelta(days=1)
        return self.shifts().all().filter(
            Q(commitment=None) | Q(commitment=self.family),
            shift__in=self.family.shifts,
            date__gte=tomorrow)


class TimedURLMixin(object):

    @property
    def time(self):
        kwargs = self.kwargs
        return datetime.time(self.kwargs.pop('hour'),
                             self.kwargs.pop('minute'))






############################
# classroom calendar views #
############################


class DailyClassroomCalendarView(ClassroomMixin,
                                 ClassroomWorktimeMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit_name = 'daily'

    @property
    def start_date(self):
        return self.date

    @property
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
    unit_name = 'weekly' # for CalendarMixin
    num_weeks = 1 # for WeekApportioningMixin

    @property
    def start_date(self):
        # print("computing start date")
        most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return most_recent_monday

    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)


class MonthlyClassroomCalendarView(ClassroomMixin,
                                   ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                   CalendarMixin,
                                   # WeekApportioningMixin,
                                   ShiftsByWeekMixin,
                                   TemplateView):
    template_name = 'monthly_calendar.html'
    unit_name = 'monthly' # for CalendarMixin

    @property
    def num_weeks(self):
        return len(calendar.monthcalendar(self.date.year, self.date.month))

    @property
    def start_date(self):
        first_of_month = datetime.date(self.date.year, self.date.month, 1)
        most_recent_monday = first_of_month - datetime.timedelta(days = first_of_month.weekday())
        return most_recent_monday

    @property
    def end_date(self):
        return self.start_date + datetime.timedelta(days = 7 * self.num_weeks - 1)
            











#######################################################
# all homeviews should be based on upcomingeventsview #
#######################################################

class RedirectToHomeView(RedirectView):
    def get_redirect_url(self, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return reverse(f'{user.active_role()}-home')
        else:
            return reverse('splash')


class SplashView(TemplateView):
    template_name = 'splash.html'


class RoleHomeView(LoginRequiredMixin, TemplateView):

    def get(self, *args, **kwargs):
        self.request.user.active_role = self.role
        self.request.user.save()
        return super().get(*args, **kwargs)


class ParentHomeView(RoleHomeView):
    role = parent_role
    template_name = 'parent_home.html'

    def worktime_commitments(self):
        today = datetime.datetime.now().date(),
        return main.models.ShiftInstance.objects.filter(
            commitment__parent_set=self.request.user,
            date__range = self.date_range()).select_related(
                'classroom', 'commitment')


# for teachers with a single classroom; 
# need special handling for multi-classroom teachers
class TeacherHomeView(ShiftsByDayMixin, RoleHomeView):
    role = teacher_role
    template_name = 'teacher_home.html'

    # todo: add data to context?
    # todo make this an instance-attribute rather than a method
    @property
    def classroom(self):
        return self.request.user.classrooms.first()

    def shifts(self):
        return main.models.ShiftInstance.objects.filter(date=self.date)


    # add to instance variables
    @property
    def date(self):
        day = datetime.datetime.now().date()
        while day.weekday() > 4 or\
              main.models.Holiday.objects.filter(start_date__lte=day,
                                                end_date__gte=day):
            day += datetime.timedelta(days=1)
        return day

    def caredays_today(self):
        return main.models.CareDayAssignment.objects.filter(
            weekday = self.date.weekday(),
            child__classroom = self.classroom
        ).select_related('child')

    def get_context_data(self):
        context = super().get_context_data()
        data = {'caredays' : self.caredays_today(),
                'date' : self.date,
                'classroom' : self.classroom,
                'shifts' : self.shifts()}
        context.update(data)
        return context


class SchedulerHomeView(RoleHomeView):
    role = scheduler_role

    template_name = 'scheduler_home.html'

    
class AdminHomeView(RoleHomeView):
    role = admin_role

    template_name = 'admin_home.html'
    

# this just handles general time structuring stuff..
# for content, use mixins below











#########################
# family calendar views #
#########################



class EditWorktimeCommitmentView(ClassroomEditMixin,
                                 ClassroomWorktimeMixin,
                                 CalendarMixin,
                                 ShiftsByWeekMixin,
                                 FamilyMixin,
                                 PerFamilyEditWorktimeMixin,
                                 TimedURLMixin,
                                 FormView):
    permission_required = 'people.edit_child'
    form_class = main.forms.RescheduleWorktimeCommitmentForm
    num_weeks = 4
    template_name = 'reschedule_worktime_commitment.html'

    @property
    def start_date(self):
        monday_before_today = datetime.datetime.now().date() - \
                              datetime.timedelta(days = self.date.weekday())
        monday_before_commitment = self.date - \
                                   datetime.timedelta(days = self.date.weekday())
        return max(monday_before_commitment - datetime.timedelta(weeks = 1),
                   monday_before_today)

    @property
    def end_date(self):
        monday_before_commitment = self.date - \
                                   datetime.timedelta(days = self.date.weekday())
        return monday_before_commitment + datetime.timedelta(weeks = 2)

    @property
    def num_weeks(self):
        return (self.end_date - self.start_date).days // 7

    @property
    def shift_instance(self):
        si = getattr(self, '_shift_instance', None)
        if not si:
            self._shift_instance = main.models.ShiftInstance.objects.get(
                classroom=self.classroom,
                date=self.date,
                start_time=self.time)
        return self._shift_instance

    def available_shifts(self):
        return super().available_shifts() | main.models.ShiftInstance.objects.filter(
            pk=self.shift_instance.pk)

    def get_success_url(self):
        return reverse('upcoming')

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'family' : self.family,
                       'current_shift' : self.shift_instance,
                       'available_shifts' : self.available_shifts()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {'new_shift': self.shift_instance}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.execute()
        if revisions:
            message = "thanks! we rescheduled {family}'s worktime commitment from {removed} to {added}".format(family=self.family, **revisions)
            messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)


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




#######################
# views for scheduler #
#######################

# outer view for scheduler
class SchedulerView(TemplateView):
    pass


# this order is a bit backward, should be specific to general
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
    unit_name = 'weekly'

    # this makes sense only if link sends to first day of month
    # else, try to extract this from a period
    @property
    def start_date(self):
        # print("computing start date")
        most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return most_recent_monday
    
    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'child_slug' : self.family.nickname,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy(f'make-worktime-commitments',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(4)

    def previous(self):
        return self.jump_url(-4)


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
        message1 = f"shifts added: {', '.join({revisions['added']})}"
        messages.add_message(self.request, messages.SUCCESS, message1)
        message2 = f"shifts removed: {', '.join({revisions['removed']})}"
        messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)




