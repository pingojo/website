from allauth.account.forms import SignupForm
from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    Application,
    Company,
    Email,
    Job,
    Link,
    Profile,
    Prompt,
    Role,
    Search,
    Skill,
    Source,
    Stage,
)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_picture", "bio", "is_public", "html_resume"]

    is_public = forms.BooleanField(
        label="Make Profile Public",
        required=False,
        help_text="Select to make your profile visible to others.",
    )


class EditAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]


class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ["content"]


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["url"]


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": "First Name"}),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
    )
    email2 = forms.EmailField(
        max_length=254,
        label="Email",
        widget=forms.TextInput(attrs={"placeholder": "Email"}),
    )
    email = forms.EmailField(max_length=254, widget=forms.HiddenInput(), required=False)
    captcha = CaptchaField()

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Remove username and password confirmation fields
        self.fields.pop("username", None)
        self.fields.pop("password2", None)
        # Make sure email is hidden and not required
        self.fields["email"].required = False
        self.fields["captcha"].widget.attrs["placeholder"] = (
            "Enter the four characters captcha ->"
        )

    def clean_email2(self):
        email = self.cleaned_data.get("email2")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def save(self, request):
        # Check if the hidden email field is filled out by bots
        bot_email = self.cleaned_data.get("email")
        if bot_email:
            # Act as if the data is processed correctly
            return super(SignupForm, self).save(request)

        # Use email2 as the email for the user
        email = self.cleaned_data.get("email2")
        user = super(CustomSignupForm, self).save(request)

        # If the super call failed for some reason, return None
        if not user:
            return None

        # Set the additional fields on the user object
        user.email = email
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        return user

    def signup(self, request, user):
        # If you need to do anything when the user signs up, add it here
        pass


class ResumeUploadForm(forms.Form):
    resume = forms.FileField()


class AutocompleteTextInput(forms.TextInput):
    class Media:
        css = {"all": ("https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css",)}
        js = (
            "https://code.jquery.com/jquery-3.6.0.min.js",
            "https://code.jquery.com/ui/1.12.1/jquery-ui.js",
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("class", "")
        attrs["class"] += " autocomplete"
        return attrs


class JobForm(forms.ModelForm):
    role = forms.CharField(
        widget=AutocompleteTextInput(attrs={"id": "role-autocomplete"})
    )
    company = forms.CharField(
        widget=AutocompleteTextInput(attrs={"id": "company-autocomplete"})
    )
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    country = forms.CharField(required=False)
    link = forms.URLField(required=False)
    salary_min = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    salary_max = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    equity_min = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    equity_max = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    job_type = forms.ChoiceField(
        choices=[
            ("Full-Time", "Full-Time"),
            ("Part-Time", "Part-Time"),
            ("Internship", "Internship"),
            ("Contractor", "Contractor"),
        ]
    )
    remote = forms.ChoiceField(choices=[("True", "True"), ("False", "False")])
    description_markdown = forms.CharField(widget=forms.Textarea, required=False)
    website = forms.URLField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Job
        fields = [
            "link",
            "company",
            "role",
            "salary_min",
            "salary_max",
            "job_type",
            "posted_date",
            "closing_date",
            "city",
            "state",
            "country",
            "remote",
            "equity_min",
            "equity_max",
            "description_markdown",
        ]

    def clean_company(self):
        """Cleans and retrieves or creates the company."""
        name = self.cleaned_data.get("company")

        if name:
            company, created = Company.objects.get_or_create(
                name=name,
            )
            return company
        else:
            raise forms.ValidationError("Company name is required.")

    def clean_role(self):
        """Cleans and retrieves or creates the role."""
        title = self.cleaned_data.get("role")
        if title:
            role_slug = slugify(title[:50])  # Create a slug from the title
            role, _ = Role.objects.get_or_create(
                slug=role_slug, defaults={"title": title}
            )
            return role
        else:
            raise forms.ValidationError("Role is required.")

    def clean(self):
        """Performs additional cleaning for the form."""
        cleaned_data = super().clean()

        # Retrieve the company and location data
        company_name = cleaned_data.get("company")
        city = cleaned_data.get("city")
        state = cleaned_data.get("state")
        country = cleaned_data.get("country")
        email = cleaned_data.get("email")
        website = cleaned_data.get("website")

        # If company information is present, update its location
        if company_name and city and state and country:
            company = cleaned_data.get(
                "company"
            )  # This is the Company object from clean_company()
            if company:
                company.city = city
                company.state = state
                company.country = country
                company.email = email
                company.website = website
                company.save()  # Save any updates to the company location

        # Additional validation can be placed here if needed
        return cleaned_data


class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["website"]
