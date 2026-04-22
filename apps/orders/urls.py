from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.orders_list_view, name='orders_list'),
    path('create/', views.create_order_view, name='create_order'),
    path('<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('<int:order_id>/payment/', views.order_payment_view, name='order_payment'),
]
