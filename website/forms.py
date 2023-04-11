from allauth.account.forms import SignupForm
from django import forms

from .models import (Application, Company, Email, Job, Role, Search, Skill,
                     Source, Stage)


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        del self.fields['username']
        del self.fields['password2']

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user



class ResumeUploadForm(forms.Form):
    resume = forms.FileField()



class AutocompleteTextInput(forms.TextInput):
    class Media:
        css = {
            'all': ('https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css',)
        }
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://code.jquery.com/ui/1.12.1/jquery-ui.js',
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault('class', '')
        attrs['class'] += ' autocomplete'
        return attrs

class JobForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Role.objects.all(), widget=AutocompleteTextInput(attrs={'id': 'role-autocomplete'}))
    company = forms.ModelChoiceField(queryset=Company.objects.all(), widget=AutocompleteTextInput(attrs={'id': 'company-autocomplete'}))

    class Meta:
        model = Job
        fields = [ 'link', 'company', 'role', 'salary_min', 'salary_max', 'posted_date', 'closing_date',  'equity_min', 'equity_max']


class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['website']
