# Generated by Django 5.1.4 on 2025-01-13 12:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0010_alter_employee_profile_mealchoice_userchoice'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserChoice',
        ),
    ]
