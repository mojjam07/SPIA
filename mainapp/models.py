from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"{self.user.username} - {'Paid' if self.paid else 'Not Paid'}"

class UsageStats(models.Model):
    signups = models.PositiveIntegerField(default=0)
    logins = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Signups: {self.signups}, Logins: {self.logins}"

class StockItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='stock_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.quantity}) - {self.user.username}"
