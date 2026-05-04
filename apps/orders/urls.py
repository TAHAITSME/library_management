from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.orders_list_view, name='orders_list'),
    path('create/', views.create_order_view, name='create_order'),
    path('<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('<int:order_id>/payment/', views.order_payment_view, name='order_payment'),
    path('<int:order_id>/stripe/checkout/', views.create_stripe_checkout_session_view, name='stripe_checkout'),
    path('<int:order_id>/stripe/success/', views.stripe_success_view, name='stripe_success'),
    path('<int:order_id>/stripe/cancel/', views.stripe_cancel_view, name='stripe_cancel'),
    path('stripe/webhook/', views.stripe_webhook_view, name='stripe_webhook'),
    path('admin/payments/', views.payments_admin_list_view, name='payments_admin_list'),
]
