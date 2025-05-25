from django.urls import path, include
from . import views
from rest_framework.authtoken import views as drf_views

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

    # API routes
    path('api/signup/', views.SignupAPIView.as_view(), name='api_signup'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/payment/', views.PaymentAPIView.as_view(), name='api_payment'),
    path('api/usage/', views.UsageTrackingAPIView.as_view(), name='api_usage'),

    # StockItem API routes
    path('api/stockitems/', views.StockItemListCreateAPIView.as_view(), name='api_stockitem_list_create'),
    path('api/stockitems/<int:pk>/', views.StockItemRetrieveUpdateDestroyAPIView.as_view(), name='api_stockitem_detail'),

    # Token auth
    path('api-token-auth/', drf_views.obtain_auth_token, name='api_token_auth'),

    path('health/', views.health_check, name='health_check'),
]
