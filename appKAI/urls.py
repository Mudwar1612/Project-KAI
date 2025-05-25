from django.urls import path
from . import views
from .views import custom_logout_view

urlpatterns = [
    path('', views.login_view, name='login'),
    path('admin', views.admin_view, name='admin'),
    path('signup', views.signup_view, name='signup'),
    path('home', views.home_view, name='home'),
    path('home/order', views.order_view, name='order'),
    path('home/booking', views.booking_view, name='booking'),
    path('home/order/prosesorder', views.prosesorder_view, name='prosesorder'),
    path('home/order/prosesorder/belumbayar/', views.belumbayar, name='belumbayar'),
    path('home/order/prosesorder/sudahdibayar/', views.sudahdibayar, name='sudahdibayar'),
    path('home/order/prosesorder/dibatalkan/', views.dibatalkan, name='dibatalkan'),
    path('home/order/prosesorder/refund/', views.refund, name='refund'),
    path('update-card-header/', views.update_card_header, name='update_card_header'),
    path("get-dates/", views.get_dates, name="get_dates"),
    path('logout/', custom_logout_view, name='logout'),
    path('bayar/<int:order_id>/', views.bayar_view, name='bayar'),
]
