from django.urls import path, include
from . import views

schedule_patterns = [
    path('upcoming', views.UpcomingEventsView.as_view(),
         name='upcoming-events')
]


schedule_preferences_patterns = [
    path('preferences', views.PreferencesSubmitView.as_view(),
         name='preferences')    
]

classroom_schedule_patterns = [
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


urlpatterns = [
    path('', views.UpcomingEventsView.as_view(), name='home'), # maybe defined by user settings
    # path('calendar/', include(family_calendar_patterns)),
    path('schedule/', include(schedule_patterns)),
    path('<slug:classroom_slug>/calendar/', include(classroom_schedule_patterns)),
    path('<slug:classroom_slug>/<slug:child>/', include(schedule_preferences_patterns)),
]


"""
general strategy for calendar urlconfs:
supply units, and either no date, or either complete absolute date
if no date, then use datetime.now, else use date supplied
extract start_date and end_date from enclosing unit of date
extract days, weeks from enclosing unit
"""

