from django.urls import path
from . import views
from . import pdf_views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book'),
    path('<int:pk>/', views.appointment_detail, name='detail'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel'),
    path('<int:pk>/reschedule/', views.reschedule_appointment, name='reschedule'),
    path('<int:pk>/pdf/', pdf_views.export_appointment_pdf, name='export_pdf'),
    path('history/pdf/', pdf_views.export_patient_history_pdf, name='export_history_pdf'),
    path('prescription/<int:consultation_id>/pdf/', pdf_views.export_prescription_pdf, name='prescription_pdf'),
    path('patient/<int:patient_id>/history/', views.patient_medical_history, name='patient_history'),
]
