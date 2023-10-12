from django import forms

class CarURLForm(forms.Form):
    url = forms.URLField(label='Enter an AutoTrader URL:', required=True)
    location = forms.CharField()

