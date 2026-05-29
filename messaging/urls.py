from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:pk>/', views.conversation_detail, name='detail'),
    path('start/<int:doctor_id>/', views.start_conversation, name='start'),
    path('from-appointment/<int:appointment_id>/', views.start_from_appointment, name='from_appointment'),
    path('unread/', views.unread_messages_count, name='unread_count'),
]
