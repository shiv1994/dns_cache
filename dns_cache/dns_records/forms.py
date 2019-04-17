from django import forms
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.core.validators import RegexValidator

class DomainForm(forms.Form):
    domain_name_validator = RegexValidator(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', 'This is not of the proper domain name format.')
    domain_name = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid domain name or IP Address", validators=[domain_name_validator])
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

class LoginForm(forms.Form):
    username = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid username")
    password = forms.CharField(widget=forms.PasswordInput)