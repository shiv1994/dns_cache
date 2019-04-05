from django import forms

class DomainForm(forms.Form):
    domain_name = forms.CharField(required= True, 
                                max_length = 50, 
                                help_text = "Please enter a valid domain name or IP Address"
    )