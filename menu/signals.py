from django.db.models.signals import pre_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .models import WeekMenu


@receiver(pre_save, sender=WeekMenu)
def resize_image(sender, instance, **kwargs):
    if instance.image_meal:
        img = Image.open(instance.image_meal)

        # Redimensionar para 400x250
        img = img.resize((400, 250), Image.ANTIALIAS)

        # Salvar a imagem no formato de arquivo
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_file = ContentFile(img_io.getvalue(), instance.image_meal.name)

        # Substituir a imagem do modelo pela imagem redimensionada
        instance.image_meal = img_file
