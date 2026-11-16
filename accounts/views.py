from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return redirect('accounts:login')


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # password is hashed by UserCreationForm
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('accounts:login')
        messages.error(request, 'Registration failed. Please fix the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().display_name}!')
        return super().form_valid(form)


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Send each user to the dashboard that matches their role."""
    if request.user.role == User.Role.CONTRACTOR:
        return redirect('accounts:contractor_dashboard')
    return redirect('accounts:homeowner_dashboard')


@role_required(User.Role.HOMEOWNER)
def homeowner_dashboard(request):
    return render(request, 'dashboards/homeowner.html')


@role_required(User.Role.CONTRACTOR)
def contractor_dashboard(request):
    return render(request, 'dashboards/contractor.html')


@login_required
def profile(request):
    # No user id in the URL: a user can only ever see their own profile.
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
def profile_edit(request):
    # Work on a fresh copy so a failed form does not change the navbar's user data.
    user = get_object_or_404(User, pk=request.user.pk)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        messages.error(request, 'Could not update your profile. Please fix the errors below.')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})
