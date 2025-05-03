from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('access/', views.access_control, name='access_control'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('payment/', views.payment, name='payment'),
    path('logout/', views.logout, name='logout'),
    path('index/', views.index, name='index'),
    path('usage/', views.usage_tracking, name='usage_tracking'),
    path('inventory/', views.inventory, name='inventory'),
    path('receipt/', views.receipt, name='receipt'),
    path('sales/', views.sales, name='sales'),
]
