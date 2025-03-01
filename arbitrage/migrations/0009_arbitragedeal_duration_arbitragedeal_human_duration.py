# Generated by Django 5.1.2 on 2025-03-01 16:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('arbitrage', '0008_alter_arbitragedeal_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='arbitragedeal',
            name='duration',
            field=models.DurationField(blank=True, null=True, verbose_name='Duration'),
        ),
        migrations.AddField(
            model_name='arbitragedeal',
            name='human_duration',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Human Duration'),
        ),
    ]
