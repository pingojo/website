from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render

def merge_companies_action(modeladmin, request, queryset):
    if queryset.count() != 2:
        modeladmin.message_user(request, "You must select exactly 2 companies to merge.", level='error')
        return

    company1, company2 = queryset.all()

    if request.method == 'POST':
        target_company = company1 if str(company1.pk) == request.POST.get('target_company') else company2
        other_company = company1 if target_company == company2 else company2

        # Update related objects
        other_company.job_set.update(company=target_company)
        other_company.application_set.update(company=target_company)

        # Delete the other company
        other_company.delete()

        modeladmin.message_user(request, f"Successfully merged companies: {target_company.name} and {other_company.name}")
        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'merge_companies.html', {
        'company1': company1,
        'company2': company2,
    })

merge_companies_action.short_description = "Merge selected companies"
