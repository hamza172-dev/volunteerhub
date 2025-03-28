from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('create_project/', views.create_project, name='create_project'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/remove_volunteer/<int:project_id>/<int:volunteer_id>/', views.remove_volunteer_from_project, name='remove_volunteer_from_project'),
    path('projects/volunteer/<int:pk>/', views.volunteer_for_project, name='volunteer_for_project'),
    path('log_hours/<int:project_id>/', views.log_volunteer_hours, name='log_volunteer_hours'),
    path('dashboard_volunteer/', views.dashboard_volunteer, name='dashboard_volunteer'),
    path('dashboard_organization/', views.dashboard_organization, name='dashboard_organization'),
    path('dashboard_admin/', views.dashboard_admin, name='dashboard_admin'),
    path('post_announcement/', views.post_announcement, name='post_announcement'),
    path('projects/edit/<int:pk>/', views.edit_project, name='edit_project'),
    path('projects/delete/<int:pk>/', views.delete_project, name='delete_project'),
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),
    path('get_project_date/<int:pk>/', views.get_project_date, name='get_project_date'),
    path('calendar_data/', views.calendar_data, name='calendar_data'),
    path('calendar/', views.calendar, name='calendar'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent_messages/', views.sent_messages, name='sent_messages'),
    path('send_message/', views.send_message, name='send_message'),
    path('message/<int:pk>/', views.view_message, name='view_message'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark_as_read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    path('analytics/', views.analytics, name='analytics'),
    path('recommend_projects/', views.recommend_projects, name='recommend_projects'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
