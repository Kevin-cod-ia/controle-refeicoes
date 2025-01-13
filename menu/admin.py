from django.contrib import admin
from .models import Options, WeekMenu, Shift, Company, Profile, Employee, UserChoice


class OptionsAdmin(admin.ModelAdmin):
    ...


@admin.register(WeekMenu)
class WeekMenuAdmin(admin.ModelAdmin):
    ...


admin.site.register(Options,OptionsAdmin)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    ...

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    ...

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    ...


def excluir_userchoices_orfaos(modeladmin, request, queryset):
    # Excluir UserChoice que não têm um User, WeekMenu ou Option válidos
    queryset.filter(user__isnull=True).delete()  # Deleta se não tiver user
    queryset.filter(menu__isnull=True).delete()  # Deleta se não tiver menu
    queryset.filter(option__isnull=True).delete()  # Deleta se não tiver option

excluir_userchoices_orfaos.short_description = 'Excluir UserChoices órfãos'

@admin.register(UserChoice)
class UserChoiceAdmin(admin.ModelAdmin):
    actions = [excluir_userchoices_orfaos]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    # Exclui o campo 'user' do formulário
    exclude = ('user',)


