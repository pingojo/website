from django.contrib import admin
from .models import Company

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'twitter_url', 'greenhouse_url', 'lever_url', 'number_of_employees_min', 'number_of_employees_max', 'description', 'website', 'city', 'state', 'country', 'ceo', 'ceo_twitter')
    search_fields = ('name', 'city', 'state', 'country', 'ceo')
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Company, CompanyAdmin)
