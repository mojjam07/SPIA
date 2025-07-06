from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add additional fields as needed, e.g., full_name, phone, etc.
    full_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class PaymentStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(auto_now_add=True)
    subscription_plan = models.CharField(max_length=20, blank=True, null=True)
    subscription_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {'Paid' if self.paid else 'Not Paid'}"

class UsageStats(models.Model):
    signups = models.IntegerField(default=0)
    logins = models.IntegerField(default=0)

    def __str__(self):
        return f"Signups: {self.signups}, Logins: {self.logins}"

class StockItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_items')
    item_name = models.CharField(max_length=255)
    size = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='stock_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.quantity}) - {self.user.username}"

class DeletedRecordLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    size = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deleted {self.item_name} ({self.quantity}) by {self.user.username} at {self.deleted_at}"

class SalesRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.JSONField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    timestamp = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Sale by {self.customer_name or self.user.username} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
