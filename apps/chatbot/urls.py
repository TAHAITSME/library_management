from django.urls import path

from . import views

app_name = 'chatbot'

urlpatterns = [
    path('ask/', views.ask_chatbot, name='ask'),
    path('conversations/', views.conversation_list, name='conversations'),
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail'),
]
