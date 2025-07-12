# ============================================================================
# DJANGO VIEWS - INVENTORY MANAGEMENT SYSTEM
# ============================================================================
# This file contains all views for a Django-based inventory management system
# with user authentication, payment processing, and API endpoints.

# ============================================================================
# IMPORTS
# ============================================================================

# Django Core Imports
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.dispatch import receiver
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.db.models import Count
from django.db import connection
from django.conf import settings
from django.utils.timezone import now
from django.core.mail import EmailMessage

# Django REST Framework Imports
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication, generics
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import TokenAuthentication
from .authentication import CookieTokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

logger = logging.getLogger(__name__)

# Local Model and Serializer Imports
from .models import (
    UserProfile, PaymentStatus, UsageStats, StockItem, 
    SalesRecord, DeletedRecordLog
)
from .serializers import StockItemSerializer

# Third-party Library Imports
import os
import io
import json
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_default_developer_user():
    """
    Creates a default developer user if one doesn't exist.
    This is used for initial system setup and admin access.
    """
    username = 'developer'
    password = 'developerpassword'
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)

def increment_signup():
    """
    Increments the signup counter in the UsageStats model.
    Called whenever a new user successfully registers.
    """
    usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
    usage_stats_obj.signups += 1
    usage_stats_obj.save()

def is_authenticated(request):
    """
    Improved authentication check using token from cookies.
    Used for frontend authentication validation.
    """
    token_key = request.COOKIES.get('auth_token')
    if not token_key:
        return False
    try:
        token = Token.objects.get(key=token_key)
        return True
    except Token.DoesNotExist:
        return False

@receiver(user_logged_in)
def increment_login(sender, request, user, **kwargs):
    """
    Signal receiver that increments login counter when a user logs in.
    This provides usage analytics for the system administrator.
    """
    usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
    usage_stats_obj.logins += 1
    usage_stats_obj.save()

# ============================================================================
# TEMPLATE-BASED VIEWS (Web Interface)
# ============================================================================

def landing(request):
    """
    Renders the main landing page of the application.
    This is typically the first page users see when visiting the site.
    """
    return render(request, 'landing.html')

def access_control(request):
    """
    Renders the access control page containing login/signup/payment options.
    Acts as a central hub for user authentication flows.
    """
    signup_count = 0
    try:
        # Retrieve the number of signups from usage statistics to display on the page.
        usage_stats, created = UsageStats.objects.get_or_create(id=1)
        signup_count = usage_stats.signups
    except Exception as e:
        # Log an error if stats can't be retrieved, but don't crash the page.
        logger.error(f"Error retrieving usage stats for access control page: {e}")

    context = {'signup_count': signup_count}
    return render(request, 'access_control.html', context)

def signup(request):
    """
    Handles user registration process.
    
    GET: Displays the signup form
    POST: Processes registration data, creates user account and profile
    
    Features:
    - Username uniqueness validation
    - User profile creation
    - Usage statistics tracking
    - Automatic redirect to payment page
    """
    if request.method == 'POST':
        # Extract form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')
        
        # Create new user account
        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = full_name
        user.save()
        
        # Create associated user profile
        UserProfile.objects.create(user=user, full_name=full_name)
        
        # Update usage statistics
        increment_signup()
        
        # Redirect to payment page
        messages.success(request, 'Signup successful. Please complete payment.')
        return redirect('payment')
    
    return render(request, 'signup.html')

def payment(request):
    """
    Handles payment processing for user accounts.
    
    Requires user authentication.
    POST: Marks user as paid (payment processing would be implemented here)
    
    Note: This is a simplified implementation. Real payment processing
    would integrate with payment gateways like Stripe, PayPal, etc.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        # TODO: Implement actual payment processing logic
        # For now, assume payment is successful
        payment_status_obj, created = PaymentStatus.objects.get_or_create(user=request.user)
        payment_status_obj.paid = True
        payment_status_obj.save()
        return redirect('index')
    
    return render(request, 'payment.html')

def logout(request):
    """
    Logs out the current user and redirects to landing page.
    """
    auth_logout(request)
    return redirect('landing')

@login_required
def index(request):
    """
    Main dashboard/index page after user login.
    Displays personalized content based on the logged-in user.
    """
    username = request.user.username
    return render(request, 'index.html', {'username': username})

@login_required
def usage_tracking(request):
    """
    Administrative view for tracking user usage and payment status.
    
    Restricted to developer account only.
    Displays:
    - List of all registered users
    - Payment status for each user
    - User registration dates
    """
    # Restrict access to developer account only
    if request.user.username != 'developer':
        return HttpResponseForbidden("Access denied")
    
    # Fetch all users and their payment status
    users = User.objects.all().order_by('date_joined')
    payment_status_qs = PaymentStatus.objects.all()
    payment_status_dict = {ps.user.username: ps.paid for ps in payment_status_qs}
    
    return render(request, 'usage_tracking.html', {
        'users': users, 
        'payment_status': payment_status_dict
    })

# ============================================================================
# INVENTORY MANAGEMENT VIEWS
# ============================================================================

def inventory(request):
    """
    Renders the inventory management interface.
    Allows users to view and manage their stock items.
    """
    return render(request, 'inventory_section.html')

def receipt(request):
    """
    Renders the receipt generation interface.
    Used for creating and printing receipts for sales transactions.
    """
    return render(request, 'receipt.html')

def sales(request):
    """
    Renders the sales tracking and reporting interface.
    Provides overview of sales performance and transaction history.
    """
    return render(request, 'sales_section.html')


@login_required
def reports_section(request):
    """
    Reports section page.
    """
    username = request.user.username
    return render(request, 'reports_section.html', {'username': username})

@login_required
def inventory(request):
    """
    Renders the inventory management interface.
    Allows users to view and manage their stock items.
    """
    username = request.user.username
    has_paid = False
    try:
        payment_status = PaymentStatus.objects.get(user=request.user)
        has_paid = payment_status.paid
    except PaymentStatus.DoesNotExist:
        has_paid = False
    return render(request, 'inventory_section.html', {'username': username, 'has_paid': has_paid})

@login_required
def sales(request):
    """
    Renders the sales tracking and reporting interface.
    Provides overview of sales performance and transaction history.
    """
    username = request.user.username
    return render(request, 'sales_section.html', {'username': username})
# ============================================================================
# SYSTEM HEALTH AND MONITORING
# ============================================================================

def health_check(request):
    """
    Health check endpoint for deployment monitoring (e.g., Render, Heroku).
    
    Returns JSON response with system status including:
    - Overall health status
    - Database connectivity
    - Static files availability
    - Environment configuration
    
    Used by monitoring services to ensure application is running properly.
    """
    health_status = {
        "status": "healthy",
        "timestamp": "2024-05-25T10:00:00Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Test database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Check static files availability
    if os.path.exists(settings.STATIC_ROOT):
        health_status["checks"]["static_files"] = "healthy"
    else:
        health_status["checks"]["static_files"] = "warning: static root not found"
    
    # Environment configuration check
    health_status["checks"]["debug_mode"] = settings.DEBUG
    health_status["checks"]["allowed_hosts"] = settings.ALLOWED_HOSTS
    
    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)

# ============================================================================
# REST API VIEWS - AUTHENTICATION
# ============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class SignupAPIView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/signup/
    - Creates new user account
    - Creates user profile
    - Updates usage statistics
    - Returns success/error response
    
    Request Body:
    {
        "username": "string",
        "password": "string", 
        "email": "string",
        "full_name": "string"
    }
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        # Extract request data
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        
        # Validate username uniqueness
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user account and profile
        user = User.objects.create_user(username=username, password=password, email=email)
        user.first_name = full_name
        user.save()
        
        UserProfile.objects.create(user=user, full_name=full_name)
        increment_signup()
        
        return Response(
            {'message': 'Signup successful. Please complete payment.'}, 
            status=status.HTTP_201_CREATED
        )

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    """
    API endpoint for user authentication.
    
    POST /api/login/
    - Authenticates user credentials
    - Creates/retrieves authentication token
    - Sets token in HTTP-only cookie
    - Returns success message
    
    Request Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Response:
    {
        "message": "Login successful."
    }
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Create or retrieve authentication token
            token, created = Token.objects.get_or_create(user=user)
            response = Response(
                {'message': 'Login successful.'}, 
                status=status.HTTP_200_OK
            )
            # Set token in HTTP-only cookie
            response.set_cookie(
                key='auth_token',
                value=token.key,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=60*60*24*7,  # 7 days
                path='/',
            )
            return response
        else:
            return Response(
                {'error': 'Invalid username or password.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAPIView(APIView):
    """
    API endpoint for payment processing.
    
    POST /api/payment/
    - Processes payment for authenticated user
    - Updates payment status in database
    - Includes improved authentication checks and logging
    
    Requires: Token authentication
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"PaymentAPIView: Unauthenticated access attempt from IP {request.META.get('REMOTE_ADDR')}")
            return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # TODO: Implement actual payment processing
        # For now, assume payment is successful
        payment_status_obj, created = PaymentStatus.objects.get_or_create(user=request.user)
        payment_status_obj.paid = True
        payment_status_obj.save()
        
        return Response(
            {'message': 'Payment successful.'}, 
            status=status.HTTP_200_OK
        )

# ============================================================================
# REST API VIEWS - INVENTORY MANAGEMENT
# ============================================================================

class StockItemListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating stock items.
    
    GET /api/stock-items/ - List all stock items for authenticated user
    POST /api/stock-items/ - Create new stock item
    
    Features:
    - User-specific stock items (users only see their own items)
    - Token-based authentication required
    - Automatic user assignment on creation
    - Improved authentication checks and logging
    """
    authentication_classes = [CookieTokenAuthentication]
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            logger.warning(f"StockItemListCreateAPIView: Unauthenticated access attempt from IP {self.request.META.get('REMOTE_ADDR')}")
            return StockItem.objects.none()
        """Return only stock items belonging to the current user."""
        return StockItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user or not self.request.user.is_authenticated:
            logger.warning(f"StockItemListCreateAPIView: Unauthenticated create attempt from IP {self.request.META.get('REMOTE_ADDR')}")
            raise PermissionError("User not authenticated")
        """Automatically assign the current user to new stock items."""
        serializer.save(user=self.request.user)

class StockItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting individual stock items.
    
    GET /api/stock-items/{id}/ - Retrieve specific stock item
    PUT /api/stock-items/{id}/ - Update stock item
    DELETE /api/stock-items/{id}/ - Delete stock item
    
    Features:
    - User-specific access control
    - Deletion logging for audit trail
    """
    authentication_classes = [CookieTokenAuthentication]
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only stock items belonging to the current user."""
        return StockItem.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Override delete method to log deleted items for audit purposes.
        Creates a record in DeletedRecordLog before deleting the item.
        """
        instance = self.get_object()
        
        # Log the deletion for audit trail
        DeletedRecordLog.objects.create(
            user=request.user,
            item_name=instance.item_name,
            size=instance.size,
            price=instance.price,
            quantity=instance.quantity
        )
        
        return super().destroy(request, *args, **kwargs)

# ============================================================================
# REST API VIEWS - SALES AND REPORTING
# ============================================================================

class SaleRecordCreateAPIView(APIView):
    """
    API endpoint for recording sales transactions.
    
    POST /api/sales/
    - Records new sales transaction
    - Handles both authenticated and anonymous sales
    - Stores detailed transaction information
    - Improved error handling and logging
    
    Request Body:
    {
        "items": [array of sold items],
        "total": number,
        "customerName": "string"
    }
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            # Handle user assignment (authenticated or default)
            user = None
            if request.user and request.user.is_authenticated:
                user = request.user
            else:
                # Assign to first superuser if no authenticated user
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    return Response(
                        {'error': 'No valid user found to assign sale record.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Extract sale data
            items = request.data.get('items', [])
            total = request.data.get('total', 0)
            customer_name = request.data.get('customerName', '')

            # Validate sale data
            if not items or total <= 0:
                return Response(
                    {'error': 'Invalid sale data.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create sales record
            sales_record = SalesRecord.objects.create(
                user=user,
                items=items,
                total=total,
                customer_name=customer_name
            )
            sales_record.save()

            return Response(
                {'message': 'Sale recorded successfully.'}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # Log full traceback for debugging
            tb = traceback.format_exc()
            logger.error(f"Exception in SaleRecordCreateAPIView POST: {str(e)}\n{tb}")
            return Response(
                {'error': str(e), 'traceback': tb}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================================================================
# REST API VIEWS - ADMINISTRATIVE
# ============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class UsageTrackingAPIView(APIView):
    """
    API endpoint for administrative usage tracking.
    
    GET /api/usage-tracking/
    - Returns user statistics and payment information
    - Restricted to developer account only
    
    Response includes:
    - List of all users with registration dates, subscription plan, and expiry
    - Payment status for each user
    - Overall usage statistics (signups, logins)
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        # Restrict access to developer account
        if request.user.username != 'developer':
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Gather user and payment data
        users = User.objects.all().order_by('date_joined')
        payment_status_qs = PaymentStatus.objects.all()
        payment_status_dict = {ps.user.username: ps for ps in payment_status_qs}
        usage_stats_obj, created = UsageStats.objects.get_or_create(id=1)
        
        # Format user data for API response
        users_data = []
        for user in users:
            ps = payment_status_dict.get(user.username)
            users_data.append({
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined,
                'payment_status': ps.paid if ps else False,
                'subscription_plan': ps.subscription_plan if ps else None,
                'subscription_expiry': ps.subscription_expiry if ps else None,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'last_login': user.last_login,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
            })
        
        # Format usage statistics
        usage_stats_data = {
            'signups': usage_stats_obj.signups,
            'logins': usage_stats_obj.logins,
        }
        
        return Response(
            {'users': users_data, 'usage_stats': usage_stats_data}, 
            status=status.HTTP_200_OK
        )

# ============================================================================
# REST API VIEWS - PDF REPORTING
# ============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class SendSalesSummaryPDFAPIView(APIView):
    """
    API endpoint for generating and emailing sales summary PDF reports.
    
    POST /api/send-sales-pdf/
    - Generates PDF report of all sales records
    - Emails the report to specified recipient
    
    Request Body:
    {
        "email": "recipient@example.com"
    }
    
    Features:
    - PDF generation using ReportLab
    - Email delivery via Django's email system
    - Comprehensive sales transaction listing
    """
    def post(self, request):
        try:
            recipient_email = request.data.get('email')
            if not recipient_email:
                return Response(
                    {'error': 'Recipient email is required.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch all sales records
            sales_records = SalesRecord.objects.all().order_by('-timestamp')

            # Generate PDF using ReportLab
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50

            # PDF Header
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, y, "Sales Summary Report")
            y -= 30

            # Sales records content
            p.setFont("Helvetica", 12)
            for i, sale in enumerate(sales_records, start=1):
                date_str = sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                total = sale.total
                p.drawString(50, y, f"{i}. Date: {date_str}  Total: ₦{total:.2f}")
                y -= 20
                
                # Handle page breaks
                if y < 50:
                    p.showPage()
                    y = height - 50

            p.showPage()
            p.save()
            buffer.seek(0)

            # Send email with PDF attachment
            email = EmailMessage(
                subject="Sales Summary Report",
                body="Please find attached the sales summary report.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach("sales_summary.pdf", buffer.read(), "application/pdf")
            email.send()

            return Response(
                {'message': 'Sales summary PDF sent successfully.'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class SendDeletedItemsPDFAPIView(APIView):
    """
    API endpoint for generating and emailing deleted items PDF reports.
    
    POST /api/send-deleted-items-pdf/
    - Generates PDF report of deleted inventory items
    - Emails the report to specified recipient
    
    Request Body:
    {
        "deletedItems": [array of deleted item objects],
        "email": "recipient@example.com"
    }
    
    Features:
    - PDF generation with detailed item information
    - Email delivery functionality
    - Audit trail for deleted inventory items
    """
    def post(self, request):
        try:
            deleted_items = request.data.get('deletedItems', [])
            recipient_email = request.data.get('email')
            
            if not recipient_email:
                return Response(
                    {'error': 'Recipient email is required.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate PDF using ReportLab
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50

            # PDF Header
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, y, "Deleted Items Report")
            y -= 30

            # Deleted items content
            p.setFont("Helvetica", 12)
            for i, item in enumerate(deleted_items, start=1):
                name = item.get('name', '')
                size = item.get('size', '')
                price = item.get('price', 0)
                quantity = item.get('quantity', 0)
                deleted_at = item.get('deletedAt', '')[:19].replace('T', ' ')
                
                item_text = f"{i}. {name} (Size: {size}) Price: ₦{price:.2f} Qty: {quantity} Deleted At: {deleted_at}"
                p.drawString(50, y, item_text)
                y -= 20
                
                # Handle page breaks
                if y < 50:
                    p.showPage()
                    y = height - 50

            p.showPage()
            p.save()
            buffer.seek(0)

            # Send email with PDF attachment
            email = EmailMessage(
                subject="Deleted Items Report",
                body="Please find attached the deleted items report.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach("deleted_items.pdf", buffer.read(), "application/pdf")
            email.send()

            return Response(
                {'message': 'Deleted items PDF sent successfully.'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def login(request):
    """
    Handles user authentication.
    
    GET: Displays the login form
    POST: Authenticates user credentials and redirects to main interface
    
    Features:
    - Username/password authentication
    - Special handling for developer account
    - Error messaging for invalid credentials
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user credentials
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Create or retrieve authentication token
            token, created = Token.objects.get_or_create(user=user)
            response = redirect('inventory')
            # Set token in HTTP-only cookie
            response.set_cookie(
                key='auth_token',
                value=token.key,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=60*60*24*7,  # 7 days
                path='/',
            )
            return response
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    return render(request, 'login.html')

from rest_framework.permissions import IsAuthenticated
from mainapp.authentication import CookieTokenAuthentication

class ClearDeletedItemsAPIView(APIView):
    """
    API endpoint to clear all deleted items records from DeletedRecordLog.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def delete(self, request):
        try:
            DeletedRecordLog.objects.all().delete()
            return Response({'message': 'All deleted items cleared successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClearSalesAPIView(APIView):
    """
    API endpoint to clear all sales records from SalesRecord.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def delete(self, request):
        try:
            SalesRecord.objects.all().delete()
            return Response({'message': 'All sales records cleared successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyAuthAPIView(APIView):
    """
    API endpoint to verify if the user is authenticated.
    Returns success if authenticated, error otherwise.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        return Response({'message': 'User is authenticated.'}, status=status.HTTP_200_OK)

from rest_framework import generics
from .serializers import DeletedRecordLogSerializer, SalesRecordSerializer
from .models import DeletedRecordLog, SalesRecord

class DeletedRecordLogListAPIView(generics.ListAPIView):
    """
    API endpoint to list all deleted record logs.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]
    serializer_class = DeletedRecordLogSerializer

    def get_queryset(self):
        return DeletedRecordLog.objects.all()

class SalesSummaryAPIView(generics.ListAPIView):
    """
    API endpoint to list all sales summary records.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]
    serializer_class = SalesRecordSerializer

    def get_queryset(self):
        return SalesRecord.objects.all()

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from .serializers import StockItemSerializer
from .models import StockItem

class TopProductsAPIView(APIView):
    """
    API endpoint to list top products by total quantity sold.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        # Aggregate total quantity sold per product name
        top_products = StockItem.objects.values('item_name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:10]
        return Response(top_products)

from django.db.models.functions import TruncDate
from rest_framework import status

class DailySalesAPIView(APIView):
    """
    API endpoint to provide daily sales totals.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        daily_sales = (
            SalesRecord.objects
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(total_sales=Sum('total'))
            .order_by('-date')
        )
        return Response(daily_sales, status=status.HTTP_200_OK)

from django.db.models.functions import TruncWeek

class WeeklySalesAPIView(APIView):
    """
    API endpoint to provide weekly sales totals.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        weekly_sales = (
            SalesRecord.objects
            .annotate(week=TruncWeek('timestamp'))
            .values('week')
            .annotate(total_sales=Sum('total'))
            .order_by('-week')
        )
        return Response(weekly_sales, status=status.HTTP_200_OK)

from django.db.models.functions import TruncMonth

class SalesTrendAPIView(APIView):
    """
    API endpoint to provide monthly sales trend.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        sales_trend = (
            SalesRecord.objects
            .annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(total_sales=Sum('total'))
            .order_by('month')
        )
        return Response(sales_trend, status=status.HTTP_200_OK)

class MonthlySalesAPIView(APIView):
    """
    API endpoint to provide monthly sales totals.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        monthly_sales = (
            SalesRecord.objects
            .annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(total_sales=Sum('total'))
            .order_by('-month')
        )
        return Response(monthly_sales, status=status.HTTP_200_OK)

class RevenueOverviewAPIView(APIView):
    """
    API endpoint to provide revenue overview.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        total_revenue = SalesRecord.objects.aggregate(total=Sum('total'))['total'] or 0
        paid_users = PaymentStatus.objects.filter(paid=True).count()
        unpaid_users = PaymentStatus.objects.filter(paid=False).count()
        data = {
            'total_revenue': total_revenue,
            'paid_users': paid_users,
            'unpaid_users': unpaid_users,
        }
        return Response(data, status=status.HTTP_200_OK)

class InventoryLevelsAPIView(APIView):
    """
    API endpoint to provide inventory levels.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        inventory_levels = (
            StockItem.objects
            .values('item_name')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('-total_quantity')
        )
        return Response(inventory_levels, status=status.HTTP_200_OK)
