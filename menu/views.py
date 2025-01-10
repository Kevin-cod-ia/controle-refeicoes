from django.shortcuts import render, redirect 
from .models import WeekMenu, Employee, MealChoice
from django.views import View
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
import copy
from .models import UserChoice
import logging

logger = logging.getLogger(__name__)
# Create your views here.

@login_required
def home(request):
    # Obter o cardápio semanal
    week_menus = WeekMenu.objects.prefetch_related('userchoice_set').all()
    user_choices = UserChoice.objects.filter(user=request.user)

    # Obter as escolhas do usuário
    user_choices_dict = {choice.menu.id: choice.option.id for choice in user_choices}


    if request.method == 'POST':
        for menu in week_menus:
            menu_id = menu.id
            option_id = request.POST.get(f'choice_{menu_id}')
            
            # Verificar se a escolha já existe, caso contrário, criar uma nova
            if option_id:
                choice, created = UserChoice.objects.update_or_create(
                    user=request.user,
                    menu=menu,
                    defaults={'option_id': option_id},
                )


    return render(request, 'menu/pages/index.html', {
        'week_menus': week_menus,
        'week_menu': week_menus,
        'user_choices': user_choices_dict,
    })


@login_required
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



def logout(request):
    # Efetua o logout do usuário
    auth_logout(request)


    # Redireciona para a página de login
    return redirect('menu:login')




@login_required
def save_user_choices(request):
    if request.method == 'POST':
        logger.info(request.POST)
        menu_id = request.POST.get('menu_id')  # Supondo que você tenha uma chave 'menu_id'
        
        # Aqui estamos assumindo que o campo será algo como 'choice_1', 'choice_2', etc.
        for key in request.POST:
            if key.startswith('choice_'):  # Para garantir que estamos pegando os campos corretos
                menu_id = key.split('_')[1]  # Extrai o menu_id da chave
                option_id = request.POST.get(key)  # Pega o id da opção escolhida
                if menu_id and option_id:
                    UserChoice.objects.update_or_create(
                        user=request.user,
                        menu_id=menu_id,
                        defaults={'option_id': option_id},
                    )

    return redirect('menu:home')