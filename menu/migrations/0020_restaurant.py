# Generated by Django 5.1.4 on 2025-01-29 19:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0019_previoususerchoice'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_restaurant', models.CharField(max_length=85, verbose_name='Restaurante')),
                ('profile', models.ForeignKey(default='Restaurante', on_delete=django.db.models.deletion.CASCADE, related_name='restaurant_profile', to='menu.profile', verbose_name='Perfil')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Restaurante',
                'verbose_name_plural': 'Restaurantes',
            },
        ),
    ]
