from django import forms
from models import FormConfiguration
from django.forms import ModelForm

class MyForm( forms.Form ):
    pass

class InitialConfigurationForm( ModelForm ):
    class Meta:
        model=FormConfiguration