import json
from django.shortcuts import render, redirect, get_object_or_404 
from .models import WeekMenu, Employee
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import UserChoice, Options, Employee, Company, Shift, Profile
import logging
from utils.menu.decorators import user_has_rh_profile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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


@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def employees_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    shift = request.GET.get('shift', '')  # Nome do campo no formulário é "shift"
    company = request.GET.get('company', '')  # Nome do campo no formulário é "company"
    
    # Querysets para filtros e colaboradores
    employees_company = Employee.objects.all()
    shifts_company = Shift.objects.all()
    companies = Company.objects.all()
    profiles = Profile.objects.all()

    # Filtragem da lista de colaboradores
    employees_list = Employee.objects.all()

    if search:
        employees_list = employees_list.filter(first_name__icontains=search)
    if shift:
        employees_list = employees_list.filter(shift__shift=shift)  # Comparando com o nome do turno
    if company:
        employees_list = employees_list.filter(company__company_name=company)

    # Paginação
    paginator = Paginator(employees_list, 10)  # Exibe 10 colaboradores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/employees.html',
        context={
            'employees_company': employees_company,
            'shifts_company': shifts_company,
            'companies': companies,
            'page_obj': page_obj,
            'profiles': profiles,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )


@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_employee(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_date_str = request.POST.get('birth_date')  # Recebido como string
        shift_id = request.POST.get('shift')
        company_id = request.POST.get('company')
        profile_id = request.POST.get('profile')
        vacation = request.POST.get('vacation') == 'on'

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([first_name, last_name, birth_date_str, shift_id, company_id, profile_id]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:employees_page')  # Ajuste para a URL correta

        try:
            # Converte a string para um objeto date
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            # Obtém os objetos relacionados de Turno, Empresa e Perfil
            shift = Shift.objects.get(id=shift_id)
            company = Company.objects.get(id=company_id)
            profile = Profile.objects.get(id=profile_id)

            # Cria o objeto Employee
            employee = Employee.objects.create(
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                shift=shift,
                company=company,
                profile=profile,
                is_on_vacations=vacation,
            )

            # Mensagem de sucesso
            messages.success(request, f"Colaborador {employee.first_name} {employee.last_name} criado com sucesso.")
            return redirect('menu:employees_page')  # Ajuste para a URL correta

        except ValueError:
            messages.error(request, "Data de nascimento inválida. Use o formato AAAA-MM-DD.")
            return redirect('menu:employees_page')

        except (Shift.DoesNotExist, Company.DoesNotExist, Profile.DoesNotExist):
            messages.error(request, "Erro ao buscar turno, empresa ou perfil.")
            return redirect('menu:employees_page')

        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('menu:employees_page')

    # Caso o método seja GET, redirecione para a lista de funcionários
    return redirect('menu:employees_page')  # Ajuste para a URL correta


@user_has_rh_profile
@login_required
def get_employee(request, employee_id):
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        data = {
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'shift_id': employee.shift.id,
            'company_id': employee.company.id,
            'profile_id': employee.profile.id,
            'birth_date': employee.birth_date.strftime('%Y-%m-%d'),
            'is_on_vacations': employee.is_on_vacations,
        }
        
        return JsonResponse(data)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Colaborador não encontrado'}, status=404)



@user_has_rh_profile
@login_required
def edit_employee(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            employee.first_name = request.POST.get('first_name')
            employee.last_name = request.POST.get('last_name')
            employee.shift_id = request.POST.get('shift') 
            employee.company_id = request.POST.get('company') 
            employee.profile_id = request.POST.get('profile') 
            employee.is_on_vacations = request.POST.get('vacation') == 'on'
            birth_date_str = request.POST.get('birth_date')  

            employee.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            employee.save()

            messages.success(request, "Colaborador editado com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Colaborador não encontrado.")
        return redirect('menu:employees_page')
    return redirect('menu:employees_page')


@user_has_rh_profile
@csrf_exempt
@login_required
def delete_employee(request):
     if request.method == 'POST':
        data = json.loads(request.body)
        employee_ids = data.get('employee_ids', [])

        if employee_ids:
            try:
                # Exclui os funcionários e seus usuários associados
                employees = Employee.objects.filter(id__in=employee_ids)
                for employee in employees:
                    user = employee.user
                    employee.delete()  # Deleta o Employee (e automaticamente o User por causa do on_delete=models.CASCADE)
                    if user:
                        user.delete()  # Deleta o User caso não tenha sido deletado automaticamente

                return JsonResponse({'message': 'Funcionários excluídos com sucesso!'})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({'error': 'Nenhum colaborador selecionado'}, status=400)


@user_has_rh_profile
@login_required
def weekly_menu(request):
    week_menu = WeekMenu.objects.prefetch_related('userchoice_set').all()
    length_options_week_menu = []
    options_week_menu = []
    options = Options.objects.filter()

    for menu in week_menu:
        length_options_week_menu.append(len(menu.options.all()))
        options_week_menu.append(menu.options.all())

    # Passando o valor para o template (exemplo, primeira opção de segunda-feira)
    options_monday = [option for option in options_week_menu[0] ]
    options_tuesday = [option for option in options_week_menu[1] ]
    options_wednesday = [option for option in options_week_menu[2] ]
    options_thursday = [option for option in options_week_menu[3] ]
    options_friday = [option for option in options_week_menu[4] ]


    return render(request, 'menu/pages/weekly_menu.html', context= {
        'week_menu': week_menu,
        'options_week_menu': length_options_week_menu,
        'options_monday': options_monday, 
        'options_tuesday': options_tuesday, 
        'options_wednesday': options_wednesday, 
        'options_thursday': options_thursday, 
        'options_friday': options_friday, 
        'options': options,
    })



@user_has_rh_profile
@login_required
def update_weekly_menu(request):

    def get_options(day):
        return [
            value for key, value in request.POST.items()
            if key.startswith(f"{day}-option-")
        ]
    
    if request.method == 'POST':
        semana = [
            (1, request.POST.get('prato_principal_segunda'), request.POST.get('guarnicao_segunda'), request.POST.get('data_segunda'), request.FILES.get('foto_segunda'), request.POST.get('qt_opcoes_segunda'), get_options('segunda')),
            (2, request.POST.get('prato_principal_terca'), request.POST.get('guarnicao_terca'), request.POST.get('data_terca'), request.FILES.get('foto_terca'), request.POST.get('qt_opcoes_terca'), get_options('terca')),
            (3, request.POST.get('prato_principal_quarta'), request.POST.get('guarnicao_quarta'), request.POST.get('data_quarta'), request.FILES.get('foto_quarta'), request.POST.get('qt_opcoes_quarta'), get_options('quarta')),
            (4, request.POST.get('prato_principal_quinta'), request.POST.get('guarnicao_quinta'), request.POST.get('data_quinta'), request.FILES.get('foto_quinta'), request.POST.get('qt_opcoes_quinta'), get_options('quinta')),
            (5, request.POST.get('prato_principal_sexta'), request.POST.get('guarnicao_sexta'), request.POST.get('data_sexta'), request.FILES.get('foto_sexta'), request.POST.get('qt_opcoes_sexta'), get_options('sexta')),
        ]

        try:
            for day, dish, side_dish, date_meal, image_meal, qt_options, options_list in semana:
                menu_item = WeekMenu.objects.filter(id=day).first()
                if not menu_item:
                    messages.error(request, f"Dia {day} não encontrado no cardápio.")
                    continue

                # Atualizar campos simples
                menu_item.title = dish
                menu_item.side_dish = side_dish
                menu_item.date_meal = date_meal

                # Tratamento da imagem
                if image_meal:
                    if not image_meal.content_type.startswith('image/'):
                        messages.error(request, f"Arquivo enviado para o dia {day} não é uma imagem válida.")
                        continue
                    if image_meal.size > 5 * 1024 * 1024:  # Limite de 5MB
                        messages.error(request, f"A imagem enviada para o dia {day} excede o tamanho permitido de 5MB.")
                        continue
                    menu_item.image_meal = image_meal
                    

                # Atualizar ManyToManyField com IDs de opções
                if options_list:
                    menu_item.options.set(options_list)

                menu_item.save()

            messages.success(request, "Cardápio atualizado com sucesso.")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao atualizar o cardápio: {str(e)}")

        return redirect('menu:weekly_menu')

    return redirect('menu:weekly_menu')




@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def options_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    
    # Querysets para filtros e colaboradores
    options = Options.objects.all()
    
    # Filtragem da lista de colaboradores
    options_list = Options.objects.all()

    if search:
        options_list = options_list.filter(name_option__icontains=search)

    # Paginação
    paginator = Paginator(options_list, 10)  # Exibe 10 colaboradores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/options.html',
        context={
            'page_obj': options_list,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )





@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_option(request):
    if request.method == 'POST':
        name_option = request.POST.get('name_category')
    

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([name_option]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:create_option')  # Ajuste para a URL correta

        try:

            # Cria o objeto Employee
            option = Options.objects.create(
                name_option=name_option,
            )

            # Mensagem de sucesso
            messages.success(request, f"Opção {option.name_option} criada com sucesso.")
            return redirect('menu:options_page')  # Ajuste para a URL correta


        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('menu:options_page') 

    return redirect('menu:options_page')   # Ajuste para a URL correta



@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def reports_page(request):
    
    weekly_menu = WeekMenu.objects.filter()
    user_choices = UserChoice.objects.filter()

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/reports.html',
        context={
            'request': request,
        }
    )




@user_has_rh_profile
@login_required
def get_options(request, option_id):
    try:
        option = get_object_or_404(Options, id=option_id)
        data = {
            'id': option.id,
            'name_option': option.name_option,
        }
        
        return JsonResponse(data)
    except Options.DoesNotExist:
        return JsonResponse({'error': 'Opção não encontrada'}, status=404)




@user_has_rh_profile
@login_required
def edit_option(request):
    if request.method == 'POST':
        option_id = request.POST.get('option_id')
        try:
            option = Options.objects.get(id=option_id)
            option.name_option = request.POST.get('name_option')
            option.save()

            messages.success(request, "Opção editada com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Opção não encontrada.")
        return redirect('menu:options_page')
    return redirect('menu:options_page')



@user_has_rh_profile
@csrf_exempt
@login_required
def delete_option(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Obtém os dados enviados no corpo da requisição
            option_ids = data.get('option_ids', [])  # IDs das opções selecionadas

            if option_ids:
                # Deleta as opções com os IDs fornecidos
                Options.objects.filter(id__in=option_ids).delete()
                return JsonResponse({'message': 'Opções excluídas com sucesso!'}, status=200)
            return JsonResponse({'error': 'Nenhuma opção selecionada.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)


