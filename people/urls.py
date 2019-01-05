from django.urls import path, include
from . import views

classroom_urls = [
    path('kids',
         views.ChildrenListView.as_view(), name='list-children'),
    path('add_kid',
         views.ChildAddView.as_view(), name='add-child'),
    path('kids/<item_slug>',
         views.ChildDetailView.as_view(), name='detail-child'),
    path('kids/<item_slug>/edit',
         views.ChildEditView.as_view(), name='edit-child'),
    path('kids/<item_slug>/remove',
         views.ChildRemoveView.as_view(), name='remove-child'),

    path('teachers',
         views.TeachersListView.as_view(), name='list-teachers'),
    path('add_teacher',
         views.TeacherAddView.as_view(), name='add-teacher'),
    path('teachers/<item_slug>',
         views.TeacherDetailView.as_view(), name='detail-teacher'),
    path('teachers/<item_slug>/edit',
         views.TeacherEditView.as_view(), name='edit-teacher'),
    path('teachers/<item_slug>/remove',
         views.TeacherRemoveView.as_view(), name='remove-teacher'),

    path('parents',
         views.ParentsListView.as_view(), name='list-parents'),
    path('parents/<item_slug>',
         views.ParentDetailView.as_view(), name='detail-parent'),
    path('parents/<item_slug>/edit',
         views.ParentEditView.as_view(), name='edit-parent'),
    path('parents/<item_slug>/remove',
         views.ParentRemoveView.as_view(), name='remove-parent'),
]

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('<slug:classroom_slug>/', include(classroom_urls)),
    path('<slug:slug>/manage', 
         views.ClassroomView.as_view(), name='manage-classroom',),
    path('create_classroom', 
         views.ClassroomCreateView.as_view(), name='create-classroom',),
    path('invited/<slug:token>',
         views.InviteAcceptView.as_view(), name='accept-invitation'),
]
