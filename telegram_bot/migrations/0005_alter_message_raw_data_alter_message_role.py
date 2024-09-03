# Generated by Django 5.1 on 2024-09-03 03:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('telegram_bot', '0004_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='raw_data',
            field=models.JSONField(default=dict, verbose_name='Raw Data'),
        ),
        migrations.AlterField(
            model_name='message',
            name='role',
            field=models.CharField(
                blank=True,
                choices=[
                    ('simple', 'Simple'),
                    ('voice_recognition', 'Voice Recognition'),
                    ('text_recognition', 'Text Recognition'),
                ],
                max_length=200,
                null=True,
                verbose_name='Role',
            ),
        ),
    ]
