from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from menu.models import Employee, Company, WeekMenu, Unity, UserChoice
import locale


def generate_unity_options_pdf(request, file_path, unit_name, unit_address, unit_filter):
    # Configuração inicial
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    # Configuração inicial com margens ajustadas
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=10,  # Margem esquerda menor
        rightMargin=10,  # Margem direita menor
    )
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name="HeaderStyle",
        fontName="Helvetica-Bold",
        fontSize=12,  # Reduzido em 2 pontos
        leading=12,
        alignment=1,  # Centralizado
        textColor=colors.black,
        spaceAfter=3,  # Reduzido para ajustar espaçamento
        wordWrap=True,  # Permitir quebra de texto
    )

    cell_style = ParagraphStyle(
        name="CellStyle",
        fontName="Helvetica",
        fontSize=10,  # Reduzido em 2 pontos
        leading=10,
        alignment=1,  # Centralizado
        textColor=colors.black,
        wordWrap=True,  # Permitir quebra de texto
    )

    red_bold_style = ParagraphStyle(
        name="RedBoldStyle",
        fontName="Helvetica-Bold",
        fontSize=11,  # Reduzido em 2 pontos
        leading=10,
        alignment=1,  # Centralizado
        textColor=colors.red,  # Vermelho
        wordWrap=True,  # Permitir quebra de texto
    )

    # Título principal
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName="Helvetica-Bold",
        fontSize=15,  # Reduzido em 2 pontos
        leading=14,
        alignment=1,  # Centralizado
        textColor=colors.black,
        spaceAfter=8,  # Reduzido para ajustar espaçamento
    )

    title = f"{unit_name.upper()} - {unit_address.upper()}"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))  # Espaçamento reduzido

    # Cabeçalhos da tabela com quebra de texto
    headers = [
        Paragraph("Prato Principal", header_style),
        Paragraph("Total de Opções", header_style),
        Paragraph("Omelete", header_style),
        Paragraph("Marmita Fit Frango", header_style),
        Paragraph("Marmita Fit Carne", header_style),
        Paragraph("Marmita Fit Vegana", header_style),
    ]

    data = [headers]  # Adiciona os cabeçalhos na tabela

    # Simula os dados para a tabela
    week_menu = WeekMenu.objects.filter()  # Substituir com dados reais
    for menu in week_menu:
        total_options = UserChoice.objects.filter(
            menu=menu,
            user__employee__unity__unity_name=unit_filter,
            user__employee__is_on_vacations=False,
            user__employee__is_home_office=False,
        ).count()

        omelet_count = UserChoice.objects.filter(
            menu=menu,
            option__name_option="Omelete",
            user__employee__unity__unity_name=unit_filter,
            user__employee__is_on_vacations=False,
            user__employee__is_home_office=False,
        ).count()

        chicken_count = UserChoice.objects.filter(
            menu=menu,
            option__name_option="Marmita de Frango",
            user__employee__unity__unity_name=unit_filter,
            user__employee__is_on_vacations=False,
            user__employee__is_home_office=False,
        ).count()

        beef_count = UserChoice.objects.filter(
            menu=menu,
            option__name_option="Marmita de Carne",
            user__employee__unity__unity_name=unit_filter,
            user__employee__is_on_vacations=False,
            user__employee__is_home_office=False,
        ).count()

        

        # Linha com dados formatados

        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        week_day = menu.date_meal.strftime("%A")

        row = [
            Paragraph(f"{menu.date_meal.strftime('%d.%m')} ({week_day.upper()}) - {menu.title.upper()}", cell_style),
            Paragraph(str(total_options), red_bold_style),  # Aplica o estilo vermelho e negrito
            Paragraph(str(omelet_count), cell_style),
            Paragraph(str(chicken_count), cell_style),
            Paragraph(str(beef_count), cell_style),
            "",
        ]
        data.append(row)

    # Criação da tabela
    col_widths = [130, 60, 60, 80, 80, 80]  # Larguras ajustadas
    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),  # Fundo cinza para os headers
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),  # Cor do texto dos headers
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # Alinha todo o texto ao centro
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Alinha verticalmente no centro
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),  # Fonte dos headers
                ("FONTSIZE", (0, 0), (-1, -1), 8),  # Tamanho da fonte reduzido
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),  # Espaçamento reduzido na parte inferior dos headers
                ("GRID", (0, 0), (-1, -1), 1, colors.black),  # Grade da tabela
            ]
        )
    )

    elements.append(table)

    # Adiciona tabelas de faturamento
    elements.append(Spacer(1, 15))

    for menu in week_menu:
        # Título de faturamento
        title = f"FATURAMENTO {menu.date_meal.strftime('%d.%m')} ({menu.date_meal.strftime('%A').upper()})"
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 10))

        # Dados de faturamento
        options_meal_list = ['ALMOÇO', 'OMELETE', 'MARMITAS FIT']
        total_unit_employees_day = 0

        data = []
        for option in options_meal_list:
            if option == 'ALMOÇO':
                no_order_count = Employee.objects.filter(
                    unity__unity_name=unit_name, is_on_vacations=False, is_home_office=False
                ).exclude(
                    user__userchoice__menu=menu,
                    user__userchoice__option__name_option__in=["Omelete", "Marmita de Frango", "Marmita de Carne"]
                ).count()
                total_value = no_order_count
            elif option == 'OMELETE':
                omelet_count = UserChoice.objects.filter(
                    menu=menu,
                    option__name_option="Omelete",
                    user__employee__unity__unity_name=unit_name,
                    user__employee__is_on_vacations=False,
                    user__employee__is_home_office=False,
                ).count()
                total_value = omelet_count
            elif option == 'MARMITAS FIT':
                marmita_count = UserChoice.objects.filter(
                    menu=menu,
                    option__name_option__in=["Marmita de Frango", "Marmita de Carne"],
                    user__employee__unity__unity_name=unit_name,
                    user__employee__is_on_vacations=False,
                    user__employee__is_home_office=False,
                ).count()
                total_value = marmita_count
                

            total_unit_employees_day += total_value

            row = [
                Paragraph(option, cell_style),
                Paragraph(str(total_value), red_bold_style),
            ]
            data.append(row)

        # Cria tabela de faturamento
        col_widths = [150, 50]  # Largura das colunas
        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 10))

        # Total geral
        total_paragraph = Paragraph(f"Total: {total_unit_employees_day}", red_bold_style)
        elements.append(total_paragraph)
        elements.append(Spacer(1, 20))

      # Total geral
    total_paragraph = Paragraph(f"Total: {total_unit_employees_day}", red_bold_style)
    elements.append(total_paragraph)
    elements.append(Spacer(1, 20))

    # Gera o PDF
    doc.build(elements)

    return file_path