from django.shortcuts import render, redirect 
from .models import WeekMenu, Employee, MealChoice
from django.views import View
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
import copy
from .models import UserChoice, Options
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

        # Aqui estamos assumindo que o campo será algo como 'choice_1', 'choice_2', etc.
        for key in request.POST:
            if key.startswith('choice_'):  # Para garantir que estamos pegando os campos corretos
                # Extrai o ID do menu (que é o dia da semana)
                menu_id = key.split('_')[1]  # Agora temos o id do menu (por exemplo, 1 para segunda-feira)
                option_id = request.POST.get(key)  # Pega o id da opção escolhida para esse dia

                if option_id and option_id != 'null':  # Se o option_id não for vazio ou nulo
                    try:
                        # Buscando a instância da opção para o dia específico
                        option_instance = Options.objects.get(id=option_id)
                    except Options.DoesNotExist:
                        option_instance = None  # Caso a opção não exista

                    if option_instance:
                        # Se a opção foi encontrada, cria ou atualiza a escolha
                        UserChoice.objects.update_or_create(
                            user=request.user,
                            menu_id=menu_id,  # Menu_id representando o dia correto
                            day_of_week=menu_id,  # Usa menu_id para distinguir entre os dias
                            defaults={'option': option_instance},
                        )
                    else:
                        # Se a opção não existe, podemos registrar um erro ou um valor padrão
                        logger.error(f"Option with ID {option_id} does not exist for day {menu_id}.")
                else:  # Se o option_id estiver vazio ou for 'null' (quando desmarcado)
                    # Deleta a escolha existente se o option_id não foi fornecido (desmarcado)
                    user_choice = UserChoice.objects.filter(
                        user=request.user,
                        menu_id=menu_id,  # Menu_id para o dia correto
                        day_of_week=menu_id
                    )
                    if user_choice.exists():
                        user_choice.delete()  # Deleta a escolha existente quando desmarcado

    return redirect('menu:home')
