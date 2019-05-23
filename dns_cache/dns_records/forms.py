from django import forms
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.core.validators import RegexValidator

class DomainForm(forms.Form):
    domain_name_validator = RegexValidator(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', 'This is not of the proper domain name format.')
    domain_name = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid domain name.", validators=[domain_name_validator])

class CaptchaForm(forms.Form):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(attrs={'style':'transform:scale(0.77);-webkit-transform:scale(0.77);transform-origin:0 0;-webkit-transform-origin:0 0;"'}))

class LoginForm(forms.Form):
    username = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid username")
    password = forms.CharField(widget=forms.PasswordInput)