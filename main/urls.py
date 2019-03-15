from django.urls import path, include
from main import views

basic_patterns = [
    path('',
         views.RedirectToHomeView.as_view(),
         name='home'),

    path('splash',
         views.SplashView.as_view(),
         name='splash'),

    path('parents',
         views.ParentHomeView.as_view(),
         name='parent-home'),
    path('teachers',
         views.TeacherHomeView.as_view(),
         name='teacher-home'),
    path('schedulers',
         views.SchedulerHomeView.as_view(),
         name='scheduler-home'),
    path('admins',
         views.AdminHomeView.as_view(),
         name='admin-home'),

#     path('reschedule/<slug:classroom_slug>/<slug:child_slug>/<slug:unit_name>/<int:year>/<int:month>/<int:day>',
#          views.EditWorktimeCommitmentsView.as_view(),
#          name='edit-worktime-commitments'),
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
    path('worktime/preferences',
         views.WorktimePreferencesSubmitView.as_view(),
         name='worktime-preferences'),
    path('worktime/reschedule/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>',
         views.EditWorktimeCommitmentView.as_view(),
         name='edit-worktime-commitment'),
]

classroom_scheduling_patterns = [
    path('scheduling',
         views.SchedulerView.as_view(),
         name='scheduling'),

    path('scheduling/calendar',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/calendar/<int:year>/<int:month>/<int:day>',
         views.SchedulerCalendarView.as_view(),
         name='scheduler-calendar'),

    path('scheduling/<slug:child_slug>/<int:year>/<int:month>/<int:day>',
         views.MakeWorktimeCommitmentsView.as_view(),
         name='make-worktime-commitments'),
]

classroom_patterns = [
    path('', include(classroom_scheduling_patterns)),
    path('calendar/', include(classroom_calendar_patterns)),
    path('<slug:child_slug>/', include(child_parenting_patterns)),
]

urlpatterns = [
    path('', include(basic_patterns)),
    # path('scheduling/', include(classroom_scheduling_patterns)),
    path('<slug:classroom_slug>/', include(classroom_patterns)),
]
