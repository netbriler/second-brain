# Generated by Django 5.1 on 2024-09-25 15:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reminders', '0004_alter_reminder_periodic_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='is_enabled',
            field=models.BooleanField(default=True, verbose_name='Is Enabled'),
        ),
    ]