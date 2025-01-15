from django.shortcuts import redirect
from functools import wraps

def user_has_rh_profile(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('menu:home')  # Redireciona para a Home se não estiver logado
        if not hasattr(request.user, 'employee') or request.user.employee.profile.profile != 'RH' and request.user.is_staff == False:
            return redirect('menu:home')  # Redireciona se o perfil não for RH
        return view_func(request, *args, **kwargs)
    return _wrapped_view
