from django.contrib import admin
from .models import Options, WeekMenu, Shift, Company, Profile, Employee


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

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    # Exclui o campo 'user' do formulário
    exclude = ('user',)


