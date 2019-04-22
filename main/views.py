import datetime
import calendar
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict
from itertools import chain

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView, RedirectView, DetailView, DeleteView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin
from django.utils import timezone
from django.http import HttpResponseRedirect

from rules.contrib.views import PermissionRequiredMixin

from main import rules, scheduling_config
from people.models import Child, Classroom, Role
from people.views import ClassroomMixin, ClassroomEditMixin, ChildEditMixin, ChildMixin, AdminMixin
from main.utilities import nearest_monday
from main.models import Holiday, Happening, Shift, WorktimeCommitment, CareDayAssignment, CareDay, ShiftOccurrence, Period, ShiftPreference, ShiftAssignmentCollection
from main.model_fields import WEEKDAYS
import main.forms


# use instance variables for frequently used attributes whose computation hits the db?

########
# todo #
########

# rescheduling
# workflow for scheduler


class UpcomingEventsMixin(object):
    # template_name = "upcoming_for_user.html"
    def date_range(self):
        today = timezone.now().date()
        return (today, today+datetime.timedelta(weeks=4))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {'events' : self.events(),
                'holidays' : self.holidays()}
        context.update(data)
        return context

    def holidays(self):
        return Holiday.objects.filter(
            start__range = self.date_range())

    def events(self):
        return Happening.objects.filter(
            start__range = self.date_range())


class DateMixin(object):
    
    # todo this is called about 748 times per request
    def date(self):
        self.is_dated = 'day' in self.kwargs
        try:
            self._date = datetime.date(self.kwargs.get('year'),
                                       self.kwargs.get('month'),
                                       self.kwargs.get('day'))
        except TypeError:
            self._date = timezone.now().date()
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
    @property
    def start_date(self):
        return self.date()

    # todo
    # @abstractmethod
    @property
    def end_date(self):
        return self.start_date

    @property
    def start(self):
        dt = timezone.datetime.combine(self.start_date,
                                         timezone.datetime.min.time())
        return timezone.make_aware(dt)

    @property
    def end(self):
        dt = timezone.datetime.combine(self.end_date,
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
        return [[(self.start_date + datetime.timedelta(days=week*7+day))
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
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
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

    def shifts_dict(self):
        return Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])

    # todo use just occurrences_for_date_range instead of shifts_dict here
    def shifts_by_week(self):
        shifts = self.shifts_dict()
        return [{date : shifts[date].values() for date in week}
         for week in self.weeks()]



class PerChildEditWorktimeMixin(object):
    # requires shifts e.g. from ClassroomWorktimeMixin 
    # todo this does'nt make sense for the ExitWorktimeCommitmentView

    # todo this should use just occurrences_for_date_range
    def available_shifts(self):
        sh_dict = Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])
        ret =  [sh for day in sh_dict for sh in sh_dict[day].values()
                if sh.is_available_to_child(self.child)]
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



############################
# classroom calendar views #
############################


class DailyClassroomCalendarView(ClassroomMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit_name = 'daily'
    view_name = 'daily-classroom-calendar'

    def commitments(self):
        return WorktimeCommitment.objects.filter(
            start__date=self.date(),
            child__classroom=self.classroom)

    def caredays(self):
        # todo FILTER BY CLASSROOM!
        caredays = CareDay.objects.filter(classroom=self.classroom,
                                          weekday=self.start.weekday())
        for careday in caredays:
            yield careday.initialize_occurrence(self.start)


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        data = {
            # 'caredays' : self.caredays_today(),
                'date' : self.date(),
                'classroom' : self.classroom,
                # 'worktimes' : Shift.
                'commitments' : self.commitments(),
        }
        context.update(data)
        return context

    @property
    def start_date(self):
        return self.date()

    @property
    def end_date(self):
        return self.date()





class WeeklyClassroomCalendarView(ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                  CalendarMixin,
                                  TemplateView):
    template_name = 'weekly_calendar.html'
    unit_name = 'weekly' # for CalendarMixin
    view_name = 'weekly-classroom-calendar'
    num_weeks = 1

    @property
    def start_date(self):
        # most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return nearest_monday(self.date())
        # return most_recent_monday

    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)



class MonthlyCalendarMixin(object):
    unit_name = 'monthly' # for CalendarMixin
 
    def weeks(self):
        cal = calendar.Calendar().monthdatescalendar(
            self.date().year, self.date().month)
        return [[date for date in week if date.weekday() < 5]
                for week in cal
                if week[0].month == self.date().month
                or week[4].month == self.date().month]

    #todo these are redundant
    @property
    def start_date(self):
        return self.weeks()[0][0]

    @property
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
            return reverse(user.active_role.get_absolute_url())
        else:
            return reverse('splash')


class SplashView(TemplateView):
    template_name = 'splash.html'


class RoleHomeMixin(LoginRequiredMixin):

    def get(self, *args, **kwargs):
        self.request.user.active_role = self.role
        self.request.user.save()
        return super().get(*args, **kwargs)


class ParentHomeView(UpcomingEventsMixin,
                     DateIntervalMixin,
                     RoleHomeMixin,
                     TemplateView):
    role, created = Role.objects.get_or_create(name='parent')
    template_name = 'parent_home.html'

    def worktime_commitments(self):
        # today = timezone.now().date(),
        return WorktimeCommitment.objects.filter(
            child__parent_set=self.request.user,
            start__range = self.date_range()).select_related(
                'child__classroom')

    def events(self):
        return Happening.objects.all()

    def holidays(self):
        return Holiday.objects.all()


# for teachers with a single classroom; 
# need special handling for multi-classroom teachers
class TeacherHomeView(RoleHomeMixin,
                      RedirectView):
    role, created = Role.objects.get_or_create(name='teacher')

    # todo bug breaks if user teaches in multiple classrooms
    def get_redirect_url(self, *args, **kwargs):
        classrooms = self.request.user.classrooms_as_teacher()
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



#########################
# child calendar views #
#########################



class EditWorktimeCommitmentView(PerChildEditWorktimeMixin,
                                 ChildEditMixin,
                                 # ClassroomMixin,
                                 # ClassroomWorktimeMixin,
                                 FormView):
    permission_required = 'people.edit_child'
    form_class = main.forms.RescheduleWorktimeCommitmentForm
    template_name = 'reschedule_worktime_commitment.html'

    def commitment(self):
        kwargs = self.kwargs
        pk = self.kwargs.get('pk')
        return WorktimeCommitment.objects.get(
            pk=pk)
        
    def available_shifts(self):
        earlier = datetime.timedelta(days=7)
        later = datetime.timedelta(days=7)
        ret = self.commitment().alternatives(earlier, later)
        return ret

    def get_success_url(self):
        return reverse('parent-home')
        # return self.request.META.get(
            # 'HTTP_REFERER', 
        # )


    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'child' : self.child,
                       'current_commitment' : self.commitment(),
                       'available_shifts' : self.available_shifts()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {'shift_occ': self.commitment().shift_occurrence().serialize()}
        print(data)
        initial.update(data)
        return initial

    def form_valid(self, form):
        # raise Exception("Form Valid method called")
        revisions = form.execute()
        if revisions:
            strformat = '%-I:%M on %-B %-d'
            message = f"thanks! {self.child}'s worktime commitment is rescheduled from {revisions['old_start'].strftime(strformat)} to {revisions['new_start'].strftime(strformat)}."
            messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)


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
        self.shifts = self.shifts()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.shifts = self.shifts()
        return super().post(request, *args, **kwargs)

    def shifts(self):
        assignments = CareDayAssignment.objects.spans(
            self.object.start, self.object.end).filter(
                child=self.child).select_related('careday')
        return list(chain.from_iterable(a.careday.shifts for a in assignments))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['min_shifts'] = scheduling_config.SHIFTPREFERENCE_MIN
        context['shifts'] = self.shifts
        return context

    def get_form_kwargs(self, *args, **kwargs):
        # todo shrink the shifts field using ContractedCareDayAssignment
        kwargs = super().get_form_kwargs(*args, **kwargs)
        extras = {'shifts_dict' : {shift.pk : shift
                                   for shift in self.shifts},
                  'child' : self.child,
                  'period' : self.object,
                  'existing_prefs' : {pref.shift.pk : pref for pref in
                                      kwargs['initial']['existing_prefs']}}
        kwargs.update(extras)
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        existing_prefs = ShiftPreference.objects.filter(child=self.child,
                                                        period=self.object)
        data = {str(pref.shift.pk) : pref.rank for pref in existing_prefs}
        data.update({'existing_prefs' : existing_prefs})
        initial.update(data)
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
        classrooms = self.request.user.classrooms_as_scheduler()
        if classrooms.count() >= 1:
            return reverse('scheduler-calendar',
                           kwargs = {'classroom_slug' : classrooms.first().slug})
        else:
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
class SchedulerCalendarView(MonthlyCalendarMixin,
                            ClassroomEditMixin,
                            ClassroomWorktimeMixin,
                            CalendarMixin,
                            TemplateView):

    template_name = 'scheduler_calendar.html'
    view_name = 'scheduler-calendar'



# todo is this the correct inheritance order?
class FourWeekSchedulerCalendarView(ClassroomEditMixin,
                            ClassroomWorktimeMixin,
                            CalendarMixin,
                            TemplateView):

    num_weeks = 4
    template_name = 'scheduler_calendar.html'
    unit_name = 'weekly'
    

    # todo break period into three four-week sections, show active section
    @property
    def start_date(self):
        most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
        return most_recent_monday
    
    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)


    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('scheduler-calendar',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(4)

    def previous(self):
        return self.jump_url(-4)





# todo is this the correct inheritance order?
class MakeWorktimeCommitmentsView(MonthlyCalendarMixin,
                                  # ClassroomEditMixin,
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

    # todo
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {sh_occ.serialize() : getattr(sh_occ.commitment, 'child', None) == self.child 
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

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['classroom'] = self.classroom
        return kwargs


class PreferencesSolicitView(ClassroomEditMixin,
                             SingleObjectMixin,
                             FormView):
    model = Period

class PreferencesNagView(ClassroomEditMixin,
                         SingleObjectMixin,
                         FormView):
    model = Period

class PreferencesDisplayView(ClassroomEditMixin,
                             DateMixin,
                             SingleObjectMixin,
                             FormView):
    # form is simple submit button to generate assignment from preferences
    template_name = 'preferences_for_scheduler.html'
    form_class = main.forms.GenerateShiftAssignmentsForm
    model = Period

    # def get_queryset(self):
        # return Period.objects.filter(classroom=self.classroom)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['period'] = self.get_object()
        return kwargs

    def get_success_url(self):
        return reverse('list-shiftassignmentcollections',
                       kwargs = {'classroom_slug' : self.object.classroom.slug,
                                 'pk' : self.object.pk})

    # def form_valid(self, form):
        # no_worse_than = form.cleaned_data['no_worse_than']
        # ShiftAssignmentCollection.objects.generate(self.get_object(),
                                                   # no_worse_than=no_worse_than)
        # super().form_valid(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    # def prefs(self):
    #     return ShiftPreference.objects.filter(child__classroom=self.object.classroom)

    def prefs_by_shift(self):
        prefs = ShiftPreference.objects.by_shift(self.object)
        return prefs.items()

    def prefs_by_time_and_weekday(self):
        return ShiftPreference.objects.by_time_and_weekday(self.object)
        # prefs = ShiftPreference.objects.by_weekday_and_time(self.object)
        # for i in prefs.items():
            # print(i)
        # return prefs


    def shifts(self):
        shifts = Shift.objects.by_weekday_and_time(classroom=self.object.classroom)
        # print(shifts)
        return shifts

    def weekdays(self):
        return WEEKDAYS


class ShiftAssignmentCollectionsListView(ClassroomEditMixin,
                                         SingleObjectMixin,
                                         TemplateView):

    template_name = 'shiftassignments_list.html'
    model = Period

    def assignment_collections(self):
        return ShiftAssignmentCollection.objects.filter(period=self.object)

    def get_success_url(self):
        return reverse('scheduler-calendar', kwargs={
            'classroom_slug' : self.object.classroom.slug
        })

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # security issue here... verify pk is ok
        # print("request.POST:", request.POST)
        collection_pk = int(request.POST['collection_pk'])
        collection = ShiftAssignmentCollection.objects.get(pk=collection_pk)
        collection.create_commitments()
        return HttpResponseRedirect(self.get_success_url())



class ShiftAssignmentDetailView(ClassroomEditMixin,
                                DetailView):
    model = Period
    # link to generate commitments from ShiftAssignment




# misquamicut
# ashtanga

# todo is this the correct inheritance order?
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
    @property
    def start_date(self):
        most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
        return most_recent_monday
    
    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'child_slug' : self.child.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('make-worktime-commitments',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(4)

    def previous(self):
        return self.jump_url(-4)


    # post is idempotent so ok to return the same url
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

class WorktimeAttendanceView(DateIntervalMixin,
                             ClassroomMixin,
                             FormView):

    form_class = main.forms.WorktimeAttendanceForm    
    template_name = 'score_attendance.html'
    permission_required = 'main.score_worktime_attendance'

    def get_success_url(self):
        kwargs = {'classroom_slug' : self.classroom.slug}
        print("DATED?", self.is_dated)
        if self.is_dated:
            kwargs.update({'year' : self.start.year,
                           'month' : self.start.month,
                           'day' : self.start.day})
        return reverse('daily-classroom-calendar',
                       kwargs=kwargs)

    

    def get_commitments(self):
        return WorktimeCommitment.objects.filter(
            child__classroom=self.classroom,
            start__date=self.date())

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'commitments' : self.get_commitments()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {str(commitment.pk) : commitment.completed
                for commitment in self.get_commitments()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        form.save()
        # if revisions:
        return super().form_valid(form)
