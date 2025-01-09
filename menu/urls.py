from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'menu'

urlpatterns = [
    path('', views.home, name='home'),
    path('page-in-progress', views.progress_page, name='progress_page'),
    path('login', views.login, name='login')
]

if settings.DEBUG:  # Apenas no modo de desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

