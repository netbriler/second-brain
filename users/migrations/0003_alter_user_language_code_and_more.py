# Generated by Django 5.0.1 on 2024-01-14 14:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_alter_user_first_name_alter_user_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='language_code',
            field=models.CharField(
                blank=True,
                choices=[('en', '🇺🇸 English'), ('ru', '🇷🇺 Русский'), ('ua', '🇺🇦 Українська')],
                default='en',
                max_length=10,
                verbose_name='Language Code',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='telegram_activity_at',
            field=models.DateTimeField(editable=False, null=True, verbose_name='Telegram Last Activity At'),
        ),
    ]
