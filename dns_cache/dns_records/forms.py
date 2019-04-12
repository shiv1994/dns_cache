from django import forms
from django.core.validators import RegexValidator
from captcha.fields import CaptchaField

class DomainForm(forms.Form):
    domain_name_validator = RegexValidator(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', 'This is not of the proper domain name format.')
    domain_name = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid domain name or IP Address", validators=[domain_name_validator])
    captcha = CaptchaField(help_text = "Fill in the textbox with the characters from the image")

class LoginForm(forms.Form):
    username = forms.CharField(required= True, max_length = 50, help_text = "Please enter a valid username")
    password = forms.CharField(widget=forms.PasswordInput)