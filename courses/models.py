from django.db import models


class Course(models.Model):
    name = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    groups = models.ManyToManyField(
        'courses.Group',
        related_name='courses',
    )

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    parent = models.ForeignKey(
        'self',
        related_name='children',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


class Lesson(models.Model):
    title = models.CharField(
        max_length=200,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    groups = models.ManyToManyField(
        'courses.Group',
        related_name='lessons',
    )

    def __str__(self):
        return self.title
