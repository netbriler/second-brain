# Generated by Django 5.1 on 2024-09-24 14:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0003_alter_course_position_alter_group_position_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LearningProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timecode', models.PositiveIntegerField(default=0, verbose_name='Timecode (in seconds)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                (
                    'course',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progresses',
                        to='courses.course',
                        verbose_name='Course',
                    ),
                ),
                (
                    'lesson',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progresses',
                        to='courses.lesson',
                        verbose_name='Lesson',
                    ),
                ),
                (
                    'lesson_entity',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progresses',
                        to='courses.lessonentity',
                        verbose_name='Lesson Entity',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progresses',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='User',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Learning Progress',
                'verbose_name_plural': 'Learning Progresses',
                'unique_together': {('user', 'course', 'lesson', 'lesson_entity')},
            },
        ),
    ]