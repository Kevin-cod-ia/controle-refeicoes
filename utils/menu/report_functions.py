from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from django.http import HttpResponse
from menu.models import Employee, Company, WeekMenu, Unity


def generate_full_report_function(request):
    wb = Workbook()
    ws = wb.active
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")
    ws.title = f"{first_day} a {last_day}"

    # Adiciona cabeçalho da tabela de funcionários
    headers = ['Unidade', 'Turno', 'Nome da Empresa', 'Nome do Funcionário']
    ws.append([f"  {header}  " for header in headers])  # Adiciona espaçamento horizontal

    # Aplica a formatação do cabeçalho
    for cell in ws[1]:
        cell.font = Font(name="Verdana", size=10, bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    # Mapeia os nomes completos das empresas
    COMPANY_FULL_NAMES = {
        'FG&P': 'FG&P CONSULTORIA ADMINISTRATIVA LTDA.',
        'FCD': 'FCD ARMAZENAGEM E DISTRIBUIÇÃO LTDA',
        'Sustenpack': 'SUSTENPACK EMBALAGENS SUSTENTAVEIS IMPORTACAO E EX',
    }

    row = 2  # Começa a adicionar os dados a partir da segunda linha

    # Agrupar os funcionários por empresa
    employees = Employee.objects.select_related('company', 'unity', 'shift').order_by('company__company_name', 'first_name', 'last_name')
    employees_by_company = {}

    for employee in employees:
        company_name = employee.company.company_name
        full_company_name = COMPANY_FULL_NAMES.get(company_name, company_name)
        if full_company_name not in employees_by_company:
            employees_by_company[full_company_name] = []
        employees_by_company[full_company_name].append(employee)

    # Adiciona os funcionários à planilha
    for full_company_name, employees in employees_by_company.items():
        total_employees = len(employees)

        for employee in employees:
            fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid") if employee.is_on_vacations else None

            # Adiciona os dados do funcionário na planilha
            ws.append([ 
                f"  {employee.unity.unity_name.upper()}  ",
                f"  {employee.shift.shift.upper()}  ",
                f"  {full_company_name.upper()}  ",
                f"  {employee.__str__().upper()}  "
            ])

            # Aplica estilo às células da linha
            for cell in ws[row]:
                cell.font = Font(name="Verdana", size=10)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                if fill:
                    cell.fill = fill

            row += 1

        # Adiciona a linha de total de funcionários
        ws.append(['', '', f"  {full_company_name.upper()}  ", f"  TOTAL: {total_employees} FUNCIONÁRIOS  "])
        for cell in ws[row]:
            cell.font = Font(name="Verdana", size=10, bold=True)
            cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        row += 1

    # Aplica o filtro na tabela
    filter_range = f"A1:D{row - 1}"
    ws.auto_filter.ref = filter_range

    # Adiciona espaço antes da seção de faturamento
    row += 9

    # Adiciona título "Faturamento"
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    title_cell = ws.cell(row=row, column=1, value=f"FATURAMENTO  {first_day} A {last_day}")
    title_cell.font = Font(name="Verdana", size=15, bold=True, underline="single")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    row += 1  # Pula uma linha em branco para dar espaçamento

    # Adiciona a tabela de faturamento
    total_general = 0
    for company_name, employees in employees_by_company.items():
        active_employees = [e for e in employees if not e.is_on_vacations]
        total_active = len(active_employees)
        total_general += total_active

        ws.append([
            f"  {company_name.upper()}  ",  # Coluna A
            "",  # Coluna B (vazia)
            f"  {total_active}  "  # Coluna C
        ])

        # Estiliza as células da tabela
        for col_index in range(1, 4):  # Apenas até a coluna C
            cell = ws.cell(row=row, column=col_index)
            cell.font = Font(name="Verdana", size=11)
            cell.border = Border(
                left=Side(style='thick'),
                right=Side(style='thick'),
                top=Side(style='thick'),
                bottom=Side(style='thick')
            )
            cell.alignment = Alignment(horizontal="center", vertical="center")

        row += 1

    # Adiciona total geral
    ws.append(["", "", f"{total_general}"])
    total_cell = ws.cell(row=row, column=3)
    total_cell.font = Font(name="Verdana", size=14, bold=True)
    total_cell.alignment = Alignment(horizontal="center", vertical="center")


    # Adiciona espaço antes da seção de faturamento (entrega)
    row += 2

    # Adiciona título "FATURAMENTO (ENTREGA)"
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    delivery_title = ws.cell(row=row, column=1, value=f"FATURAMENTO (ENTREGA) {first_day} A {last_day}")
    delivery_title.font = Font(name="Verdana", size=15, bold=True, underline="single")
    delivery_title.alignment = Alignment(horizontal="center", vertical="center")
    row += 1  # Pula uma linha em branco para dar espaçamento

    # Adiciona a tabela de faturamento (entrega)
    for unity in Unity.objects.all():
        active_employees = Employee.objects.filter(unity=unity, is_on_vacations=False)
        total_active = len(active_employees)

        # Preenche a linha da unidade
        if unity.unity_name == "Unidade 1":
            unity_name = "UNIDADE 1 - Rua João Jose dos Reis, 59"
        elif unity.unity_name == "Unidade 2":
            unity_name = "UNIDADE 2 - Rua Jose Maria de Melo, 311"
        elif unity.unity_name == "Unidade 5 - Galpão Novo":
            unity_name = "UNIDADE 5 (GALPÃO NOVO) - Rua Jose Maria de Melo, 157"

        # Adiciona a linha de faturamento
        ws.append([
            f"  {unity_name}  ",  # Coluna A
            "ALMOÇO (CUBA)",  # Coluna B
            f"  {total_active}  "  # Coluna C
        ])

        # Estiliza as células da tabela
        for col_index in range(1, 4):  # Apenas até a coluna C
            cell = ws.cell(row=row, column=col_index)
            cell.font = Font(name="Verdana", size=11)
            cell.border = Border(
                left=Side(style='thick'),
                right=Side(style='thick'),
                top=Side(style='thick'),
                bottom=Side(style='thick')
            )
            cell.alignment = Alignment(horizontal="center", vertical="center")

            # Aplica a formatação vermelha e em negrito na coluna C
            cell_c = ws.cell(row=row, column=3)  # Coluna C
            cell_c.font = Font(name="Verdana", size=11, bold=True, color="FF0000")  # Vermelho e Negrito

        row += 1  # Pula uma linha para a próxima unidade

    # Adiciona a soma total geral de funcionários não de férias
    ws.append(["", "", f"  {total_general}  "])
    total_delivery_cell = ws.cell(row=row, column=3)
    total_delivery_cell.font = Font(name="Verdana", size=14, bold=True, color="FF0000")
    total_delivery_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Ajusta largura das colunas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = max_length + 14
        ws.column_dimensions[column].width = adjusted_width

    # Retorna o arquivo como resposta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="RELACAO FUNCIONARIO JEITINHO BRASILEIRO {first_day} A {last_day}.xlsx"'

    wb.save(response)
    return response