from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # Réservations
    path('', views.reservation_list, name='list'),
    path('create/<int:book_id>/', views.create_reservation, name='create'),
    path('<int:pk>/cancel/', views.cancel_reservation, name='cancel'),
    path('<int:pk>/detail/', views.reservation_detail, name='detail'),
]
