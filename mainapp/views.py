from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

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
usage_stats = {
    'signups': 0,
    'logins': 0,
}

# In-memory payment status tracking
payment_status = {}

# Update payment view to mark user as paid
def payment(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Here you would handle payment processing
        # For now, assume payment is successful
        payment_status[request.user.username] = True
        return redirect('index')
    return render(request, 'payment.html')

@login_required
def usage_tracking(request):
    if request.user.username != 'developer':
        return HttpResponseForbidden("Access denied")
    users = User.objects.all().order_by('date_joined')
    # Pass payment status dict to template
    return render(request, 'usage_tracking.html', {'users': users, 'payment_status': payment_status})

# Increment signup count when user is created
def increment_signup():
    usage_stats['signups'] += 1

# Increment login count on user login signal
@receiver(user_logged_in)
def increment_login(sender, request, user, **kwargs):
    usage_stats['logins'] += 1

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
