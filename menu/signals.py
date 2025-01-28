from django.db.models.signals import pre_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .models import WeekMenu


@receiver(pre_save, sender=WeekMenu)
def resize_image(sender, instance, **kwargs):
    # Remova o código de redimensionamento aqui
    # O redimensionamento agora será tratado no método `save()` do modelo
    pass