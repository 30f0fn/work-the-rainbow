from django.urls import path, include
from main import views

basic_patterns = [
    path('',
         views.RedirectToHomeView.as_view(),
         name='home'),

    path('splash',
         views.SplashView.as_view(),
         name='splash'),

    path('parent',
         views.ParentHomeView.as_view(),
         name='parent-home'),
    path('teacher',
         views.TeacherHomeView.as_view(),
         name='teacher-home'),
    path('scheduler',
         views.SchedulerHomeView.as_view(),
         name='scheduler-home'),
    path('admin',
         views.AdminHomeView.as_view(),
         name='admin-home'),
]




classroom_calendar_patterns = [

    path('',
         views.WeeklyClassroomCalendarView.as_view(),
         name='classroom-calendar'),
    path('daily',
         views.DailyClassroomCalendarView.as_view(),
         name='daily-classroom-calendar'),
    path('weekly',
         views.WeeklyClassroomCalendarView.as_view(),
         name='weekly-classroom-calendar'),
    path('monthly',
         views.MonthlyClassroomCalendarView.as_view(),
         name='monthly-classroom-calendar'),

    path('daily/<int:year>/<int:month>/<int:day>',
         views.DailyClassroomCalendarView.as_view(),
         name='daily-classroom-calendar'),
    path('weekly/<int:year>/<int:month>/<int:day>',
         views.WeeklyClassroomCalendarView.as_view(),
         name='weekly-classroom-calendar'),
    path('monthly/<int:year>/<int:month>/<int:day>',
         views.MonthlyClassroomCalendarView.as_view(),
         name='monthly-classroom-calendar'),
]

child_parenting_patterns = [
    path('worktime/reschedule/<int:pk>',
         views.EditWorktimeCommitmentView.as_view(),
         name='edit-worktime-commitment'),
    path('caredays/assign',
         views.CareDayAssignmentsCreateView.as_view(),
         name='create-careday-assignments'),
    path('caredays/create/<int:pk>',
          views.CareDayAssignmentDeleteView.as_view(),
          name='delete-caredayassignment'),
    path('caredays/edit/<int:pk>',
          views.CareDayAssignmentEditView.as_view(),
          name='edit-caredayassignment'),
    path('worktime/preferences/submit/<int:pk>',
         views.WorktimePreferencesSubmitView.as_view(),
         name='submit-preferences'),
]

classroom_scheduling_patterns = [
    path('scheduling',
         views.SchedulerHomeView.as_view(),
         name='scheduling'),

    path('scheduling/periods/list',
         views.PeriodListView.as_view(),
         name='list-periods'),

    path('scheduling/periods/detail/<int:pk>',
         views.PeriodDetailView.as_view(),
         name='manage-period'),

    path('scheduling/periods/create',
         views.PeriodCreateView.as_view(),
         name='create-period'),

    path('scheduling/periods/edit/<int:pk>',
         views.PeriodUpdateView.as_view(),
         name='update-period'),

    path('scheduling/periods/delete/<int:pk>',
         views.PeriodDeleteView.as_view(),
         name='delete-period'),

    # todo all below paths should be relativized to period

    # path('scheduling/preferences/solicit',
    #      views.PreferencesSolicitView.as_view(),
    #      name='solicit-preferences'),

    # # path('scheduling/preferences/nag',
    #      # views.PreferencesNagView.as_view(),
    #      # name='nag-preferences'),

    path('scheduling/preferences/display/<int:pk>',
         views.PreferencesDisplayView.as_view(),
         name='display-preferences'),

    path('scheduling/shiftassignments/list/<int:period_pk>',
         views.ShiftAssignmentsListView.as_view(),
         name='list-shiftassignments'),


    path('scheduling/calendar',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/calendar/<int:year>/<int:month>/<int:day>',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/<slug:nickname>/<int:year>/<int:month>/<int:day>',
         views.MakeWorktimeCommitmentsView.as_view(),
         name='make-worktime-commitments'),
]

classroom_patterns = [
    path('', include(classroom_scheduling_patterns)),
    path('calendar/', include(classroom_calendar_patterns)),
    path('worktime/attendance',
         views.WorktimeAttendanceView.as_view(),
         name='worktime-attendance'),
    path('worktime-attendance/<int:year>/<int:month>/<int:day>',
         views.WorktimeAttendanceView.as_view(),
         name='worktime-attendance'),

]

urlpatterns = [
    path('', include(basic_patterns)),
    # path('scheduling/', include(classroom_scheduling_patterns)),
    path('<slug:classroom_slug>/', include(classroom_patterns)),
    path('<slug:nickname>/', include(child_parenting_patterns)),
]
