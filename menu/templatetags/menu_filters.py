from django import template

register = template.Library()

@register.filter
def get_option(user_choices, menu_id):
    """
    Retorna a opção selecionada para um determinado cardápio.
    """
    return user_choices.get(menu_id)
