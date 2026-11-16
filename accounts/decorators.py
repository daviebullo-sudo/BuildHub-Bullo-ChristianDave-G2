from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def role_required(role):
    """Allow only logged-in users with the given role.

    Anonymous users are sent to the login page. Logged-in users with a different
    role are sent back to their own dashboard with an error message.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role != role:
                messages.error(request, 'You do not have access to that page.')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
