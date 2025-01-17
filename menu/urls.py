from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'menu'

urlpatterns = [
    path('', views.home, name='home'),
    path('page-in-progress', views.progress_page, name='progress_page'),
    path('employees/', views.employees_page, name='employees_page'),
    path('weekly-menu/', views.weekly_menu, name='weekly_menu'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('save-user-choices', views.save_user_choices, name='save_user_choices'),
    path('create-employee', views.create_employee, name='create_employee'),
    path('edit-employee/', views.edit_employee, name='edit_employee'),
    path('delete-employees/', views.delete_employee, name='delete_employee'),
    path('get-employee/<int:employee_id>/', views.get_employee, name='get_employee'),
    path('update-weekly-menu', views.update_weekly_menu, name='update_weekly_menu'),
    path('options/', views.options_page, name='options_page'),
    path('create-option/', views.create_option, name='create_option'),
    path('get-option/<int:option_id>/', views.get_options, name='get_options'),
    path('reports/', views.reports_page, name='reports_page'),
    path('edit-option/', views.edit_option, name='edit_option'),
    path('delete-options/', views.delete_option, name='delete_option'),
]


if settings.DEBUG:  # Apenas no modo de desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

