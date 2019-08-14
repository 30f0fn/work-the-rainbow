from django.urls import path, include
from main import views

basic_patterns = [
    path('',
         views.RedirectToHomeView.as_view(),
         name='home'),

    path('splash',
         views.SplashView.as_view(),
         name='splash'),

    path('splash',
         views.SplashView.as_view(),
         name='null-home'),

    path('parent/upcoming',
         views.ParentHomeView.as_view(),
         name='parent-home'),

    path('parent/upcoming/<int:year>/<int:month>/<int:day>',
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

    path('admin/holidays/create',
         views.HolidayCreateView.as_view(),
         name='create-holiday'),
    path('admin/holidays/edit/<int:pk>',
         views.HolidayUpdateView.as_view(),
         name='update-holiday'),
    path('admin/holidays/delete/<int:pk>',
         views.HolidayDeleteView.as_view(),
         name='delete-holiday'),

    path('admin/happenings/create',
         views.HappeningCreateView.as_view(),
         name='create-happening'),
    path('admin/happenings/edit/<int:pk>',
         views.HappeningUpdateView.as_view(),
         name='update-happening'),
    path('admin/happenings/delete/<int:pk>',
         views.HappeningDeleteView.as_view(),
         name='delete-happening'),
]




classroom_calendar_patterns = [

    path('',
         views.DefaultCalendarView.as_view(),
         # views.WeeklyClassroomCalendarView.as_view(),
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

    # path('scheduling/preferences/solicit',
    #      views.PreferencesSolicitView.as_view(),
    #      name='solicit-preferences'),

    # # path('scheduling/preferences/nag',
    #      # views.PreferencesNagView.as_view(),
    #      # name='nag-preferences'),

    path('scheduling/preferences/display/<int:pk>',
         views.PreferencesView.as_view(),
         name='display-preferences'),

    # path('scheduling/shiftassignments/list/<int:pk>',
         # views.GeneratedSchedulesView.as_view(),
         # name='list-shiftassignmentcollections'),

    path('scheduling/assignables/<int:pk>',
         views.AssignablesView.as_view(),
         name='view-assignables'),

    path('scheduling/generated-schedules/<int:pk>',
         views.GeneratedSchedulesView.as_view(),
         name='view-generated-schedules'),



    path('scheduling/calendar',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/calendar/<int:year>/<int:month>/<int:day>',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/<slug:child_slug>/<int:year>/<int:month>/<int:day>',
         views.MakeWorktimeCommitmentsView.as_view(),
         name='make-worktime-commitments'),

    path('rescheduling/<slug:child_slug>/<int:year>/<int:month>/<int:day>',
         views.EditWorktimeCommitmentsForParentByMonth.as_view(),
         name='edit-worktimecommitments-for-parent-by-month'),

    path('rescheduling/<slug:child_slug>/<int:pk>',
         views.EditWorktimeCommitmentView.as_view(),
         name='edit-worktime-commitment'),

    path('rescheduling/<slug:child_slug>/<int:pk>/<int:year>/<int:month>/<int:day>',
         views.EditWorktimeCommitmentView.as_view(),
         name='edit-worktime-commitment'),



]

classroom_patterns = [
    path('', include(classroom_scheduling_patterns)),
    path('calendar/', include(classroom_calendar_patterns)),
    # path('worktime/attendance',
         # views.WorktimeAttendanceByDateView.as_view(),
         # name='worktime-attendance'),
    # path('worktime-attendance/<int:year>/<int:month>/<int:day>',
         # views.WorktimeAttendanceByDateView.as_view(),
         # name='worktime-attendance-by-date'),
    # path('worktime-attendance-weekly',
    #      views.WorktimeAttendanceByWeekView.as_view(),
    #      name='worktime-attendance-by-week'),
    path('worktime/attendance',
         views.WorktimeAttendanceByMonthView.as_view(),
         name='worktime-attendance'),
    # path('worktime-attendance-weekly/<int:year>/<int:month>/<int:day>',
         # views.WorktimeAttendanceByWeekView.as_view(),
         # name='worktime-attendance-by-week'),
    path('worktime/attendance/<int:year>/<int:month>/<int:day>',
         views.WorktimeAttendanceByMonthView.as_view(),
         name='worktime-attendance-by-month'),
    # path('worktime-attendance/<slug:child_slug>/<int:year>',
         # views.WorktimeAttendanceByChildView.as_view(),
         # name='worktime-attendance-by-child'),

]

urlpatterns = [
    path('', include(basic_patterns)),
    # path('scheduling/', include(classroom_scheduling_patterns)),
    path('<slug:classroom_slug>/', include(classroom_patterns)),
    path('<slug:child_slug>/', include(child_parenting_patterns)),
]
