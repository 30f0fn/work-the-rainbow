import datetime
import calendar
from dateutil import relativedelta

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from people.models import Child
from people.views import ClassroomMixin
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

class BaseCalendarView(TemplateView):
    
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
            date__lte=self.start_date+duration)


############################
# classroom calendar views #
############################

class ClassroomWorktimeMixin(ClassroomMixin):

    def shifts_dict(self, date):
        return {shift_instance:
                shift_instance.worktimecommitment_set.filter(
                    family__classroom=self.classroom).first()
                for shift_instance in main.models.ShiftInstance.objects.filter(date=date)}

    def days_dict(self, start_date, num_days):
        return {date: self.shifts_dict(date)
                for date in [start_date + datetime.timedelta(days=n)
                             for n in range(num_days)]}

    def weeks_list(self, start_date, num_weeks):
        return [self.days_dict(date, 5)
                for date in [start_date + n * datetime.timedelta(days=7)
                             for n in range(num_weeks)]]


class DailyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, BaseCalendarView):
    template_name = 'daily_calendar.html'
    unit = 'days'
    unit_name = 'daily'

    @property
    def start_date(self):
        return self.date

    @property
    def worktimes_struct(self):
        return self.shifts_dict(self.date)



class WeeklyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, BaseCalendarView):
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


    

class MonthlyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, BaseCalendarView):
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




#########################
# family calendar views #
#########################

class UpcomingEventsView(LoginRequiredMixin, TemplateView):
    template_name = "upcoming_for_user.html"

    def holidays(self):
        return main.models.Holiday.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))

    def worktime_commitments(self):
        return main.models.WorktimeCommitment.objects.filter(
            family__parents=self.request.user)

    def events(self):
        return main.models.Happening.objects.filter(
            start_date__lte=datetime.datetime.now()+datetime.timedelta(days=28))
        
    


################################
# Worktime preference handling #
################################

# require selection of at least n shifts, for some n fixed by settings
class PreferencesSubmitView(ClassroomMixin, FormView): 
    template_name = 'preferences_submit.html'
    def get_success_url(self):
        return reverse_lazy('classroom-roster',
                            kwargs={'slug':self.classroom.slug})

    @property
    def child(self):
        return Child.objects.get(nickname=self.kwargs.get('child'),
                                 classroom=self.classroom)

    form_class = main.forms.PreferenceSubmitForm

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
 

