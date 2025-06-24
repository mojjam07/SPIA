from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, PaymentStatus, UsageStats, StockItem, SalesRecord
from .serializers import StockItemSerializer
from rest_framework import generics, permissions

# Create your views here.
def landing(request):
    return render(request, 'landing.html')

def access_control(request):
    # Simple access control landing page for login/signup/payment
    return render(request, 'access_control.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')
        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = full_name
        user.save()
        # Create UserProfile
        UserProfile.objects.create(user=user, full_name=full_name)
        increment_signup()
        messages.success(request, 'Signup successful. Please complete payment.')
        return redirect('payment')
    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if username == 'developer':
                return redirect('index')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, 'login.html')

def payment(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Here you would handle payment processing
        # For now, assume payment is successful
        return redirect('index')
    return render(request, 'payment.html')

def logout(request):
    auth_logout(request)
    return redirect('landing')

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth.models import User

# In-memory usage tracking (for demonstration)
# Removed in-memory dictionaries, replaced with models

# Update payment view to mark user as paid
def payment(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Here you would handle payment processing
        # For now, assume payment is successful
        payment_status_obj, created = PaymentStatus.objects.get_or_create(user=request.user)
        payment_status_obj.paid = True
        payment_status_obj.save()
        return redirect('index')
    return render(request, 'payment.html')

@login_required
def usage_tracking(request):
    if request.user.username != 'developer':
        return HttpResponseForbidden("Access denied")
    users = User.objects.all().order_by('date_joined')
    payment_status_qs = PaymentStatus.objects.all()
    payment_status_dict = {ps.user.username: ps.paid for ps in payment_status_qs}
    return render(request, 'usage_tracking.html', {'users': users, 'payment_status': payment_status_dict})

# Increment signup count when user is created
def increment_signup():
    usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
    usage_stats_obj.signups += 1
    usage_stats_obj.save()

# Increment login count on user login signal
@receiver(user_logged_in)
def increment_login(sender, request, user, **kwargs):
    usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
    usage_stats_obj.logins += 1
    usage_stats_obj.save()

@login_required
def index(request):
    username = request.user.username
    return render(request, 'index.html', {'username': username})

from django.contrib.auth.models import User

@login_required
def usage_tracking(request):
    if request.user.username != 'developer':
        return HttpResponseForbidden("Access denied")
    users = User.objects.all().order_by('date_joined')
    return render(request, 'usage_tracking.html', {'users': users})

def inventory(request):
    return render(request, 'inventory.html')

def receipt(request):
    return render(request, 'receipt.html')

def sales(request):
    return render(request, 'sales.html')

# Create default developer user if not exists
def create_default_developer_user():
    username = 'developer'
    password = 'developerpassword'
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)

# API Views

@method_decorator(csrf_exempt, name='dispatch')
class SignupAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = full_name
        user.save()
        UserProfile.objects.create(user=user, full_name=full_name)
        increment_signup()
        return Response({'message': 'Signup successful. Please complete payment.'}, status=status.HTTP_201_CREATED)

from rest_framework.authentication import TokenAuthentication

class StockItemListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StockItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class StockItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StockItem.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Log the deleted record
        from .models import DeletedRecordLog
        DeletedRecordLog.objects.create(
            user=request.user,
            item_name=instance.item_name,
            size=instance.size,
            price=instance.price,
            quantity=instance.quantity
        )
        return super().destroy(request, *args, **kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'message': 'Login successful.', 'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request):
        # Here you would handle payment processing
        # For now, assume payment is successful
        payment_status_obj, created = PaymentStatus.objects.get_or_create(user=request.user)
        payment_status_obj.paid = True
        payment_status_obj.save()
        return Response({'message': 'Payment successful.'}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class UsageTrackingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        if request.user.username != 'developer':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all().order_by('date_joined')
        payment_status_qs = PaymentStatus.objects.all()
        payment_status_dict = {ps.user.username: ps.paid for ps in payment_status_qs}
        usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
        users_data = []
        for user in users:
            users_data.append({
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined,
                'payment_status': payment_status_dict.get(user.username, False),
            })
        usage_stats_data = {
            'signups': usage_stats_obj.signups,
            'logins': usage_stats_obj.logins,
        }
        return Response({'users': users_data, 'usage_stats': usage_stats_data}, status=status.HTTP_200_OK)



from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
import json

def health_check(request):
    """
    Health check endpoint for Render deployment monitoring
    """
    health_status = {
        "status": "healthy",
        "timestamp": "2024-05-25T10:00:00Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Static files check
    if os.path.exists(settings.STATIC_ROOT):
        health_status["checks"]["static_files"] = "healthy"
    else:
        health_status["checks"]["static_files"] = "warning: static root not found"
    
    # Environment check
    health_status["checks"]["debug_mode"] = settings.DEBUG
    health_status["checks"]["allowed_hosts"] = settings.ALLOWED_HOSTS
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)

class SaleRecordCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        try:
            user = request.user
            items = request.data.get('items', [])
            total = request.data.get('total', 0)
            customer_name = request.data.get('customerName', '')

            if not items or total <= 0:
                return Response({'error': 'Invalid sale data.'}, status=status.HTTP_400_BAD_REQUEST)

            sales_record = SalesRecord.objects.create(
                user=user,
                items=items,
                total=total,
                customer_name=customer_name
            )
            sales_record.save()

            return Response({'message': 'Sale recorded successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class SendSalesSummaryPDFAPIView(APIView):
    def post(self, request):
        try:
            recipient_email = request.data.get('email')
            if not recipient_email:
                return Response({'error': 'Recipient email is required.'}, status=status.HTTP_400_BAD_REQUEST)

            sales_records = SalesRecord.objects.all().order_by('-timestamp')

            # Generate PDF
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50

            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, y, "Sales Summary Report")
            y -= 30

            p.setFont("Helvetica", 12)
            for i, sale in enumerate(sales_records, start=1):
                date_str = sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                total = sale.total
                p.drawString(50, y, f"{i}. Date: {date_str}  Total: ₦{total:.2f}")
                y -= 20
                if y < 50:
                    p.showPage()
                    y = height - 50

            p.showPage()
            p.save()
            buffer.seek(0)

            email = EmailMessage(
                subject="Sales Summary Report",
                body="Please find attached the sales summary report.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach("sales_summary.pdf", buffer.read(), "application/pdf")
            email.send()

            return Response({'message': 'Sales summary PDF sent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class SendDeletedItemsPDFAPIView(APIView):
    def post(self, request):
        try:
            deleted_items = request.data.get('deletedItems', [])
            recipient_email = request.data.get('email')
            if not recipient_email:
                return Response({'error': 'Recipient email is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate PDF
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50

            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, y, "Deleted Items Report")
            y -= 30

            p.setFont("Helvetica", 12)
            for i, item in enumerate(deleted_items, start=1):
                name = item.get('name', '')
                size = item.get('size', '')
                price = item.get('price', 0)
                quantity = item.get('quantity', 0)
                deleted_at = item.get('deletedAt', '')[:19].replace('T', ' ')
                p.drawString(50, y, f"{i}. {name} (Size: {size}) Price: ₦{price:.2f} Qty: {quantity} Deleted At: {deleted_at}")
                y -= 20
                if y < 50:
                    p.showPage()
                    y = height - 50

            p.showPage()
            p.save()
            buffer.seek(0)

            email = EmailMessage(
                subject="Deleted Items Report",
                body="Please find attached the deleted items report.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach("deleted_items.pdf", buffer.read(), "application/pdf")
            email.send()

            return Response({'message': 'Deleted items PDF sent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
