from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'menu'

urlpatterns = [
    path('', views.home, name='home'),
    path('last-week-menu', views.last_week_menu, name='last_week_menu'),
    path('page-in-progress', views.progress_page, name='progress_page'),
    path('weekly-menu/', views.weekly_menu, name='weekly_menu'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'), 
    path('save-user-choices', views.save_user_choices, name='save_user_choices'),
    
    path('update-weekly-menu', views.update_weekly_menu, name='update_weekly_menu'),
    
    path('reports/', views.reports_page, name='reports_page'),
    path('generate-full-report/', views.generate_full_report_button, name='generate_full_report_button'),
    path('generate-pdf-report-unity-one/', views.generate_pdf_report_unit_one, name='generate_pdf_report_unit_one'),
    path('generate-pdf-report-unity-two/', views.generate_pdf_report_unit_two, name='generate_pdf_report_unit_two'),
    path('generate-pdf-report-unity-five/', views.generate_pdf_report_unit_five, name='generate_pdf_report_unit_five'),
    path('generate-pdf-invoicing-report/', views.generate_pdf_invoicing_report, name='generate_pdf_invoicing_report'),


    path('comparative-reports/', views.reports_comparative_page, name='reports_comparative_page'),

    path('employees/', views.employees_page, name='employees_page'),
    path('create-employee', views.create_employee, name='create_employee'),
    path('edit-employee/', views.edit_employee, name='edit_employee'),
    path('delete-employees/', views.delete_employee, name='delete_employee'),
    path('get-employee/<int:employee_id>/', views.get_employee, name='get_employee'),

    path('options/', views.options_page, name='options_page'),
    path('create-option/', views.create_option, name='create_option'),
    path('get-option/<int:option_id>/', views.get_options, name='get_options'),
    path('edit-option/', views.edit_option, name='edit_option'),
    path('delete-options/', views.delete_option, name='delete_option'),
    
    path('shifts/', views.shifts_page, name='shifts_page'),
    path('create-shift/', views.create_shift, name='create_shift'),
    path('get-shift/<int:shift_id>/', views.get_shifts, name='get_shifts'),
    path('delete-shifts/', views.delete_shift, name='delete_shift'),
    path('edit-shifts/', views.edit_shift, name='edit_shift'),

    path('companies/', views.companies_page, name='companies_page'),
    path('create-company/', views.create_company, name='create_company'),
    path('get-company/<int:company_id>/', views.get_companies, name='get_companies'),
    path('delete-companies/', views.delete_company, name='delete_company'),
    path('edit-companies/', views.edit_company, name='edit_company'),

    path('units/', views.units_page, name='units_page'),
    path('create-unity/', views.create_unity, name='create_unity'),
    path('get-unity/<int:unity_id>/', views.get_units, name='get_units'),
    path('delete-units/', views.delete_unity, name='delete_unity'),
    path('edit-units/', views.edit_unity, name='edit_unity'),

    path('my-profile/', views.profile_page, name='profile_page'),
    path('change-password', views.change_password, name='change_password'),


    path('restaurants/', views.restaurant_page, name='restaurant_page'),
    path('create-restaurant/', views.create_restaurant, name='create_restaurant'),
    path('get-restaurant/<int:restaurant_id>/', views.get_restaurants, name='get_restaurants'),
    path('edit-restaurant/', views.edit_restaurant, name='edit_restaurant'),
    path('delete-restaurant/', views.delete_restaurant, name='delete_restaurant'),
]


if settings.DEBUG:  # Apenas no modo de desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

