# Generated by Django 5.1 on 2024-09-25 19:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0006_alter_course_options_alter_group_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='learningprogress',
            options={
                'ordering': ('-updated_at',),
                'verbose_name': 'Learning Progress',
                'verbose_name_plural': 'Learning Progresses',
            },
        ),
        migrations.AlterUniqueTogether(
            name='learningprogress',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='learningprogress',
            name='course',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='progresses',
                to='courses.course',
                verbose_name='Course',
            ),
        ),
    ]