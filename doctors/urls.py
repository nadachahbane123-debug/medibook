from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='list'),
    path('<int:pk>/', views.doctor_detail, name='detail'),
    path('profile/edit/', views.doctor_profile_edit, name='edit_profile'),
    path('profile/save/', views.save_doctor_profile, name='save_profile'),
]