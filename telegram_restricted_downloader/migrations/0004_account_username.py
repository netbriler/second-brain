# Generated by Django 5.1 on 2024-10-31 12:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('telegram_restricted_downloader', '0003_account_telegram_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='username',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
