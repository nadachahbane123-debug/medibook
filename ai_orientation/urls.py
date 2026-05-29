from django.urls import path
from . import views

app_name = 'ai_orientation'

urlpatterns = [
    path('suggest/', views.ai_suggest, name='suggest'),
    path('api/', views.ai_api, name='api'),
]
