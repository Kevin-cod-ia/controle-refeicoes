from django.db import models
from django.contrib.auth.models import User
import locale
from django.utils.text import slugify

class Options(models.Model):
    name_option = models.CharField(max_length=65)

    class Meta:
        verbose_name = "Opção"
        verbose_name_plural = "Opções"

    def __str__(self):
        return self.name_option



class WeekMenu(models.Model):

    title = models.CharField(max_length=65, verbose_name="Prato Principal")
    side_dish = models.CharField(max_length=165, verbose_name="Guarnição")
    date_meal = models.DateField(verbose_name='Data da refeição')
    image_meal = models.ImageField(upload_to='menu/week_menu/%Y/%m/%d/', blank=True, default='', verbose_name='Foto do prato')
    created_at = models.DateTimeField(auto_now_add=True)

    options = models.ManyToManyField(Options, related_name='weekmenu_options', verbose_name='Opções')

    class Meta:
        verbose_name = "Cardápio semanal"
        verbose_name_plural = "Cardápio semanal"

    def __str__(self):
        # Configurar localidade compatível com Windows
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        return f'{self.date_meal.strftime("%A")}'
    



class Shift(models.Model):
    shift = models.CharField(max_length=65, verbose_name='Turno')

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return self.shift
    

class Company(models.Model):
    company_name = models.CharField(max_length=65, verbose_name='Empresa')

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.company_name


class Unity(models.Model):
    unity_name = models.CharField(max_length=65, verbose_name='Unidade')

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.unity_name
    


class Profile(models.Model):
    profile = models.CharField(max_length=65, verbose_name='Perfil')

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    
    def __str__(self):
        return self.profile
    


class Employee(models.Model):
    first_name = models.CharField(max_length=65, verbose_name='Nome')
    last_name = models.CharField(max_length=65, verbose_name='Sobrenome')
    birth_date = models.DateField(verbose_name='Data de nasc.')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='employee_shift', verbose_name='Turno')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employee_company', verbose_name='Empresa')
    unity = models.ForeignKey(Unity, on_delete=models.CASCADE, related_name='employee_unity', verbose_name='Unidade', null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='employee_profile', verbose_name='Perfil')
    is_on_vacations = models.BooleanField(default=False, verbose_name='Férias')
    first_day_vacations = models.DateField(verbose_name='Ínicio Férias', null=True, blank=True)
    last_day_vacations = models.DateField(verbose_name='Final Férias', null=True, blank=True)
    is_home_office = models.BooleanField(default=False, verbose_name='Home Office')
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuário', null=True, blank=True)

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"


    def save(self, *args, **kwargs):
        # Cria o login como nome.primeiro_sobrenome
        username = slugify(f"{self.first_name.lower()}.{self.last_name.split()[0].lower()}")
        
        # Gera a senha com base na data de nascimento
        password = self.birth_date.strftime("%d%m%Y")
        
        if not self.user:
            # Cria um objeto User do Django com o username e a senha gerados
            user = User.objects.create_user(username=username, password=password)
            self.user = user
        
        super().save(*args, **kwargs)  # Salva o Employee normalmente
    
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'




class MealChoice(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='meal_choices')
    meal_date = models.DateField()
    meal_option = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('employee', 'meal_date')  # Garante uma escolha única por dia para cada funcionário.

    def __str__(self):
        return f"{self.employee.first_name} - {self.meal_date} - {self.meal_option}"
    


class UserChoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(WeekMenu, on_delete=models.CASCADE)
    option = models.ForeignKey(Options, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    class Meta:
        unique_together = ('user', 'menu')

    def __str__(self):
        return f"{self.user} - {self.menu}"



class MenuOption(models.Model):
    menu = models.ForeignKey(WeekMenu, on_delete=models.CASCADE)
    option = models.ForeignKey(Options, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # Armazena a posição/ordem da opção

    class Meta:
        ordering = ['order']