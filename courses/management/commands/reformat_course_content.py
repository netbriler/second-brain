from django.core.management.base import BaseCommand
from django.utils.html import strip_tags

from courses.models import Course, Link


class Command(BaseCommand):
    help = 'Reformat course content'

    def add_arguments(self, parser):
        parser.add_argument('course_id', type=int)

    def handle(self, course_id: int, *args, **options):
        course = Course.objects.get(id=course_id)

        for lesson in course.lessons.all():
            for lesson_entity in lesson.lesson_entities.all():
                content = strip_tags(lesson_entity.content.strip()).split('\n')

                for i in range(len(content)):
                    content[i] = content[i].strip()

                    if content[i] and content[i] == content[i].upper():
                        content[i] = f'<b>{content[i]}</b>'

                    if content[i].startswith('https://teletype.in/'):
                        Link.objects.get_or_create(
                            title='ОТКРЫТЬ КОНСПЕКТ',
                            url=content[i],
                            lesson_entity=lesson_entity,
                            defaults={
                                'position': i,
                            },
                        )

                        del content[i]

                lesson_entity.content = '\n'.join(content).strip()
                lesson_entity.save()
