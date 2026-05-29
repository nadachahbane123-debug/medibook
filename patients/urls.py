from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('update-medical/', views.update_medical_info, name='update_medical'),
]
