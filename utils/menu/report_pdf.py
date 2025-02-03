from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.http import HttpResponse
from menu.models import Employee, Company, WeekMenu, Unity, UserChoice
import locale
from collections import defaultdict



def generate_unity_options_pdf(request, file_path, unit_name, unit_address, unit_filter):
    # Obter dados do banco
    week_menu = WeekMenu.objects.filter()
    

    # Criar buffer de memória para o PDF
    buffer = BytesIO()

    # Configuração inicial do PDF
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    # Estilo do PDF
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontSize = 14
    title_style.textColor = colors.black
    title_style.alignment = 1  # Centralizado
    title_style.leading = 16
    title_style.underline = True

    normal_style = styles["BodyText"]
    normal_style.alignment = 1

    red_bold_style = styles["BodyText"].clone('red_bold')
    red_bold_style.textColor = colors.red
    red_bold_style.fontSize = 10
    red_bold_style.fontName = "Helvetica-Bold"
    red_bold_style.alignment = 1

    # Adicionar título principal
    title = f"<u>{unit_name.upper()} - {unit_address.upper()}</u>"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))

    # Cabeçalhos da tabela
    headers = [
        "Prato Principal",
        "Total de Opções",
        "Omelete",
        "Opções - Marmita Fit Frango",
        "Opções - Marmita Fit Carne",
        "Marmita Fit Vegana",
    ]

    # Inicializar dicionário para armazenar dados do menu por dia
    menu_data = []

    for menu in week_menu:
        # Filtrar escolhas por menu e unidade
        choices = UserChoice.objects.filter(
            menu=menu,
            user__employee__unity__unity_name=unit_filter,
            user__employee__is_on_vacations=False,
            user__employee__is_home_office=False
        )

        # Contagem de opções e nomes dos funcionários
        options_summary = defaultdict(list)
        for choice in choices:
            option_name = choice.option.name_option
            employee_name = f"{choice.user.employee.first_name} {choice.user.employee.last_name}"
            options_summary[option_name].append(employee_name)



        # Criar strings formatadas com total de pedidos + nomes para cada tipo de opção
        def format_option(option_name):
            employee_names = options_summary.get(option_name, [])
            total = len(employee_names)
            if total > 0:
                names_str = " / ".join(employee_names)
                return f"{total} - {names_str}"
            return "0"

        omelet_str = format_option("Omelete")
        chicken_str = format_option("Marmita de Frango")
        beef_str = format_option("Marmita de Carne")

        # Adicionar dados do menu atual

        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        week_day = menu.date_meal.strftime("%A").upper() 

        menu_data.append([
            Paragraph(f"{menu.date_meal.strftime('%d.%m')} ({week_day}) - {menu.title.upper()}", normal_style),
            Paragraph(f"<b>{len(choices)}</b>", red_bold_style),
            Paragraph(omelet_str, normal_style),
            Paragraph(chicken_str, normal_style),
            Paragraph(beef_str, normal_style),
            Paragraph("0", normal_style),  # Marmita Vegana (ajuste conforme necessário)
        ]) 

    # Dados completos (cabeçalho + conteúdo)
    data_table = [headers] + menu_data

    # Criação da tabela
    table = Table(data_table, colWidths=[150, 100, 120, 140, 140, 120])
    table.setStyle(TableStyle([ 
        # Estilo do cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('WORDSPACE', (0, 0), (-1, 0), 4),  # Ajuste para quebra de texto

        # Estilo das células
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),

        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)

    # Adicionar as tabelas de segunda a sexta-feira
    weekdays = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    total_data = [
        ['Almoço', 'Omelete', 'Marmitas FIT', 'TOTAL'],
        ['47', '2', '1', '50']
    ]

    elements.append(Spacer(1, 0.3 * inch)) 

    for menu, day in zip(week_menu, weekdays):
        # Título para o dia
        day_title = f"<u>{menu.date_meal.strftime('%d.%m.%Y')} ({day.upper()})</u>"
        day_title_style = styles["Heading1"]
        day_title_style.fontSize = 12
        day_title_style.textColor = colors.black
        day_title_style.alignment = 1  # Centralizado
        day_title_style.bold = True
        day_title_style.underline = True
        day_title_style.backColor = colors.yellow

        elements.append(Paragraph(day_title, day_title_style))

        options_meal_list = ['ALMOÇO', 'OMELETE', 'MARMITAS FIT']

        total_value = 0

        for i, option in enumerate(options_meal_list):
            active_employees = Employee.objects.filter(unity__unity_name=unit_filter, is_on_vacations=False, is_home_office=False)
            
            
            if option == 'ALMOÇO':
                # Funcionários que não pediram nem omelete nem marmita
                no_order_count = active_employees.exclude(
                    user__userchoice__menu=menu,
                    user__userchoice__option__name_option__in=["Omelete", "Marmita de Frango", "Marmita de Carne"]
                ).count()
                total_value = total_value + no_order_count
            elif option == 'OMELETE':
                # Funcionários que pediram omelete
                omelet_count = UserChoice.objects.filter(
                    menu=menu,
                    option__name_option="Omelete",
                    user__employee__unity__unity_name=unit_filter,
                    user__employee__is_on_vacations=False, user__employee__is_home_office=False
                    
                ).count()
                total_value = total_value + omelet_count
            elif option == 'MARMITAS FIT':
                # Funcionários que pediram marmita de frango ou carne
                marmita_count = UserChoice.objects.filter(
                    menu=menu,
                    option__name_option__in=["Marmita de Frango", "Marmita de Carne"],
                    user__employee__unity__unity_name=unit_filter,
                    user__employee__is_on_vacations=False, user__employee__is_home_office=False
                ).count()
                total_value = total_value + marmita_count

        # Tabela do faturamento
        faturamento_data = [
            [f'{unit_name.upper()} - {unit_address}', 'Almoço', '', f'{no_order_count}'],
            [f'{unit_name.upper()} - {unit_address}', 'Omelete', '', f'{omelet_count}'],
            [f'{unit_name.upper()} - {unit_address}', 'Marmitas FIT', '', f'{marmita_count}'],
            ['', 'TOTAL', '', f'{total_value}']
        ]
        
        faturamento_table = Table(faturamento_data, colWidths=[200, 120, 100, 80])
        faturamento_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),  # Retira o fundo amarelo
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Bordas da tabela

            # Última linha em negrito e maior
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (-1, 3), 11),  # Aumenta o tamanho da fonte da última linha
            ('TEXTCOLOR', (3, 3), (3, 3), colors.red),  # Última coluna em vermelho

            # Quebra automática de linha na primeira coluna
            ('WORDWRAP', (0, 0), (0, -1), True),  # Permite quebra de linha na primeira coluna
        ]))

        elements.append(faturamento_table)
        elements.append(Spacer(1, 0.25 * inch))  # Espaço entre as tabelas

    # Construção do PDF
    pdf.build(elements)

    #  Preparar resposta HTTP para download
    buffer.seek(0)  # Voltar para o início do arquivo
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_path}.pdf"'

    # Limpeza do buffer após o envio
    buffer.close()

    return response



def generate_invoicing_report_pdf(request, file_path, first_day, last_day):
    # Criar buffer de memória para o PDF
    buffer = BytesIO()

    # Configuração inicial do PDF
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []

    styles = getSampleStyleSheet()

    # Dicionário de mapeamento dos nomes completos das empresas
    COMPANY_FULL_NAMES = {
        'FG&P': 'FG&P CONSULTORIA ADMINISTRATIVA LTDA.',
        'FCD': 'FCD ARMAZENAGEM E DISTRIBUIÇÃO LTDA',
        'Sustenpack': 'SUSTENPACK EMBALAGENS SUSTENTAVEIS IMPORTACAO E EX',
    }

    # Estilos
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, textColor=colors.black,
                                 alignment=1, backColor=colors.lightgrey, spaceAfter=10, underline=True, leading=16)
    
    total_style = ParagraphStyle('TotalStyle', parent=styles['Normal'], fontSize=12, textColor=colors.black,
                                 fontWeight='bold', alignment=1)
    
    total_style_red = ParagraphStyle('TotalStyleRed', parent=styles['Normal'], fontSize=12, textColor=colors.red,
                                     fontWeight='bold', alignment=1)
    
    centered_style = ParagraphStyle('CenteredStyle', parent=styles['Normal'], fontSize=10, alignment=1)

    # Criando primeira tabela - FATURAMENTO
    title1 = Paragraph(f"FATURAMENTO {first_day} A {last_day}", title_style)
    elements.append(title1)

    employees = Employee.objects.select_related('company').order_by('company__company_name', 'first_name', 'last_name')
    employees_by_company = {}
    total_general = 0  # Inicializa a contagem total

    for employee in employees:
        company_name = employee.company.company_name
        full_company_name = COMPANY_FULL_NAMES.get(company_name, company_name)
        if full_company_name not in employees_by_company:
            employees_by_company[full_company_name] = []
        employees_by_company[full_company_name].append(employee)

    faturamento_data = []
    for company_name, employees in employees_by_company.items():
        active_employees = [e for e in employees if not e.is_on_vacations and not e.is_home_office]
        total_active = len(active_employees)
        total_general += total_active
        faturamento_data.append([company_name, Paragraph(str(total_active), centered_style)])

    # Adiciona linha de total
    faturamento_data.append([Paragraph("", total_style), Paragraph(str(total_general), total_style)])

    tabela_faturamento = Table(faturamento_data, colWidths=[300, 150])
    tabela_faturamento.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (-1, -1), (-1, -1), 12),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTWEIGHT', (0, -1), (-1, -1), 'BOLD'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER')
    ]))

    elements.append(tabela_faturamento)
    elements.append(Spacer(1, 20))

    # Criando segunda tabela - FATURAMENTO (ENTREGA)
    title2 = Paragraph(f"FATURAMENTO (ENTREGA) {first_day} A {last_day}", title_style)
    elements.append(title2)

    entrega_data = []
    total_entrega = 0

    for unity in Unity.objects.all():
        active_employees = Employee.objects.filter(unity=unity, is_on_vacations=False, is_home_office=False)
        total_active = len(active_employees)
        total_entrega += total_active

        # Mapeia o nome da unidade para a descrição completa
        unity_name_map = {
            "Unidade 1": "UNIDADE 1 - Rua João Jose dos Reis, 59",
            "Unidade 2": "UNIDADE 2 - Rua Jose Maria de Melo, 311",
            "Unidade 5 - Novo Galpão": "UNIDADE 5 (GALPÃO NOVO) - Rua Jose Maria de Melo, 157"
        }
        unity_name = unity_name_map.get(unity.unity_name, unity.unity_name)

        entrega_data.append([unity_name, "ALMOÇO (CUBA)", Paragraph(str(total_active), total_style_red)])

    # Adiciona a linha de total
    entrega_data.append([Paragraph("", total_style), Paragraph("", total_style), Paragraph(str(total_entrega), total_style_red)])

    tabela_entrega = Table(entrega_data, colWidths=[300, 150, 100])
    tabela_entrega.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (-1, -1), (-1, -1), 12),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.black),
        ('TEXTCOLOR', (-1, 0), (-1, -2), colors.red),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTWEIGHT', (0, -1), (-1, -1), 'BOLD'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER')
    ]))

    elements.append(tabela_entrega)

    # Construção do PDF
    pdf.build(elements)

    # Preparar resposta HTTP para download
    buffer.seek(0)  # Voltar para o início do arquivo
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_path}.pdf"'

    # Limpeza do buffer após o envio
    buffer.close()

    return response



# Executa a função
if __name__ == '__main__':
    file_path = 'ALMOÇO 30.12.2024 A 03.01.2025 G1' 
    unit_name = "Unidade 1"
    unit_address = "Rua João Jose dos Reis, 59"
    unit_filter = "Unidade 1"
    generate_unity_options_pdf('a', file_path, unit_name, unit_address, unit_filter)