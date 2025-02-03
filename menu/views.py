import json
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404 
from .models import WeekMenu, Employee, Unity, PreviousUserChoice, Restaurant
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import UserChoice, Options, Employee, Company, Shift, Profile, PreviousWeekMenu
import logging
from utils.menu.decorators import user_has_rh_profile, user_has_rh_and_restautant_profile
from utils.menu.report_functions import generate_full_report_function
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from utils.menu.helpers import convert_to_monday, is_the_date_in_seven_days
from utils.menu.report_pdf import generate_unity_options_pdf, generate_invoicing_report_pdf
from django.http import HttpResponse
import os
from django.contrib.auth import update_session_auth_hash
import locale

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


def custom_404_view(request, exception):
    return render(request, 'menu/partials/_page_404.html', status=404)



@login_required
def last_week_menu(request):
    # Obter o cardápio semanal
    week_menus = PreviousWeekMenu.objects.all().order_by('date_meal')
    user_choices = PreviousUserChoice.objects.filter(user=request.user)

    # Criar um dicionário de escolhas do usuário
    user_choices_dict = {choice.menu.id: choice.option for choice in user_choices}

    user_choices_dict_plus = {choice.menu.id: choice.option.id for choice in user_choices}

    # Criar um resumo para cada dia
    resumo = []
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    for menu in week_menus:
        option = user_choices_dict.get(menu.id)
        if option:
            resumo.append({
                'day': menu.date_meal.strftime('%A').capitalize(),  # Nome do dia da semana
                'option': option.name_option,
            })
        else:
            resumo.append({
                'day': menu.date_meal.strftime('%A').capitalize(),
                'option': None,
            })

    return render(request, 'menu/pages/last_week_menu.html', {
        'week_menu': week_menus,
        'resumo': resumo,
        'user_choices': user_choices_dict_plus,
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


# EMPLOYEE PAGE FUNCTIONS

@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def employees_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    shift = request.GET.get('shift', '')  # Nome do campo no formulário é "shift"
    company = request.GET.get('company', '')  # Nome do campo no formulário é "company"
    unity = request.GET.get('unity', '')  # Nome do campo no formulário é "unity"
    
    # Querysets para filtros e colaboradores
    employees_company = Employee.objects.all()
    shifts_company = Shift.objects.all()
    companies = Company.objects.all()
    units = Unity.objects.all()
    profiles = Profile.objects.all()

    # Filtragem da lista de colaboradores
    employees_list = Employee.objects.all()

    if search:
        employees_list = employees_list.filter(first_name__icontains=search)
    if shift:
        employees_list = employees_list.filter(shift__shift=shift)  # Comparando com o nome do turno
    if company:
        employees_list = employees_list.filter(company__company_name=company)
    if unity:
        employees_list = employees_list.filter(unity__unity_name=unity)

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
            'units': units,
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
        unity_id = request.POST.get('unity')
        profile_id = request.POST.get('profile')
        vacation = request.POST.get('vacation') == 'on'
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        home_office = request.POST.get('home_office') == 'on'

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([first_name, last_name, birth_date_str, shift_id, company_id, unity_id, profile_id]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:employees_page')  # Ajuste para a URL correta

        try:
            # Converte a string para um objeto date
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            # Obtém os objetos relacionados de Turno, Empresa e Perfil
            shift = Shift.objects.get(id=shift_id)
            company = Company.objects.get(id=company_id)
            unity = Unity.objects.get(id=unity_id)
            profile = Profile.objects.get(id=profile_id)

            # Cria o objeto Employee
            employee = Employee.objects.create(
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                shift=shift,
                company=company,
                unity=unity,
                profile=profile,
                is_on_vacations=vacation,
                first_day_vacations=start_date if vacation == True else None,
                last_day_vacations=end_date if vacation == True else None,
                is_home_office=home_office,
            )

            # Mensagem de sucesso
            messages.success(request, f"Colaborador {employee.first_name} {employee.last_name} criado com sucesso.")
            return redirect('menu:employees_page')  # Ajuste para a URL correta

        except ValueError:
            messages.error(request, "Data de nascimento inválida. Use o formato AAAA-MM-DD.")
            return redirect('menu:employees_page')

        except (Shift.DoesNotExist, Company.DoesNotExist, Profile.DoesNotExist):
            messages.error(request, "Erro ao buscar turno, empresa, unidade ou perfil.")
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
            'unity_id': employee.unity.id,
            'profile_id': employee.profile.id,
            'birth_date': employee.birth_date.strftime('%Y-%m-%d'),
            'is_on_vacations': employee.is_on_vacations,
            'first_day_vacations': employee.first_day_vacations if employee.is_on_vacations == True else None,
            'last_day_vacations': employee.last_day_vacations if employee.is_on_vacations == True else None,
            'is_home_office': employee.is_home_office,
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
            employee.unity_id = request.POST.get('unity') 
            employee.profile_id = request.POST.get('profile') 
            employee.is_on_vacations = request.POST.get('vacation') == 'on'
            birth_date_str = request.POST.get('birth_date')  
            first_day_vacations_str  = request.POST.get('start_date')
            last_day_vacations_str = request.POST.get('end_date')
            employee.is_home_office = request.POST.get('home_office') == 'on'

            employee.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            if employee.is_on_vacations:
                if not first_day_vacations_str or not last_day_vacations_str:
                    messages.error(request, "Datas de início e fim das férias devem ser preenchidas.")
                    return redirect('menu:employees_page')
                first_day_vacations = datetime.strptime(first_day_vacations_str, '%Y-%m-%d').date()
                last_day_vacations = datetime.strptime(last_day_vacations_str, '%Y-%m-%d').date()
                if first_day_vacations > last_day_vacations:
                    messages.error(request, "A data de início das férias não pode ser posterior à data de fim.")
                    return redirect('menu:employees_page')
                employee.first_day_vacations = first_day_vacations
                employee.last_day_vacations = last_day_vacations
            else:
                employee.first_day_vacations = None
                employee.last_day_vacations = None

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


@user_has_rh_and_restautant_profile
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



@user_has_rh_and_restautant_profile
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

        # Ordenação explícita para garantir a sequência correta
        semana = sorted(semana, key=lambda x: x[0])

        data_alterada = False  # Inicializando a flag para alteração de data

        try:
            for day, dish, side_dish, date_meal, image_meal, qt_options, options_list in semana:
                print(f"Dia: {day}, prato principal: {dish}, guarnição: {side_dish}, data: {date_meal}")  # Log para depuração

                menu_item = WeekMenu.objects.filter(id=day).first()
                if not menu_item:
                    messages.error(request, f"Dia {day} não encontrado no cardápio.")
                    continue

                # Converter a data recebida no POST para um objeto datetime.date
                try:
                    date_meal_obj = datetime.strptime(date_meal, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, f"A data fornecida para o dia {day} está em formato inválido.")
                    continue

    
            # Salvar dados antigos no modelo PreviousWeekMenu
                prev_week_menu = PreviousWeekMenu.objects.filter(id=day).first()
                if prev_week_menu:
                    prev_week_menu.title = menu_item.title
                    prev_week_menu.side_dish = menu_item.side_dish
                    prev_week_menu.date_meal = menu_item.date_meal
                    prev_week_menu.image_meal = menu_item.image_meal
                    prev_week_menu.options.set(menu_item.options.all())
                    prev_week_menu.save() if menu_item.date_meal != date_meal_obj else ...  # Salvar após atualizar os campos
                    print(f"PreviousWeekMenu para o dia {day} atualizado.")  # Log de sucesso
                    
                else:
                    # Se não existir, cria um novo PreviousWeekMenu
                    prev_week_menu = PreviousWeekMenu(
                        id=day,  # Garantir que estamos associando o mesmo índice (dia da semana)
                        title=menu_item.title,
                        side_dish=menu_item.side_dish,
                        date_meal=menu_item.date_meal,
                        image_meal=menu_item.image_meal,
                    )
                    prev_week_menu.save()  if menu_item.date_meal != date_meal_obj else ... # Salvar após atualizar os campos
                    print(f"PreviousWeekMenu para o dia {day} atualizado.")  # Log de sucesso
         

                if menu_item.date_meal != date_meal_obj:
                    data_alterada = True


                # Atualizar campos simples no WeekMenu
                menu_item.title = dish
                menu_item.side_dish = side_dish
                menu_item.date_meal = date_meal_obj

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

                # Salvar as alterações no WeekMenu
                menu_item.save()
                print(f"Menu do dia {day} atualizado com sucesso.")  # Log de sucesso de atualização
         

            print(f"\n===> STATUS FINAL: data_alterada = {data_alterada}")
            
            # Se houver alteração de data, limpar as escolhas anteriores
            if data_alterada:
                PreviousUserChoice.objects.filter().delete()
   
                employees_on_vacations = Employee.objects.filter(is_on_vacations=True)
                
                for employee in employees_on_vacations:
                    if employee.last_day_vacations:  # Verifica se o campo não está nulo
                        week_comeback_vacation = convert_to_monday(employee.last_day_vacations)

                    if is_the_date_in_seven_days(week_comeback_vacation) == True:
                        employee.is_on_vacations = False
                        employee.save()

                 # Atualizar ou salvar o PreviousUserChoice
                for day, dish, side_dish, date_meal, image_meal, qt_options, options_list in semana:

                    menu_item = WeekMenu.objects.filter(id=day).first()
                    if not menu_item:
                        continue  # Pula dias inexistentes no banco

                    # Obter o PreviousWeekMenu correspondente ao dia atual
                    prev_week_menu = PreviousWeekMenu.objects.filter(id=day).first()
                    if not prev_week_menu:
                        continue  # Pula dias sem registros no PreviousWeekMenu

                    user_choices = UserChoice.objects.filter(menu=menu_item)
                    for user_choice in user_choices:
                        prev_user_choice = PreviousUserChoice.objects.filter(user=user_choice.user, menu=prev_week_menu).first()
                        if prev_user_choice:
                            prev_user_choice.option = user_choice.option
                            prev_user_choice.day_of_week = user_choice.day_of_week
                        else:
                            # Se não houver registro anterior, cria um novo
                            prev_user_choice = PreviousUserChoice(
                                user=user_choice.user,
                                menu=prev_week_menu,
                                option=user_choice.option,
                                day_of_week=user_choice.day_of_week,
                            )
                        prev_user_choice.save()

                UserChoice.objects.filter().delete()

                        
                messages.success(request, "Cardápio atualizado com sucesso.")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao atualizar o cardápio: {str(e)}")

        return redirect('menu:weekly_menu')

    return redirect('menu:weekly_menu')






# OPTIONS PAGE FUNCTIONS

@login_required
@user_has_rh_and_restautant_profile
def options_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    title_page_category = 'Opção'
    delete_message = 'Tem certeza de que deseja excluir as opções selecionadas? '
    delete_warning = 'essas opções'
    dynamic_url_name_create = f"menu:create_option"
    dynamic_url_name_edit = f"menu:edit_option"
    dynamic_url_name_delete = f"menu:delete_option"

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
            'title_page_category': title_page_category,
            'delete_message': delete_message,
            'delete_warning': delete_warning,
            'dynamic_url_name_create': dynamic_url_name_create,
            'dynamic_url_name_edit': dynamic_url_name_edit,
            'dynamic_url_name_delete': dynamic_url_name_delete,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )



@login_required
@user_has_rh_and_restautant_profile
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




@user_has_rh_and_restautant_profile
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




@user_has_rh_and_restautant_profile
@login_required
def edit_option(request):
    if request.method == 'POST':
        option_id = request.POST.get('category_id')
        try:
            option = Options.objects.get(id=option_id)
            option.name_option = request.POST.get('name_category')
            option.save()

            messages.success(request, "Opção editada com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Opção não encontrada.")
        return redirect('menu:options_page')
    return redirect('menu:options_page')



@user_has_rh_and_restautant_profile
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



# SHIFTS PAGE FUNCTIONS

@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def shifts_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    title_page_category = 'Turno'
    delete_message = 'Tem certeza de que deseja excluir os turnos selecionados?'
    delete_warning = 'esses turnos'
    dynamic_url_name_create = f"menu:create_shift"
    dynamic_url_name_edit = f"menu:edit_shift"
    dynamic_url_name_delete = f"menu:delete_shift"

    # Querysets para filtros e colaboradores
    shifts = Shift.objects.all()
    
    # Filtragem da lista de colaboradores
    shifts_list = Shift.objects.all()

    if search:
        shifts_list = shifts_list.filter(shift__icontains=search)

    # Paginação
    paginator = Paginator(shifts_list, 10)  # Exibe 10 colaboradores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/shifts.html',
        context={
            'page_obj': shifts_list,
            'title_page_category': title_page_category,
            'delete_message': delete_message,
            'delete_warning': delete_warning,
            'dynamic_url_name_create': dynamic_url_name_create,
            'dynamic_url_name_edit': dynamic_url_name_edit,
            'dynamic_url_name_delete': dynamic_url_name_delete,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )



@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_shift(request):
    if request.method == 'POST':
        name_shift = request.POST.get('name_category')
    

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([name_shift]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:create_shift')  # Ajuste para a URL correta

        try:

            # Cria o objeto Employee
            shift = Shift.objects.create(
                shift=name_shift,
            )

            # Mensagem de sucesso
            messages.success(request, f"Turno {shift.shift} criada com sucesso.")
            return redirect('menu:shifts_page')  # Ajuste para a URL correta


        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('menu:shifts_page') 

    return redirect('menu:shifts_page')   # Ajuste para a URL correta



@user_has_rh_profile
@login_required
def get_shifts(request, shift_id):
    try:
        shift = get_object_or_404(Shift, id=shift_id)
        data = {
            'id': shift.id,
            'shift': shift.shift,
        }
        
        return JsonResponse(data)
    except Shift.DoesNotExist:
        return JsonResponse({'error': 'Turno não encontrado'}, status=404)



@user_has_rh_profile
@login_required
def edit_shift(request):
    if request.method == 'POST':
        shift_id = request.POST.get('category_id')
        
        try:
            shift = Shift.objects.get(id=shift_id)
            shift.shift = request.POST.get('name_category')

            shift.save()

            messages.success(request, "Turno editado com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Turno não encontrado.")
        return redirect('menu:shifts_page')
    return redirect('menu:shifts_page')


@user_has_rh_profile
@csrf_exempt
@login_required
def delete_shift(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Obtém os dados enviados no corpo da requisição
            shift_ids = data.get('shift_ids', [])  # IDs das opções selecionadas

            if shift_ids:
                # Deleta as opções com os IDs fornecidos
                Shift.objects.filter(id__in=shift_ids).delete()
                return JsonResponse({'message': 'Turnos excluídos com sucesso!'}, status=200)
            return JsonResponse({'error': 'Nenhum turno selecionado.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)




# COMPANIES PAGE FUNCTIONS

@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def companies_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    title_page_category = 'Empresa'
    delete_message = 'Tem certeza de que deseja excluir as empresas selecionadas?'
    delete_warning = 'essas empresas'
    dynamic_url_name_create = f"menu:create_company"
    dynamic_url_name_edit = f"menu:edit_company"
    dynamic_url_name_delete = f"menu:delete_company"

    # Querysets para filtros e colaboradores
    companies = Company.objects.all()
    
    # Filtragem da lista de colaboradores
    companies_list = Company.objects.all()

    if search:
        companies_list = companies_list.filter(company_name__icontains=search)

    # Paginação
    paginator = Paginator(companies_list, 10)  # Exibe 10 colaboradores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/companies.html',
        context={
            'page_obj': companies_list,
            'title_page_category': title_page_category,
            'delete_message': delete_message,
            'delete_warning': delete_warning,
            'dynamic_url_name_create': dynamic_url_name_create,
            'dynamic_url_name_edit': dynamic_url_name_edit,
            'dynamic_url_name_delete': dynamic_url_name_delete,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )



@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_company(request):
    if request.method == 'POST':
        name_company = request.POST.get('name_category')
    

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([name_company]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:create_company')  # Ajuste para a URL correta

        try:

            # Cria o objeto Employee
            company = Company.objects.create(
                company_name=name_company,
            )

            # Mensagem de sucesso
            messages.success(request, f"Empresa {company.company_name} criada com sucesso.")
            return redirect('menu:companies_page')  # Ajuste para a URL correta


        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('menu:companies_page') 

    return redirect('menu:companies_page')   # Ajuste para a URL correta




@user_has_rh_profile
@login_required
def get_companies(request, company_id):
    try:
        company = get_object_or_404(Company, id=company_id)
        data = {
            'id': company.id,
            'company': company.company_name,
        }
        
        return JsonResponse(data)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Empresa não encontrada'}, status=404)


@user_has_rh_profile
@login_required
def edit_company(request):
    if request.method == 'POST':
        company_id = request.POST.get('category_id')
        
        try:
            company = Company.objects.get(id=company_id)
            company.company_name = request.POST.get('name_category')

            company.save()

            messages.success(request, "Empresa editada com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Empresa não encontrada.")
        return redirect('menu:companies_page')
    return redirect('menu:companies_page')



@user_has_rh_profile
@csrf_exempt
@login_required
def delete_company(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Obtém os dados enviados no corpo da requisição
            company_ids = data.get('company_ids', [])  # IDs das empresas selecionadas

            if company_ids:
                # Deleta as empresas com os IDs fornecidos
                Company.objects.filter(id__in=company_ids).delete()
                return JsonResponse({'message': 'Empresas excluídas com sucesso!'}, status=200)
            return JsonResponse({'error': 'Nenhuma empresa selecionado.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)



# UNITS PAGE FUNCTIONS

@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def units_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"
    title_page_category = 'Unidade'
    delete_message = 'Tem certeza de que deseja excluir as unidades selecionadas?'
    delete_warning = 'essas unidades'
    dynamic_url_name_create = f"menu:create_unity"
    dynamic_url_name_edit = f"menu:edit_unity"
    dynamic_url_name_delete = f"menu:delete_unity"

    # Querysets para filtros e colaboradores
    units = Unity.objects.all()
    
    # Filtragem da lista de colaboradores
    units_list = Unity.objects.all()

    if search:
        units_list = units_list.filter(unity_name__icontains=search)

    # Paginação
    paginator = Paginator(units_list, 10)  # Exibe 10 colaboradores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/units.html',
        context={
            'page_obj': units_list,
            'title_page_category': title_page_category,
            'delete_message': delete_message,
            'delete_warning': delete_warning,
            'dynamic_url_name_create': dynamic_url_name_create,
            'dynamic_url_name_edit': dynamic_url_name_edit,
            'dynamic_url_name_delete': dynamic_url_name_delete,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )



@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_unity(request):
    if request.method == 'POST':
        name_unity = request.POST.get('name_category')
    

        # Valida se todos os campos obrigatórios foram preenchidos
        if not all([name_unity]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('menu:create_unity')  # Ajuste para a URL correta

        try:

            # Cria o objeto Employee
            unity = Unity.objects.create(
                unity_name=name_unity,
            )

            # Mensagem de sucesso
            messages.success(request, f"Unidade {unity.unity_name} criada com sucesso.")
            return redirect('menu:units_page')  # Ajuste para a URL correta


        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect('menu:units_page') 

    return redirect('menu:units_page')   # Ajuste para a URL correta




@user_has_rh_profile
@login_required
def get_units(request, unity_id):
    try:
        unity = get_object_or_404(Unity, id=unity_id)
        data = {
            'id': unity.id,
            'unity': unity.unity_name,
        }
        
        return JsonResponse(data)
    except unity.DoesNotExist:
        return JsonResponse({'error': 'Unidade não encontrada'}, status=404)




@user_has_rh_profile
@login_required
def edit_unity(request):
    if request.method == 'POST':
        unity_id = request.POST.get('category_id')
        
        try:
            unity = Unity.objects.get(id=unity_id)
            unity.unity_name = request.POST.get('name_category')

            unity.save()

            messages.success(request, "Unidade editada com sucesso.")
        except Employee.DoesNotExist:
            messages.error(request, "Unidade não encontrada.")
        return redirect('menu:units_page')
    return redirect('menu:units_page')



@user_has_rh_profile
@csrf_exempt
@login_required
def delete_unity(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Obtém os dados enviados no corpo da requisição
            unity_ids = data.get('unity_ids', [])  # IDs das unidades selecionadas

            if unity_ids:
                # Deleta as unidades com os IDs fornecidos
                Unity.objects.filter(id__in=unity_ids).delete()
                return JsonResponse({'message': 'Unidades excluídas com sucesso!'}, status=200)
            return JsonResponse({'error': 'Nenhuma unidade selecionado.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)




@login_required
@user_has_rh_and_restautant_profile
def reports_page(request):
    
    weekly_menu = WeekMenu.objects.filter()
    user_choices = UserChoice.objects.select_related('user', 'menu', 'option').all()
    companies = Company.objects.filter()
    units = Unity.objects.filter()
    employees = Employee.objects.filter()

    choices_by_company = (
        Employee.objects
        .values('company__company_name')  # Agrupa por empresa
        .annotate(
            total_options=Count(
                'user__userchoice__option', 
                filter=Q(user__userchoice__isnull=False)
            )
        )  # Conta as opções ou retorna 0 se não houver
        .order_by('company__company_name')  # Ordena pelo nome da empresa
    )

    # Obter o total de funcionários não de férias por empresa
    employees_no_vacation = (
        Employee.objects
        .values('company__company_name')  # Agrupa por empresa
        .annotate(
            employees_no_vacation_total=Count(
                'id',
                filter=Q(is_on_vacations=False, is_home_office=False)
            )
        )
        .order_by('company__company_name')  # Ordena pelo nome da empresa
    )


    # Classificar empresas por unidade de entrega
    UNIT_MAPPING = {
        'Unidade 01 - Rua João Jose dos Reis, 59': ['Unidade 1'],
        'Unidade 02 - Rua Jose Maria de Melo, 311': ['Unidade 2'],
        'Unidade 05 (GALPÃO NOVO) - Rua Jose Maria de Melo, 157': ['Unidade 5 - Novo Galpão'],
    }

    # Contabilizar funcionários por unidade de entrega
    employees_by_unit = {}
    for unit, units in UNIT_MAPPING.items():
        employees_by_unit[unit] = Employee.objects.filter(
            unity__unity_name__in=units,
            is_on_vacations=False, is_home_office=False  # Apenas funcionários não de férias
        ).count()


    # Juntar os resultados em um único dicionário
    company_data = {}
    for choice in choices_by_company:
        company_name = choice['company__company_name']
        company_data[company_name] = {
            'total_options': choice['total_options'],
            'employees_no_vacation_total': 0,  # Valor padrão
        }

    for employee in employees_no_vacation:
        company_name = employee['company__company_name']
        if company_name in company_data:
            company_data[company_name]['employees_no_vacation_total'] = employee['employees_no_vacation_total']
        else:
            company_data[company_name] = {
                'total_options': 0,  # Caso não tenha opções associadas
                'employees_no_vacation_total': employee['employees_no_vacation_total'],
            }

    total_employees_by_unit = sum(employees_by_unit.values())

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/reports.html',
        context={
            'weekly_menu': weekly_menu,
            'company_data': company_data,
            'employees_by_unit': employees_by_unit,
            'total_employees_by_unit': total_employees_by_unit,
            'request': request,
        }
    )



@user_has_rh_and_restautant_profile
@login_required
def generate_full_report_button(request):
    return generate_full_report_function(request)
    

@user_has_rh_and_restautant_profile
@login_required
def generate_pdf_report_unit_one(request):
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")

    file_path = f'ALMOÇO {first_day} A {last_day} G1' 
    unit_name= "Unidade 1"
    unit_address="Rua João Jose dos Reis, 59"
    unit_filter="Unidade 1"

    # Gera o PDF
    return generate_unity_options_pdf(request, file_path, unit_name, unit_address, unit_filter)


@user_has_rh_and_restautant_profile
@login_required
def generate_pdf_report_unit_two(request):
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")

    file_path = f'ALMOÇO {first_day} A {last_day} G2' 
    unit_name= "Unidade 2"
    unit_address="Rua Jose Maria de Melo, 311"
    unit_filter="Unidade 2"

    # Gera o PDF
    return generate_unity_options_pdf(request, file_path, unit_name, unit_address, unit_filter)



@user_has_rh_and_restautant_profile
@login_required
def generate_pdf_report_unit_five(request):
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")

    file_path = f'ALMOÇO {first_day} A {last_day} G5' 
    unit_name= "UNIDADE 5"
    unit_address="Rua Jose Maria de Melo, 157"
    unit_filter="Unidade 5 - Novo Galpão"

    # Gera o PDF
    return generate_unity_options_pdf(request, file_path, unit_name, unit_address, unit_filter)



@user_has_rh_and_restautant_profile
@login_required
def generate_pdf_invoicing_report(request):
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")

    file_path = f'FATURAMENTO {first_day} A {last_day}' 

    # Gera o PDF
    return generate_invoicing_report_pdf(request, file_path, first_day, last_day)




@login_required
def profile_page(request):
    # Obter o cardápio semanal
    employee_data = Employee.objects.filter(user=request.user)
    restaurant_data = Restaurant.objects.filter(user=request.user)


    return render(request, 'menu/pages/profile.html', {
        'employee_data': employee_data[0] if employee_data else ...,
        'restaurant_data': restaurant_data[0] if restaurant_data else ...,
    })



@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Verificar se as senhas coincidem
        if new_password != confirm_password:
            messages.error(request, 'As senhas não coincidem!')
        else:
            # Verificar se a senha atual está correta
            user = request.user
            if not user.check_password(current_password):
                messages.error(request, 'Senha atual incorreta!')
            else:
                # Alterar a senha
                user.set_password(new_password)
                user.save()

                # Atualizar a sessão do usuário para que ele não seja desconectado após a mudança de senha
                update_session_auth_hash(request, user)

                # Mensagem de sucesso
                messages.success(request, 'Senha alterada com sucesso!')

        return redirect('menu:profile_page')
    



# RESTAURANT PAGE FUNCTIONS

@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def restaurant_page(request):

# Obter filtros do GET
    search = request.GET.get('search', '')  # Nome do campo no formulário é "search"

    
    # Querysets para filtros e restaurantes
    restaurants = Restaurant.objects.all()
    profiles = Profile.objects.all()

    # Filtragem da lista de restaurantes
    restaurants_list = Restaurant.objects.all()

    if search:
        restaurants_list = restaurants_list.filter(name_restaurant__icontains=search)

    # Paginação
    paginator = Paginator(restaurants_list, 10)  # Exibe 10 restaurantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/restaurants.html',
        context={
            'restaurants': restaurants,
            'page_obj': page_obj,
            'request': request,  # Passa request para o template (opcional, para reutilizar filtros)
        }
    )


@login_required
@user_has_rh_profile  # Restringe o acesso a usuários com perfil RH
def create_restaurant(request):
    if request.method == 'POST':
        name_restaurant = request.POST.get('full_name')
        short_name = request.POST.get('short_name')

        try:
            profile = Profile.objects.get(profile='Restaurante')  # Pega um único Profile
        except Profile.DoesNotExist:
            messages.error(request, "Erro: O perfil 'Restaurante' não existe.")
            return redirect('menu:restaurant_page')

        # Cria o objeto Restaurant
        restaurant = Restaurant.objects.create(
            name_restaurant=name_restaurant,
            short_name=short_name,
            profile=profile
        )

        # Mensagem de sucesso
        messages.success(request, f"Restaurante {restaurant.short_name} criado com sucesso.")
        return redirect('menu:restaurant_page')  # Ajuste para a URL correta
    
    return redirect('menu:restaurant_page')   # Ajuste para a URL correta




@user_has_rh_profile
@login_required
def get_restaurants(request, restaurant_id):
    try:
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        data = {
            'id': restaurant.id,
            'full_name': restaurant.name_restaurant,
            'short_name': restaurant.short_name,
        }
        
        return JsonResponse(data)
    except Restaurant.DoesNotExist:
        return JsonResponse({'error': 'Restaurante não encontrado'}, status=404)


@user_has_rh_profile
@login_required
def edit_restaurant(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')


        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            restaurant.name_restaurant = request.POST.get('full_name')
            restaurant.short_name = request.POST.get('short_name')

            restaurant.save()

            messages.success(request, "Restaurante editado com sucesso.")
        except Restaurant.DoesNotExist:
            messages.error(request, "Restaurante não encontrado.")
        return redirect('menu:restaurant_page')
        
    return redirect('menu:restaurant_page')



@user_has_rh_profile
@csrf_exempt
@login_required
def delete_restaurant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Obtém os dados enviados no corpo da requisição
            restaurant_ids = data.get('restaurant_ids', [])  # IDs dos restaurantes selecionados


            if restaurant_ids:
                restaurants = Restaurant.objects.filter(id__in=restaurant_ids)
                for restaurant in restaurants:
                    user = restaurant.user
                    restaurant.delete()  # Deleta o Employee (e automaticamente o User por causa do on_delete=models.CASCADE)
                    if user:
                        user.delete()  # Deleta o User caso não tenha sido deletado automaticamente

                    Restaurant.objects.filter(id__in=restaurant_ids).delete()
                return JsonResponse({'message': 'Restaurantes excluídos com sucesso!'}, status=200)
            return JsonResponse({'error': 'Nenhum restaurante selecionado.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)




@login_required
@user_has_rh_and_restautant_profile
def reports_comparative_page(request):
    
    weekly_menu = WeekMenu.objects.filter()
    user_choices = UserChoice.objects.select_related('user', 'menu', 'option').all()
    companies = Company.objects.filter()
    units = Unity.objects.filter()
    employees = Employee.objects.filter()

    choices_by_company = (
        Employee.objects
        .values('company__company_name')  # Agrupa por empresa
        .annotate(
            total_options=Count(
                'user__userchoice__option', 
                filter=Q(user__userchoice__isnull=False)
            )
        )  # Conta as opções ou retorna 0 se não houver
        .order_by('company__company_name')  # Ordena pelo nome da empresa
    )

    # Obter o total de funcionários não de férias por empresa
    employees_no_vacation = (
        Employee.objects
        .values('company__company_name')  # Agrupa por empresa
        .annotate(
            employees_no_vacation_total=Count(
                'id',
                filter=Q(is_on_vacations=False, is_home_office=False)
            )
        )
        .order_by('company__company_name')  # Ordena pelo nome da empresa
    )


    # Classificar empresas por unidade de entrega
    UNIT_MAPPING = {
        'Unidade 01 - Rua João Jose dos Reis, 59': ['Unidade 1'],
        'Unidade 02 - Rua Jose Maria de Melo, 311': ['Unidade 2'],
        'Unidade 05 (GALPÃO NOVO) - Rua Jose Maria de Melo, 157': ['Unidade 5 - Novo Galpão'],
    }

    # Contabilizar funcionários por unidade de entrega
    employees_by_unit = {}
    for unit, units in UNIT_MAPPING.items():
        employees_by_unit[unit] = Employee.objects.filter(
            unity__unity_name__in=units,
            is_on_vacations=False, is_home_office=False  # Apenas funcionários não de férias
        ).count()


    # Juntar os resultados em um único dicionário
    company_data = {}
    for choice in choices_by_company:
        company_name = choice['company__company_name']
        company_data[company_name] = {
            'total_options': choice['total_options'],
            'employees_no_vacation_total': 0,  # Valor padrão
        }

    for employee in employees_no_vacation:
        company_name = employee['company__company_name']
        if company_name in company_data:
            company_data[company_name]['employees_no_vacation_total'] = employee['employees_no_vacation_total']
        else:
            company_data[company_name] = {
                'total_options': 0,  # Caso não tenha opções associadas
                'employees_no_vacation_total': employee['employees_no_vacation_total'],
            }

    total_employees_by_unit = sum(employees_by_unit.values())

    # Renderizar template com contexto
    return render(
        request,
        'menu/pages/comparative_report.html',
        context={
            'weekly_menu': weekly_menu,
            'company_data': company_data,
            'employees_by_unit': employees_by_unit,
            'total_employees_by_unit': total_employees_by_unit,
            'request': request,
        }
    )

