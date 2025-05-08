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

from .models import UserProfile, PaymentStatus, UsageStats

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
