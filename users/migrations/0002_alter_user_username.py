# Generated by Django 5.1 on 2024-08-30 06:32

from django.db import migrations, models

import users.validators


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(
                max_length=36,
                null=True,
                unique=True,
                validators=[users.validators.UnicodeUsernameValidator()],
                verbose_name='Username',
            ),
        ),
    ]