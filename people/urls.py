from django.urls import path, include
from . import views

import main.views

classroom_urls = [
    # path('kids',
         # views.ChildrenListView.as_view(), name='list-children'),
    path('add_kid',
         views.ChildAddView.as_view(), name='add-child'),


    # path('teachers',
         # views.TeachersListView.as_view(), name='list-teachers'),
    path('add_teacher',
         views.TeacherAddView.as_view(), name='add-teacher'),
    # path('teachers/<item_slug>',
         # views.TeacherDetailView.as_view(), name='detail-teacher'),
    # path('teachers/<item_slug>/edit',
         # views.TeacherEditView.as_view(), name='edit-teacher'),
    # path('teachers/<item_slug>/remove',
         # views.TeacherRemoveView.as_view(), name='remove-teacher'),

    path('add_scheduler',
         views.SchedulerAddView.as_view(), name='add-scheduler'),

    # path('parents',
    #      views.ParentsListView.as_view(), name='list-parents'),
    # path('parents/<item_slug>',
    #      views.ParentDetailView.as_view(), name='detail-parent'),
    # path('parents/<item_slug>/edit',
    #      views.ParentEditView.as_view(), name='edit-parent'),
    # path('parents/<item_slug>/remove',
    #      views.ParentRemoveView.as_view(), name='remove-parent'),
]

urlpatterns = [

    path('kids/<slug:nickname>',
         views.ChildDetailView.as_view(), name='child-profile'),
    path('kids/<slug:nickname>/edit',
         views.ChildEditView.as_view(), name='edit-child'),
    path('kids/<slug:nickname>/remove',
         views.ChildRemoveView.as_view(), name='remove-child'),


    path('accounts/', include('allauth.urls')),
    path('accounts/profile/',
         views.PrivateProfileView.as_view(), name='profile'),
    path('accounts/profile/edit',
         views.ProfileEditView.as_view(), name='edit-profile'),
    path('invitations/', include('invitations.urls', namespace='invitations')),
    path('<slug:classroom_slug>/', include(classroom_urls)),
    path('<slug:classroom_slug>/roster', 
         views.ClassroomView.as_view(), name='classroom-roster'),
    path('<slug:classroom_slug>/manage', 
         views.ManageClassroomView.as_view(), name='manage-classroom'),
    path('create_classroom', 
         views.ClassroomCreateView.as_view(), name='create-classroom'),

    path('people/<slug:username>',
         views.PublicProfileView.as_view(), name='public-profile')
]
