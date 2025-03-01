from django import forms
from django.contrib.admin.helpers import ActionForm

from users.models import User


class UserForm(ActionForm):
    user_field = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
