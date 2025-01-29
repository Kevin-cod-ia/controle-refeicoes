from django.db import models
from django.contrib.auth.models import User
import locale
from django.utils.text import slugify
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import os
import datetime

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
    

    def save(self, *args, **kwargs):
        if self.image_meal and isinstance(self.image_meal, InMemoryUploadedFile):
            # Somente redimensiona se a imagem for um upload válido
            self.image_meal = self.resize_image(self.image_meal)
        super().save(*args, **kwargs)

    def resize_image(self, image):
        img = Image.open(image)
        img = img.resize((400, 250), Image.Resampling.LANCZOS)
        
        # Salvar a imagem redimensionada em memória
        img_io = BytesIO()
        
        # Garantir que a imagem seja salva em um formato correto
        img_format = image.name.split('.')[-1].upper()
        if img_format not in ['JPEG', 'PNG']:
            img_format = 'JPEG'  # Caso não tenha o formato adequado, forçar para JPEG

        img.save(img_io, format=img_format)  # Usar o formato correto
        img_io.seek(0)

        # Extrair o caminho correto com base na data
        date_path = self.date_meal.strftime('%Y/%m/%d')
        file_name = os.path.basename(image.name)
        path = os.path.join('menu/week_menu', date_path, file_name)
        
        # Retorna a imagem redimensionada com o nome correto
        return InMemoryUploadedFile(img_io, None, path, f'image/{img_format.lower()}', sys.getsizeof(img_io), None)


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




class UserChoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(WeekMenu, on_delete=models.CASCADE)
    option = models.ForeignKey(Options, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    class Meta:
        unique_together = ('user', 'menu')

    def __str__(self):
        return f"{self.user} - {self.menu}"




class PreviousWeekMenu(models.Model):
    title = models.CharField(max_length=65, verbose_name="Prato Principal")
    side_dish = models.CharField(max_length=165, verbose_name="Guarnição")
    date_meal = models.DateField(verbose_name='Data da refeição')
    image_meal = models.ImageField(upload_to='menu/previous_week_menu/%Y/%m/%d/', blank=True, default='', verbose_name='Foto do prato')
    created_at = models.DateTimeField(auto_now_add=True)

    options = models.ManyToManyField('Options', related_name='previous_week_menu_options', verbose_name='Opções')

    class Meta:
        verbose_name = "Cardápio anterior"
        verbose_name_plural = "Cardápios anteriores"

    def __str__(self):
        import locale
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        return f'{self.date_meal.strftime("%A")}'
    


    def save(self, *args, **kwargs):
        if self.image_meal and isinstance(self.image_meal, InMemoryUploadedFile):
            # Somente redimensiona se a imagem for um upload válido
            self.image_meal = self.resize_image(self.image_meal)
        super().save(*args, **kwargs)

    def resize_image(self, image):
        img = Image.open(image)
        img = img.resize((400, 250), Image.Resampling.LANCZOS)
        
        # Salvar a imagem redimensionada em memória
        img_io = BytesIO()
        
        # Garantir que a imagem seja salva em um formato correto
        img_format = image.name.split('.')[-1].upper()
        if img_format not in ['JPEG', 'PNG']:
            img_format = 'JPEG'  # Caso não tenha o formato adequado, forçar para JPEG

        img.save(img_io, format=img_format)  # Usar o formato correto
        img_io.seek(0)

        # Extrair o caminho correto com base na data
        date_path = self.date_meal.strftime('%Y/%m/%d')
        file_name = os.path.basename(image.name)
        path = os.path.join('menu/week_menu', date_path, file_name)
        
        # Retorna a imagem redimensionada com o nome correto
        return InMemoryUploadedFile(img_io, None, path, f'image/{img_format.lower()}', sys.getsizeof(img_io), None)


class PreviousUserChoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(PreviousWeekMenu, on_delete=models.CASCADE)
    option = models.ForeignKey(Options, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    class Meta:
        unique_together = ('user', 'menu')

    def __str__(self):
        return f"{self.user} - {self.menu}"



class Restaurant(models.Model):
    name_restaurant = models.CharField(max_length=85, verbose_name='Restaurante')
    short_name = models.CharField(max_length=85, verbose_name='Nome Curto')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='restaurant_profile', verbose_name='Perfil', default='Restaurante')
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuário', null=True, blank=True)

    class Meta:
        verbose_name = "Restaurante"
        verbose_name_plural = "Restaurantes"

    def save(self, *args, **kwargs):
        # Cria o login como nome.primeiro_sobrenome
        username = self.short_name.lower()
        current_year = datetime.datetime.today().year
        
        # Gera a senha com base na data de nascimento
        password = f'{self.short_name.lower()}@{current_year}'
        
        if not self.user:
            # Cria um objeto User do Django com o username e a senha gerados
            user = User.objects.create_user(username=username, password=password)
            self.user = user
        
        super().save(*args, **kwargs)  # Salva o Employee normalmente
    
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'


    def __str__(self):
        return f"{self.name_restaurant} - {self.user}"



