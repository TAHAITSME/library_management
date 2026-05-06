from django.urls import path
from . import views

app_name = 'borrowing'

urlpatterns = [
    path('', views.borrow_list_view, name='borrow_list'),
    path('<int:borrow_id>/', views.borrow_detail_view, name='borrow_detail'),
    path('request/<int:book_id>/', views.borrow_direct_view, name='borrow_request'),
    path('return/<int:borrow_id>/', views.return_book_view, name='return_book'),
    path('renew/<int:borrow_id>/', views.renew_borrow_view, name='renew_borrow'),
]
