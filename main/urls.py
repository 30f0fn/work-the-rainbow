from django.urls import path, include
from . import views

family_calendar_patterns = [
    path('daily', views.DailyFamilyCalendarView.as_view(),
         name='daily-family-calendar'),
    path('weekly', views.WeeklyFamilyCalendarView.as_view(),
         name='weekly-family-calendar'),
    path('monthly', views.MonthlyFamilyCalendarView.as_view(),
         name='monthly-family-calendar'),
]

classroom_calendar_patterns = [
    path('daily', views.DailyClassroomCalendarView.as_view(),
         name='daily-classroom-calendar'),
    path('weekly', views.WeeklyClassroomCalendarView.as_view(),
         name='weekly-classroom-calendar'),
    path('monthly', views.MonthlyClassroomCalendarView.as_view(),
         name='monthly-classroom-calendar'),
]


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'), # maybe defined by user settings
    path('calendar/', include(family_calendar_patterns)),
    path('calendar/<slug:classroom_slug>/', include(classroom_calendar_patterns)),
]
