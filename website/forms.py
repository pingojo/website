from allauth.account.forms import SignupForm
from django import forms

from .models import (Application, Company, Email, Job, Role, Search, Skill,
                     Source, Stage)


from django.utils.text import slugify

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
    role = forms.CharField(widget=AutocompleteTextInput(attrs={'id': 'role-autocomplete'}))
    company = forms.CharField(widget=AutocompleteTextInput(attrs={'id': 'company-autocomplete'}))
    city = forms.CharField()
    state = forms.CharField()
    country = forms.CharField()

    class Meta:
        model = Job
        fields = [
            'link', 
            'company', 
            'role', 
            'salary_min', 
            'job_type',
            'salary_max', 
            'posted_date', 
            'closing_date',
            'city',
            'remote',
            'state',
            'country',
            'equity_min', 
            'equity_max', 
            'description_markdown'
        ]

    def clean_company(self):
        name = self.cleaned_data.get('company')
        company, created = Company.objects.get_or_create(name=name)
        return company

    def clean_role(self):
        title = self.cleaned_data.get('role')

        role_slug = slugify(title[:50])
        role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": title}
        )
        
        #role, created = Role.objects.get_or_create(title=title)
        return role

    def clean(self):
        name = self.cleaned_data.get('company')
        company, created = Company.objects.update_or_create(
            name=name,
            defaults={
                'city': self.cleaned_data.get('city'),
                'state': self.cleaned_data.get('state'),
                'country': self.cleaned_data.get('country')
            }
        )
        

class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['website']
