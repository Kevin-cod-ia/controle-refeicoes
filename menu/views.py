from django.shortcuts import render, redirect 
from .models import WeekMenu, Employee
from django.views import View
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from utils.menu.factory import make_week_menu

# Create your views here.


def home(request):
    week_menu = WeekMenu.objects.filter()
    employee = Employee.objects.filter()

    return render(request, 'menu/pages/index.html', context={
         'week_menu': week_menu,
         'employee': employee
    })


def progress_page(request):
    return render(request, 'menu/pages/page_progress.html')



def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Verifique se o nome de usuário e senha foram fornecidos
        if not username or not password:
            messages.error(request, 'Usuário ou senha incorretos!')
            return redirect('menu:login')

        user = authenticate(request, username=username, password=password)

        # Se não encontrar o usuário
        if not user:
            messages.error(request, 'Usuário ou senha incorretos!')
            return redirect('menu:login')

        # Fazer login do usuário
        auth_login(request, user)

        messages.success(request, 'Usuário logado com sucesso!')
        return redirect('menu:home')

    # Se o método não for POST, apenas renderize a página de login
    return render(request, 'menu/pages/login.html')