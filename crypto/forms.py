from django import forms
from django.contrib.admin.helpers import ActionForm

from crypto.models import ExchangeCredentials
from users.models import User


class UserForm(ActionForm):
    user_field = forms.ModelChoiceField(queryset=User.objects.all(), required=False)


class ExchangeCredentialsAdminForm(forms.ModelForm):
    # Use a PasswordInput so it's never shown in plain text
    api_secret = forms.CharField(
        label='API Secret',
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    class Meta:
        model = ExchangeCredentials
        fields = '__all__'

    def save(self, commit=True):
        """
        Only update the model's api_secret if user entered a new one.
        If left blank, do not overwrite the old value.
        """
        secret = self.cleaned_data.get('api_secret')
        if secret:  # If user provided a new secret
            self.instance.api_secret = secret
        return super().save(commit=commit)
