from django.contrib import admin
from .models import UserProfile, PaymentStatus, UsageStats

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name')

@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'paid', 'payment_date')

@admin.register(UsageStats)
class UsageStatsAdmin(admin.ModelAdmin):
    list_display = ('signups', 'logins')
