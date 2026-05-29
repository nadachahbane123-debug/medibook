from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .search_views import global_search

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('search/', global_search, name='search'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('patients/', include('patients.urls', namespace='patients')),
    path('doctors/', include('doctors.urls', namespace='doctors')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('schedules/', include('schedules.urls', namespace='schedules')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('ai/', include('ai_orientation.urls', namespace='ai_orientation')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('messaging/', include('messaging.urls', namespace='messaging')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'medibook_project.views.error_404'
handler500 = 'medibook_project.views.error_500'
