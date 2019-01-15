import datetime
import calendar

from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from people.models import Classroom
from people.views import ClassroomMixin
from main.utilities import weeks_for_month
from main.models import FamilyCommitment

"""
calendar views

time divisions:
#  for whole classroom, do these three views:
#    daily/weekly/monthly
#  units-relative-from-today vs by-absolute-unit
#  this mainly applies to weekly; do the former for weekly and latter for monthly

# for user, just give an "upcoming events" view

"""

########
# todo #
########


# permissions

class HomeView(TemplateView):
    template_name = 'home.html'

    
#todo rename BaseCalendarView or Abstract...
# this just handles general time structuring stuff..
# for content, use mixins below
class CalendarView(ListView):
    duration = 0 # in days replace with below, or delete 
    # num_days = 0 
    # define above variable in subclasses
    
    @property
    def year(self):
        return self.kwargs.get('year')

    @property
    def month(self):
        return self.kwargs.get('month', 1)

    @property
    def day(self):
        return self.kwargs.get('day', 1)

    @property
    def start_date(self):
        return datetime.date(self.year, self.month, self.day)

    @property
    def days(self):
        return [self.start_date + datetime.timedelta(days=n)
                for n in range(duration)]

    @property
    def weeks(self):
        return [week_of(self.start_date + datetime.timedelta(days = n * 7))
                for n in self.duration // 7]
    

class HolidayMixin(object):
    @property
    def holidays(self):
        return Holiday.objects.filter(
            classroom=classroom,
            date__gte=self.start_date,
            date__lte=self.start_date+duration)


class WorktimeMixin(object):
    @property
    def worktime_commitments_by_day(self):
        commitments = FamilyCommitment.objects.filter(
            date__gte=self.start_date,
            date__lte=self.start_date+duration)
        dc_dict = {date: [dc for dc in daily_commitments if dc.date==date]
                   for date in [self.start_date + datetime.timedelta(days=i)
                                for i in range(self.duration)]}
        return dc_dict


class ClassroomWorktimeMixin(WorktimeMixin, ClassroomMixin):
    @property
    def worktime_commitments(self):
        return super().worktime_commitments().filter(classroom=self.classroom)


class FamilyWorktimeMixin(WorktimeMixin):
    @property
    def worktime_commitments(self):
        return super().worktime_commitments().filter(family=self.family)


#########################
# family calendar views #
#########################

class UpcomingFamilyEventsView(TemplateView):
    pass


############################
# classroom calendar views #
############################

class DailyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, CalendarView):
    duration = datetime.timedelta(days=1)


class WeeklyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, CalendarView):
    duration = datetime.timedelta(days=7)


class MonthlyClassroomCalendarView(ClassroomWorktimeMixin, HolidayMixin, CalendarView):
    num_days = calendar.monthrange(self.year, self.month)[1]
    duration = datetime.timedelta(days= num_days)

    # this differs from default, because the weekdays not in month are replaced with None
    @property
    def weeks(self):
        return weeks_for_month(self.year, self.month)


################################
# Worktime preference handling #
################################

# create shiftpreference relative to child of user
# should have update_child permission
class PreferencesSubmitView(FormView): 
    form_class = PreferencesSubmitForm
