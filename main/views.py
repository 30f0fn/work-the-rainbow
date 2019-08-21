# 2450

import ast
import datetime
import calendar
import itertools
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict, namedtuple
from itertools import chain


from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, FormView, UpdateView, RedirectView, DetailView, DeleteView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin
from django.utils import timezone
from django.http import HttpResponseRedirect


from rules.contrib.views import PermissionRequiredMixin
from extra_views import ModelFormSetView

from main import rules, scheduling_config
from people.models import Child, Classroom, Role
from people.views import ClassroomMixin, ClassroomEditMixin, ChildEditMixin, ChildMixin, AdminMixin
from main.utilities import nearest_monday
from main.models import Holiday, Happening, Shift, WorktimeCommitment, CareDayAssignment, CareDay, ShiftOccurrence, Period, ShiftPreference, WorktimeSchedule, ShiftAssignable
from main.model_fields import WEEKDAYS
import main.forms

# use instance variables for frequently used attributes whose computation hits the db?

########
# todo #
########

# rescheduling
# workflow for scheduler


class UpcomingEventsMixin(object):
    # needs start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {'events' : self.events(),
                'holidays' : self.holidays()}
        context.update(data)
        return context

    def holidays(self):
        return Holiday.objects.filter(
            start__range = (self.start_date(),
                            self.end_date()))

    def events(self):
        return Happening.objects.filter(
            start__range = (self.start_date(),
                            self.end_date()))


class DateMixin(object):
    
    def date(self):
        # if no year is supplied, return actual date
        # if year but no month or day, return first date of current month
        # if year and month but no day, return first date of specified month
        date = getattr(self, '_date', None)
        if not date:
            if self.kwargs.get('year', None):
                year = self.kwargs.get('year', timezone.now().year)
                month = self.kwargs.get('month', 1)
                day = self.kwargs.get('day', 1)
                date = datetime.date(year, month, day)
            else:
                date = timezone.localdate()
            self._date = date
        return self._date

    @property
    def next_careday_date(self):
        d = self.date()
        while d.weekday() > 4 or\
              Holiday.objects.filter(start__lte=day,
                                     end__gte=day):
            dd += datetime.timedelta(days=1)
        return d



class DateIntervalMixin(DateMixin):

    # todo python3 ABC
    # @abstractmethod
    def start_date(self):
        return self.date()

    # # todo
    # @abstractmethod
    # def end_date(self):
    #     return self.start_date()

    def start(self):
        dt = timezone.datetime.combine(self.start_date(),
                                         timezone.datetime.min.time())
        return timezone.make_aware(dt)

    def end(self):
        dt = timezone.datetime.combine(self.end_date(),
                                         timezone.datetime.max.time())
        return timezone.make_aware(dt)




class CalendarMixin(DateIntervalMixin):

    # todo eliminate these uses of property decorator, they're weird
    
    unit_dict = {'daily':'days', 'weekly':'weeks', 'monthly':'months'}    
    # unit_dict = {'weekly':'weeks', 'monthly':'months'}    
    @property
    def unit(self):
        return self.unit_dict[self.unit_name]

    # @property
    # todo yucky, maybe I don't need it
    def weeks(self):
        return [[(self.start_date() + datetime.timedelta(days=week*7+day))
                 for day in range(5)]
                for week in range(self.num_weeks)]

    def jump_date(self, increment):
        assert(increment != 0)
        sign = 1 if increment > 0 else -1 if increment < 0 else 0
        new_date = self.date() + sign * relativedelta.relativedelta(
            **{self.unit:sign*increment})
        return new_date

    def jump_kwargs(self, increment):
        new_date = self.jump_date(increment)
        kwargs = {'classroom_slug' : self.classroom.slug,
                  'year':new_date.year,
                  'month':new_date.month,
                  'day':new_date.day}
        return kwargs

    def jump_url(self, increment):
        return reverse_lazy(f'{self.view_name}',
                            kwargs=self.jump_kwargs(increment))

    def next(self):
        return self.jump_url(1)

    def previous(self):
        return self.jump_url(-1)




class ClassroomWorktimeMixin(object):
    # requires ClassroomMixin
    # requires the datetimes start and end as bounds of the occurrence dict
    # for this, CalendarMixin is enough

    # todo use just occurrences_for_date_range instead of shifts_dict here
    def shifts_by_week(self):
        shifts = Shift.objects.filter(classroom=self.classroom)\
                            .occurrences_by_date(
                                self.start(), self.end(),
                                include_commitments=True)
        ret = [{date : shifts[date] for date in week}
                for week in self.weeks()]
        # print(f"RET_DICT = {ret}")
        return ret


class PerChildEditWorktimeMixin(object):

    # todo... "available" is kind of a misnomer

    def available_shifts(self):
        shoccs = Shift.objects.filter(classroom=self.classroom)\
                               .occurrences_for_date_range(
                                   self.start(), self.end(),
                                   include_commitments=True)
        ret = [shocc for shocc in shoccs
               if timezone.now() <= shocc.reservation_deadline()]
        return ret


class TimedURLMixin(object):

    @property
    def time(self):
        kwargs = self.kwargs
        return datetime.time(self.kwargs.pop('hour'),
                             self.kwargs.pop('minute'))



class PeriodFromDateMixin(object):
    # needs classroom or child
    def get_period(self):
        try:
            return Period.objects.get(start__date = self.date(),
                                      classroom=self.classroom)
        except AttributeError:
            return Period.objects.get(classroom=self.child.classroom,
                                      date=self.date())

    def get_object(self, *args, **kwargs):
        return self.get_period()




class ScoreWorktimeAttendanceMixin(object):
    
    def post(self, *args, **kwargs):
        reverse_vals = {"completed" : True,
                        "missed" : False,
                        "unmark" : None}
        for wtc in self.get_commitments():
            if f"wtc-{wtc.pk}" in self.request.POST:
                # print(f"found wtc-{wtc.pk} in request.POST")
                val = self.request.POST[f"wtc-{wtc.pk}"]
                # print(val)
                wtc.completed = reverse_vals.get(val, wtc.completed)
                wtc.save()
        # todo below is wrong
        return self.get(*args, **kwargs)
        


############################
# classroom calendar views #
############################


class DefaultCalendarView(RedirectView):
    def get_redirect_url(self, **kwargs):
        return reverse('weekly-classroom-calendar',
                       kwargs = kwargs
        )


class DailyClassroomCalendarView(ClassroomMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 ScoreWorktimeAttendanceMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit_name = 'daily'
    view_name = 'daily-classroom-calendar'

    def get_commitments(self):
        return WorktimeCommitment.objects.filter(
            start__date=self.date(),
            child__classroom=self.classroom).order_by('start')

    def caredays(self):
        # todo FILTER BY CLASSROOM!
        caredays = CareDay.objects.filter(classroom=self.classroom,
                                          weekday=self.start().weekday())
        for careday in caredays:
            yield careday.initialize_occurrence(self.start())


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        data = {
            # 'caredays' : self.caredays_today(),
                'date' : self.date(),
                'classroom' : self.classroom,
                # 'worktimes' : Shift.
                'commitments' : self.get_commitments(),
        }
        context.update(data)
        return context

    def start_date(self):
        return self.date()

    def end_date(self):
        return self.date()





class WeeklyClassroomCalendarView(ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                  CalendarMixin,
                                  ScoreWorktimeAttendanceMixin,
                                  TemplateView):
    template_name = 'weekly_calendar.html'
    unit_name = 'weekly' # for CalendarMixin
    view_name = 'weekly-classroom-calendar'
    num_weeks = 1

    def start_date(self):
        # most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return nearest_monday(self.date())
        # return most_recent_monday

    def end_date(self):
        return self.start_date() + self.num_weeks * datetime.timedelta(days=7)

    def get_commitments(self):
        return WorktimeCommitment.objects.filter(
            child__classroom = self.classroom,
            start__range = (self.start_date(),
                            self.end_date())).order_by('-start')


class MonthlyCalendarMixin(object):
    unit_name = 'monthly' # for CalendarMixin
 
    def weeks(self):
        try:
            return self._weeks
        except AttributeError:
            cal = calendar.Calendar().monthdatescalendar(
                self.date().year, self.date().month)
            self._weeks = [[date for date in week if date.weekday() < 5]
                     for week in cal
                     if week[0].month == self.date().month
                     or week[4].month == self.date().month]
        # print(self._weeks)
        return self._weeks

    def start_date(self):
        return self.weeks()[0][0]

    def end_date(self):
        return self.weeks()[-1][-1]
    


# todo make sure date makes sense 
class MonthlyClassroomCalendarView(MonthlyCalendarMixin,
                                   ClassroomMixin,
                                   ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                   CalendarMixin,
                                   TemplateView):
    template_name = 'monthly_calendar.html'
    view_name = 'monthly-classroom-calendar'



#######################################################
# all homeviews should be based on upcomingeventsview #
#######################################################

# todo maybe some of this should be in people app?

class RedirectToHomeView(RedirectView):
    def get_redirect_url(self, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return user.active_role().get_absolute_url()
        else:
            return reverse('splash')


class SplashView(TemplateView):
    template_name = 'splash.html'


class RoleHomeMixin(LoginRequiredMixin):

    def get(self, *args, **kwargs):
        self.request.user.update_active_role(self.role)
        self.request.user.save()
        return super().get(*args, **kwargs)


class ParentHomeView(UpcomingEventsMixin,
                     CalendarMixin,
                     RoleHomeMixin,
                     TemplateView):
    role, created = Role.objects.get_or_create(name='parent')
    template_name = 'parent_home.html'
    num_weeks = 4
    unit_name = 'weekly'

    def end_date(self):
        return self.start_date() + datetime.timedelta(days=self.num_weeks * 7)
    
    def worktime_commitments(self):
        # today = timezone.now().date(),
        return WorktimeCommitment.objects.filter(
            child__parent_set=self.request.user,
            start__range = (self.start_date(),
                            self.end_date())).select_related(
                                'child__classroom').order_by('start')

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('parent-home',
                            kwargs=kwargs)

    def next(self):
        return self.jump_url(self.num_weeks)

    def previous(self):
        return self.jump_url(-self.num_weeks)


# for teachers with a single classroom; 
# need special handling for multi-classroom teachers
class TeacherHomeView(RoleHomeMixin,
                      RedirectView):
    role, created = Role.objects.get_or_create(name='teacher')

    # todo bug breaks if user teaches in multiple classrooms
    def get_redirect_url(self, *args, **kwargs):
        classrooms = Classroom.objects.filter(
            teacher_set=self.request.user)
        if classrooms.count() >= 1:
            return reverse('daily-classroom-calendar',
                           kwargs = {'classroom_slug' : classrooms.first().slug})
        else:
            return reverse('profile')


    

"""
add/delete classroom
edit people of classroom (students, teachers, schedulers)
create/edit Shifts?  or do that programmatically
"""
class AdminHomeView(RoleHomeMixin,
                    DateIntervalMixin,
                    TemplateView):
    role, created = Role.objects.get_or_create(name='admin')
    template_name = 'admin_home.html'
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # holidays = Holiday.objects.all()
        # happenings = Happening.objects.all()
        # classrooms = Classroom.objects.all()
        context.update({'holidays' : Holiday.objects.all(),
                        'happenings' : Happening.objects.all(),
                        'classrooms' : Classroom.objects.all()})
        return context
# this just handles general time structuring stuff..
# for content, use mixins below





class HolidayCreateView(AdminMixin,
                        CreateView):
    model = Holiday
    template_name = 'generic_create.html'
    fields = ['name', 'start', 'end']

    def get_success_url(self):
        return reverse('admin-home')


class HolidayUpdateView(AdminMixin,
                        UpdateView):
    model = Holiday
    template_name = 'generic_update.html'
    fields = ['name', 'start', 'end']

    def get_success_url(self):
        return reverse('admin-home')


class HolidayDeleteView(AdminMixin,
                        DeleteView):
    model = Holiday
    template_name = 'generic_delete.html'
    
    def get_success_url(self):
        return reverse('admin-home')


class HappeningCreateView(AdminMixin,
                        CreateView):
    model = Happening
    template_name = 'generic_create.html'
    fields = ['name', 'start', 'end']

    def get_success_url(self):
        return reverse('admin-home')


class HappeningUpdateView(AdminMixin,
                          UpdateView):
    model = Happening
    template_name = 'generic_update.html'
    fields = ['name', 'start', 'end']

    def get_success_url(self):
        return reverse('admin-home')


class HappeningDeleteView(AdminMixin,
                        DeleteView):
    model = Happening
    template_name = 'generic_delete.html'

    def get_success_url(self):
        return reverse('admin-home')




################################
# Worktime preference handling # 
################################


# require selection of at least n shifts, for some n fixed by settings
# change form so that the fields are the shift instances and the options are the ranks (rather than vice versa)
class WorktimePreferencesSubmitView(ChildEditMixin,
                                    SingleObjectMixin,
                                    FormView): 

    template_name = 'preferences_submit.html'
    form_class = main.forms.PreferenceSubmitForm
    model = Period

    def get_success_url(self):
        return reverse('child-profile',
                       kwargs={'child_slug' : self.child.slug})

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.shifts = self._shifts()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.shifts = self._shifts()
        return super().post(request, *args, **kwargs)

    def _shifts(self):
        assignments = CareDayAssignment.objects.filter(
            start__lte=self.object.start,
            end__gte=self.object.end,
            child=self.child).select_related('careday')
        print(assignments)
        print([a.careday for a in assignments])
        return list(chain.from_iterable(
            a.careday.shifts() for a in assignments))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['min_shifts'] = scheduling_config.SHIFTPREFERENCE_MIN
        context['shifts'] = self.shifts
        return context

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        extras = {'shifts_dict' : {shift.pk : shift
                                   for shift in self.shifts},
                  'child' : self.child,
                  'period' : self.object,
                  'existing_prefs' : {pref.shift.pk : pref for pref in
                                      kwargs['initial']['existing_prefs']},
                  # 'existing_note' : kwargs['existing_note']
        } 
        kwargs.update(extras)
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        existing_prefs = ShiftPreference.objects.filter(child=self.child,
                                                        period=self.object)
        data = {str(pref.shift.pk) : pref.rank for pref in existing_prefs}
        data.update({'existing_prefs' : existing_prefs})
        initial.update(data)
        # existing_note = ShiftPreferenceNoteForPeriod.objects.filter(
            # period=self.object, child=self.child).first()
        # if existing_note:
            # initial['existing_note'] = existing_note
        return initial

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)




############
# caredays #
############

class CareDayAssignmentsCreateView(ChildEditMixin, FormView):
    form_class = main.forms.CreateCareDayAssignmentsForm
    template_name = 'caredayassignments_create.html'

    def get_success_url(self):
        return reverse('child-profile',
                       kwargs={'child_slug' : self.child.slug})

    def caredays(self):
        return CareDay.objects.filter(classroom=self.child.classroom)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['child'] = self.child
        return kwargs
    
    def form_valid(self, form):
        new_caredays = form.save()
        # message = "thanks! {} {}".format(child=self.child, **new_caredays)
        return super().form_valid(form)


class CareDayAssignmentEditView(ChildEditMixin,
                                UpdateView):
    model = CareDayAssignment
    # fields = ['start','end']
    template_name = 'generic_update.html'
    form_class = main.forms.CareDayAssignmentUpdateForm

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {'start': self.object.start.date(),
                'end': self.object.end.date(),
        }
        initial.update(data)
        return initial

    def get_success_url(self):
        return reverse('child-profile',
                       kwargs={'child_slug' : self.child.slug})


class CareDayAssignmentDeleteView(ChildEditMixin,
                                  DeleteView):
    model = CareDayAssignment
    template_name = 'generic_delete.html'


    def get_success_url(self):
        return reverse('child-profile',
                       kwargs={'child_slug' : self.child.slug})



#######################
# views for scheduler #
#######################


class SchedulerHomeView(RoleHomeMixin,
                        RedirectView):
    role, created = Role.objects.get_or_create(name='scheduler')

    # todo bug breaks if user schedules in multiple classrooms
    def get_redirect_url(self, *args, **kwargs):
        return reverse('profile')


# class SchedulerHomeView(RoleHomeMixin,
#                         DateIntervalMixin,
#                         TemplateView):
#     role, created = Role.objects.get_or_create(name='scheduler')
#     # todo similar issue as with teacher... what if person is scheduler to multiple classrooms?
    
#     template_name = 'scheduler_home.html'

#     @property
#     def classroom(self):
#         return self.request.user.classrooms.first()


# todo is this the correct inheritance order?
class SchedulerCalendarView(ClassroomWorktimeMixin,
                            MonthlyCalendarMixin,
                            CalendarMixin,
                            ClassroomEditMixin,
                            TemplateView):

    template_name = 'scheduler_calendar.html'
    view_name = 'scheduler-calendar'




# # todo is this the correct inheritance order?
# class FourWeekSchedulerCalendarView(ClassroomEditMixin,
#                                     ClassroomWorktimeMixin,
#                                     CalendarMixin,
#                                     TemplateView):

#     num_weeks = 4
#     template_name = 'scheduler_calendar.html'
#     unit_name = 'weekly'
    

#     # todo break period into three four-week sections, show active section
#     @property
#     def start_date(self):
#         most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
#         return most_recent_monday
    
#     @property
#     def end_date(self):
#         return self.start_date() + self.num_weeks * datetime.timedelta(days=7)


#     def jump_url(self, increment):
#         new_date = self.jump_date(increment)
#         kwargs= {'classroom_slug' : self.classroom.slug,
#                  'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
#         return reverse_lazy('scheduler-calendar',
#                             kwargs=kwargs)
 
#     def next(self):
#         return self.jump_url(4)

#     def previous(self):
#         return self.jump_url(-4)





# todo is this the correct inheritance order?
class MakeWorktimeCommitmentsView(MonthlyCalendarMixin,
                                  ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  CalendarMixin,
                                  ChildEditMixin,
                                  PerChildEditWorktimeMixin,
                                  FormView):
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeChildCommitmentsForm
    view_name = 'make-worktime-commitments' # for MonthlyCalendarMixin

    def get_success_url(self, *args, **kwargs):
        return self.request.path

    def jump_kwargs(self, increment):
        kwargs = super().jump_kwargs(increment)
        kwargs.update({'child_slug' : self.child.slug})
        return kwargs

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        sh_occ_deserializer = {sh_occ.serialize() : sh_occ
                               for sh_occ in self.available_shifts()}
        kwargs.update({'child' : self.child,
                       'sh_occ_deserializer' : sh_occ_deserializer,
        })
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {sh_occ.serialize() :
                getattr(sh_occ.commitment, 'child', None) == self.child 
                for sh_occ in self.available_shifts()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)



class EditWorktimeCommitmentsForParentByMonth(MakeWorktimeCommitmentsView):
    template_name = 'monthly_edit_worktime_commitments.html'

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'child_slug' : self.child.slug,
            'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('edit-worktimecommitments-for-parent-by-month',
                            kwargs=kwargs)



class EditWorktimeCommitmentView(ClassroomMixin,
                                 CalendarMixin,
                                 ClassroomWorktimeMixin,
                                 PerChildEditWorktimeMixin,
                                 ChildEditMixin,
                                 UpdateView):

    template_name = 'weekly_edit_worktime_commitment.html'
    model = WorktimeCommitment
    form_class = main.forms.EditWorktimeCommitmentForm
    view_name = 'edit-worktime-commitment' # for MonthlyCalendarMixin
    unit_name = 'weekly'
    num_weeks = 1

    def date(self):
        if 'day' not in self.kwargs:
            return self.commitment().date
        else:
            return super().date()

    def start_date(self):
        # most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return nearest_monday(self.date())
        # return most_recent_monday

    def end_date(self):
        return self.start_date() + self.num_weeks * datetime.timedelta(days=6)

    def commitment(self):
        return self.object
        
    def get_success_url(self, *args, **kwargs):
        return reverse('parent-home')
        # return reverse('weekly-classroom-calendar',
        #                kwargs={'classroom_slug' : self.classroom.slug,
        #                        'year' : self.date().year,
        #                        'month' : self.date().month,
        #                        'day' : self.date().day})

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        sh_occ_deserializer = {sh_occ.serialize() : sh_occ
                               for sh_occ in self.available_shifts()}
        kwargs.update({'sh_occ_deserializer' : sh_occ_deserializer,
        })
        kwargs['user'] = self.request.user
        # kwargs.update({'commitment' : self.commitment})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        availabilities = {sh_occ.serialize() :
                          getattr(sh_occ.commitment, 'child', None) == self.child 
                          for sh_occ in self.available_shifts()}
        initial.update(availabilities)
        return initial

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs = self.kwargs.copy()
        kwargs.update({'pk' : self.commitment().pk,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day
        })
        return reverse_lazy(self.view_name,
                            kwargs=kwargs)





class PeriodListView(ClassroomMixin,
                     ListView):
    model = Period
    template_name = 'periods.html'
    
    def get_queryset(self):
        return Period.objects.filter(classroom=self.classroom).order_by('-start')


   


class PeriodDetailView(ClassroomMixin,
                       DetailView):
    model = Period

    


class PeriodUpdateView(ClassroomEditMixin,
                       DateMixin,
                       UpdateView):
    model = Period
    template_name = 'generic_update.html'
    form_class = main.forms.PeriodForm

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['classroom'] = self.classroom
        return kwargs

    def get_success_url(self):
        return reverse('manage-period',
                       kwargs = {'classroom_slug' : self.classroom.slug,
                                 'pk' : self.object.pk})


class PeriodDeleteView(ClassroomEditMixin,
                       DeleteView):
    model = Period
    template_name = 'generic_delete.html'


class PeriodCreateView(ClassroomEditMixin,
                       CreateView):
    # todo default start_date should be next careday after latest end_date of all existing period
    # todo require periods not overlap
    model = Period
    template_name = 'generic_create.html'
    form_class = main.forms.PeriodForm

    def get_success_url(self):
        return reverse('list-periods',
                       kwargs = {'classroom_slug' : self.classroom.slug})

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        latest_period = Period.objects.filter(
            classroom=self.classroom).order_by('start').last()
        if latest_period:
            new_start = latest_period.end.date() + datetime.timedelta(days=1)
            new_end = new_start + Period.DEFAULT_LENGTH - datetime.timedelta(days=1)
        data = {'start' : new_start, 'end' : new_end}
        initial.update(data)
        return initial



    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['classroom'] = self.classroom
        return kwargs


class ClearScheduleForPeriodView(ClassroomMixin,
                                 DetailView):
    model = Period

    def get_success_url(self):
        return reverse('manage-period',
                       kwargs = {'classroom_slug' : self.classroom.slug,
                                 'pk' : self.object.pk})

    def post(self, request, *args, **kwargs):
        if 'clear' in self.request.POST:
            period = self.get_object()
            period.clear_commitments()
        return super().post(request, *args, **kwargs)
            
            



class PreferencesSolicitView(ClassroomEditMixin,
                             SingleObjectMixin,
                             FormView):
    model = Period

class PreferencesNagView(ClassroomEditMixin,
                         SingleObjectMixin,
                         FormView):
    model = Period



class PreferencesView(ClassroomEditMixin,
                      DateMixin,
                      TemplateView):
    """
    for each child, display preferences and note
    upon get, generate shiftassignables and number of all solutions
    for each assignable, include button which, upon submission, toggles is_active setting and regenerates the solutions
    """
    template_name = 'preferences_for_scheduler.html'


    def get(self, request, *args, **kwargs):
        self.period = Period.objects.get(pk=self.kwargs.get('pk'))
        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        ret = self.get(*args, **kwargs)
        # reverse_vals = {"deactivate" : False,
                        # "activate" : True}
        try:
            posted_val = self.request.POST['update-assignable']
        except KeyError:
            return super().get(*args, **kwargs)
        action_dict = ast.literal_eval(posted_val)
        preference = ShiftPreference.objects.get(pk=action_dict['pref'])
        offset = int(action_dict['offset'])
        value = action_dict['value']
        if action_dict['value'] == 'deactivate':
            preference.deactivate_offset(offset)
        else:
            preference.activate_offset(offset)
        preference.save()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

        # print(self.request.POST)        
        # for assignable in ShiftAssignable.objects.filter(
        #     preference__period=self.period):
        #     if f"assignable-{assignable.pk}" in self.request.POST:
        #         print(f"found assignable-{assignable.pk}")
        #         print(f"assignable is {'not' if not assignable.is_active else ''} active before change")
        #         val = self.request.POST[f"assignable-{assignable.pk}"]
        #         print(f"new_val = {val}")
        #         assignable.is_active = reverse_vals.get(val, assignable.is_active)
        #         assignable.save()
        #         print(f"assignable is {'not' if not assignable.is_active else ''} active after save")
        # context = self.get_context_data(**kwargs)
        # return self.render_to_response(context)

    def solutions_exist(self):
        # return 0
        schedule_iter = WorktimeSchedule.generate_solutions(
            period=self.period)
        try:
            next(schedule_iter)
            return True
        except StopIteration:
            return False


    def weekdays(self):
        return WEEKDAYS


    def shifts_by_weekday(self):
        # prefs = self.prefs_by_shift()
        shifts = Shift.objects.filter(classroom=self.classroom)
        return {weekday :
                {shift for shift in shifts if shift.weekday==weekday}
                for weekday in WEEKDAYS}

    def prefs_by_shift_and_status(self):
        """for each shift, return by_status namedtuple, 
        with active field mapping prefs to their active assignables, 
        and inactive field mapping prefs to inactive assignables"""
        prefs_by_status_init = lambda : namedtuple(
            'PrefsByStatus', 'active inactive')({}, {})
        ret = defaultdict(prefs_by_status_init)
        for pref in ShiftPreference.objects.filter(period=self.period):
            by_status_from_pref = pref.assignables_by_status()
            if by_status_from_pref.active:
                ret[pref.shift].active[pref] = by_status_from_pref.active
            if by_status_from_pref.inactive:
                ret[pref.shift].inactive[pref] = by_status_from_pref.inactive
        return ret

    def prefs_data(self):
        prefs_dict = self.prefs_by_shift_and_status()
        return {weekday : {shift : prefs_dict[shift] for shift in shifts}
                for weekday, shifts in self.shifts_by_weekday().items()}




class GeneratedSchedulesView(ClassroomEditMixin,
                             TemplateView):

    BATCH_SIZE = 10
    template_name = 'generated_schedules.html'
    model = Period
    
    def period(self):
        try:
            return self._period
        except AttributeError:
            self._period = get_object_or_404(Period, 
                                 pk=self.kwargs.get('period_pk'))
            return self._period

    def num_requested(self):
        return self.kwargs.get('num_requested', self.BATCH_SIZE)

    def _build_schedules(self):
        if not hasattr(self, '_schedules'):
            sched_iter = WorktimeSchedule.generate_schedules(
                period=self.period())
            self._schedules = list(itertools.islice(
                sched_iter, 0, self.num_requested()))
            try:
                next(sched_iter)
                self._more_exist = True
            except StopIteration:
                self._more_exist = False

    def more_exist(self):
        try:
            return self._more_exist
        except AttributeError:
            self._build_schedules()
            return self._more_exist

    def schedules(self):
        try:
            return self._schedules
        except AttributeError:
            self._build_schedules()
            return self._schedules

    # def grouper(iterable, n):
    #     """https://docs.python.org/3/library/itertools.html#itertools-recipes"""
    #     args = [iter(iterable)] * n
    #     return itertools.zip_longest(*args)

    # def schedule_groups(self):
    #     return enumerate(grouper(self.schedules(), 10))

    def get_success_url(self):
        return reverse('scheduler-calendar',
                       kwargs={'classroom_slug' :
                               self.classroom.slug})

    def post(self, request, *args, **kwargs):
        schedule_data = self.request.POST['commit']
        schedule = WorktimeSchedule.deserialize(schedule_data)
        schedule.commit()
        return HttpResponseRedirect(self.get_success_url())



class ShiftAssignmentDetailView(ClassroomEditMixin,
                                DetailView):
    model = Period
    # link to generate commitments from ShiftAssignment




# misquamicut
# ashtanga

# todo is this the correct inheritance order?
# todo I think this is not in use
class FourWeekMakeWorktimeCommitmentsView(MonthlyCalendarMixin,
                                          ClassroomEditMixin,
                                          ClassroomWorktimeMixin,
                                          CalendarMixin,
                                          ChildEditMixin,
                                          PerChildEditWorktimeMixin,
                                          FormView):
    # todo evaluate start_date based on whether mode is monthly
    num_weeks = 4
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeChildCommitmentsForm
    unit_name = 'weekly'

    def form():
        return self.form_class()

    # this makes sense only if link sends to first day of month
    # else, try to extract this from a period
    def start_date(self):
        most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
        return most_recent_monday
    
    def end_date(self):
        return self.start_date() + self.num_weeks * datetime.timedelta(days=7)

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'child_slug' : self.child.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('make-worktime-commitments',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(self.num_weeks)

    def previous(self):
        return self.jump_url(-self.num_weeks)


    def get_success_url(self):
        return self.request.path

    # todo mimic prefsubmitview
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'child' : self.child,
                       'available_shifts' : self.available_shifts()
        })
        return kwargs

    # todo
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {sh.serialize() : getattr(sh.commitment, 'child', None) == self.child 
                for sh in self.available_shifts()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.revise_commitments()
        added_repr = ', '.join([str(sh) for sh in revisions['added']])
        if added_repr:
            message1 = "shifts added: "+ added_repr
            messages.add_message(self.request, messages.SUCCESS, message1)
        removed_repr = ', '.join([str(sh) for sh in revisions['removed']])
        if removed_repr:
            message2 = "shifts removed: "+ ', '.join([str(sh) for sh in revisions['removed']])
            messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)


#####################
# views for teacher #
#####################


class _BaseWorktimeAttendanceView(ClassroomEditMixin,
                                  ScoreWorktimeAttendanceMixin,
                                  TemplateView):

    # form_class = main.forms.WorktimeAttendanceForm    
    template_name = 'worktime_attendance.html'
    permission_required = 'main.score_worktime_attendance'

    def get_commitments(self):
        return WorktimeCommitment.objects.filter(
            child__classroom = self.classroom)

    def get_success_url(self, *args, **kwargs):
        return self.request.path

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["commitments"] = self.get_commitments()
        return context
 

class WorktimeAttendanceByMonthView(MonthlyCalendarMixin,
                                    CalendarMixin,
                                    _BaseWorktimeAttendanceView):

    view_name = 'worktime-attendance-by-month'

    def get_commitments(self):
        return super().get_commitments().filter(
            start__month=(self.date().month)).order_by('-start')

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs = self.kwargs.copy()
        kwargs.update({
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day
        })
        return reverse_lazy(self.view_name,
                            kwargs=kwargs)




# class WorktimeAttendanceByDateView(DateIntervalMixin,
#                                    BaseWorktimeAttendanceView):

#     def get_commitments(self):
#         return WorktimeCommitment.objects.filter(
#             child__classroom=self.classroom,
#             start__date=self.date())


# class WorktimeAttendanceByChildView(ChildMixin,
#                                     _BaseWorktimeAttendanceView):

#     # def period(self):
#         # kwargs=self.kwargs
#         # return Period.objects.get(pk=int(self.kwargs.get('period_pk')))

#     def get_commitments(self):
#         return super().get_commitments().filter(
#             child=self.child,
#             start__range=(self.date())
#         )








# for each commitment wtc returned in view's get_commitments' methodd:
    # support "mark as complete", "mark as incomplete", "unmark"
    # do this 

