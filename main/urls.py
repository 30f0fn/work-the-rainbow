from django.urls import path, include
from main import views

user_schedule_patterns = [
    path('',
         views.UpcomingEventsView.as_view(),
         name='home'),
    path('upcoming',
         views.UpcomingEventsView.as_view(),
         name='upcoming-events'),
    path('worktime-preferences/<slug:classroom_slug>/<slug:child>',
         views.WorktimePreferencesSubmitView.as_view(),
         name='worktime-preferences'),
    path('reschedule/<int:pk>',
         views.WorktimeCommitmentRescheduleView.as_view(),
         name='reschedule-worktimecommitment'),
]

classroom_calendar_patterns = [
    path('',
         views.WeeklyClassroomCalendarView.as_view(),
         name='classroom-calendar'),
    path('daily',
         views.DailyClassroomCalendarView.as_view(),
         name='daily-classroom-calendar'),
    path('daily/<int:year>/<int:month>/<int:day>',
         views.DailyClassroomCalendarView.as_view(),
         name='daily-classroom-calendar'),
    path('weekly',
         views.WeeklyClassroomCalendarView.as_view(),
         name='weekly-classroom-calendar'),
    path('weekly/<int:year>/<int:month>/<int:day>',
         views.WeeklyClassroomCalendarView.as_view(),
         name='weekly-classroom-calendar'),
    path('monthly',
         views.MonthlyClassroomCalendarView.as_view(),
         name='monthly-classroom-calendar'),
    path('monthly/<int:year>/<int:month>/<int:day>',
         views.MonthlyClassroomCalendarView.as_view(),
         name='monthly-classroom-calendar'),
]

classroom_scheduling_patterns = [
    path('<slug:child_slug>/<int:year>/<int:month>/<int:day>',
         views.MakeWorktimeCommitmentsView.as_view(),
         name='make-worktime-commitments'),
]

classroom_patterns = [
    path('scheduling/', include(classroom_scheduling_patterns)),
    path('calendar/', include(classroom_calendar_patterns)),
]

urlpatterns = [
    path('/', include(user_schedule_patterns)),
    # path('scheduling/', include(classroom_scheduling_patterns)),
    path('<slug:classroom_slug>/', include(classroom_patterns)),
]
