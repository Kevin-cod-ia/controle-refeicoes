from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from django.http import HttpResponse
from menu.models import Employee, Company, WeekMenu


def generate_full_report_function(request, companies):
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Completo"
    week_menu = WeekMenu.objects.filter()
    first_day = week_menu[0].date_meal.strftime("%d.%m.%Y")
    last_day = week_menu[4].date_meal.strftime("%d.%m.%Y")

    # Adiciona cabeçalho
    headers = ['Unidade', 'Turno', 'Nome da Empresa', 'Nome do Funcionário']
    ws.append(headers)

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

    # Definir as unidades e suas respectivas empresas
    UNIT_MAPPING = {
        'Unidade 01': ['FG&P', 'FCD'],
        'Unidade 02': ['Sustenpack - Unidade 2'],
        'Unidade 05 - Novo Galpão': ['Sustenpack'],
    }

    row = 2  # Começa a adicionar os dados a partir da segunda linha

    # Loop pelas unidades
    for unit, companies in UNIT_MAPPING.items():
        for company_name in companies:
            company = Company.objects.get(company_name=company_name)
            
            # Obter todos os funcionários da empresa
            employees = Employee.objects.filter(company=company).order_by('first_name', 'last_name')
            total_employees = len(employees)
            
            # Adiciona os funcionários
            for employee in employees:
                # Determina a cor de fundo com base no status de férias
                fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid") if employee.is_on_vacations else None
                
                # Adiciona dados do funcionário com a formatação de maiúsculas e fonte Verdana
                ws.append([unit,
                           employee.shift.shift,  # Adaptação para pegar o nome do turno
                           company_name.upper(),  # Nome da empresa em maiúsculas
                           employee.__str__().upper()])  # Nome do funcionário em maiúsculas

                # Aplica a cor de fundo se o funcionário estiver de férias
                if fill:
                    for cell in ws[row]:
                        cell.fill = fill

                # Aplica borda e formatação Verdana
                for cell in ws[row]:
                    cell.font = Font(name="Verdana", size=10)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )

                row += 1

            # Linha de total de funcionários
            ws.append([
                '',
                '',
                company_name.upper(),  # Nome da empresa na 3ª coluna
                'TOTAL: {} FUNCIONÁRIOS'.format(total_employees)  # "TOTAL" na 4ª coluna
            ])

            # Aplica formatação especial na linha de total
            total_row = row  # Posição da linha total
            for cell in ws[total_row]:
                cell.font = Font(name="Verdana", size=10, bold=True)
                cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

            row += 1  # Avança para a próxima linha

    # Ajusta o tamanho das colunas para que o conteúdo caiba bem e o texto não fique cortado
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Obtém o nome da coluna
        for cell in col:
            try:
                if cell.value:  # Verifica se o valor da célula não é None
                    max_length = max(max_length, len(str(cell.value)))  # Calcula o maior comprimento de valor
            except:
                pass
        adjusted_width = max_length + 4  # Ajuste extra para garantir que o texto não fique cortado
        ws.column_dimensions[column].width = adjusted_width

    # Cria a resposta para download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="RELACAO FUNCIONARIO JEITINHO BRASILEIRO {first_day} A {last_day}.xlsx"'

    wb.save(response)
    return response