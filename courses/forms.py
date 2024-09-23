from django import forms
from django.contrib.admin.helpers import ActionForm

from courses.models import Course, Group


class GroupAndCourseForm(ActionForm):
    group_field = forms.ModelChoiceField(queryset=Group.objects.all(), required=False)

    course_field = forms.ModelChoiceField(queryset=Course.objects.all(), required=False)
