from django.contrib import admin
from .models import UserProfile, PaymentStatus, UsageStats, StockItem

admin.site.register(UserProfile)
admin.site.register(PaymentStatus)
admin.site.register(UsageStats)
admin.site.register(StockItem)
