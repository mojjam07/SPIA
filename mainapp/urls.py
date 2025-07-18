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
    path('reports/', views.reports_section, name='reports_section'),

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

    path('api/send_sales_summary_pdf/', views.SendSalesSummaryPDFAPIView.as_view(), name='send_sales_summary_pdf'),
    path('api/send_deleted_items_pdf/', views.SendDeletedItemsPDFAPIView.as_view(), name='send_deleted_items_pdf'),

    path('api/record_sale/', views.SaleRecordCreateAPIView.as_view(), name='record_sale'),
    path('api/verify-auth/', views.VerifyAuthAPIView.as_view(), name='api_verify_auth'),

    # New API endpoint for deleted items list
    path('api/deleted-items/', views.DeletedRecordLogListAPIView.as_view(), name='api_deleted_items'),

    # New API endpoint for sales summary list
    path('api/sales-summary/', views.SalesSummaryAPIView.as_view(), name='api_sales_summary'),

    path('api/clear-sales/', views.ClearSalesAPIView.as_view(), name='api_clear_sales'),
    path('api/clear-deleted-items/', views.ClearDeletedItemsAPIView.as_view(), name='api_clear_deleted_items'),

    # Added missing API routes to fix 404 errors
    path('api/top-products/', views.TopProductsAPIView.as_view(), name='api_top_products'),
    path('api/daily-sales/', views.DailySalesAPIView.as_view(), name='api_daily_sales'),
    path('api/revenue-overview/', views.RevenueOverviewAPIView.as_view(), name='api_revenue_overview'),
    path('api/inventory-levels/', views.InventoryLevelsAPIView.as_view(), name='api_inventory_levels'),
    path('api/weekly-sales/', views.WeeklySalesAPIView.as_view(), name='api_weekly_sales'),
    path('api/sales-trend/', views.SalesTrendAPIView.as_view(), name='api_sales_trend'),
    path('api/monthly-sales/', views.MonthlySalesAPIView.as_view(), name='api_monthly_sales'),
]


    
# from .views import (
#     ClearDeletedItemsAPIView, ClearSalesAPIView, payment_callback,
#     VerifyAuthAPIView, DeletedRecordLogListAPIView,
#     SalesSummaryAPIView, TopProductsAPIView, DailySalesAPIView, WeeklySalesAPIView,
#     SalesTrendAPIView, MonthlySalesAPIView, RevenueOverviewAPIView, InventoryLevelsAPIView, SendSalesSummaryPDFAPIView, SendDeletedItemsPDFAPIView
# )
#     path('login/', views.login, name='login'),
#     path('signup/', views.signup, name='signup'),
#     path('payment/', views.payment, name='payment'),
#     path('payment/callback/', payment_callback, name='payment_callback'),
#     path('logout/', views.logout, name='logout'),
#     path('inventory/', views.inventory, name='inventory'),
#     path('receipt/', views.receipt, name='receipt'),
#     path('sales/', views.sales, name='sales'),
#     # API endpoints
#     path('api/signup/', SignupAPIView.as_view(), name='signup-api'),
#     path('api/login/', LoginAPIView.as_view(), name='login-api'),
#     path('api/stock-items/', StockItemListCreateAPIView.as_view(), name='stock-item-list-create'),
#     path('api/stock-items/<int:pk>/', StockItemRetrieveUpdateDestroyAPIView.as_view(), name='stock-item-retrieve-update-destroy'),
#     path('api/sales/', SaleRecordCreateAPIView.as_view(), name='sale-record-create'),