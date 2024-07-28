# Generated by Django 4.2.2 on 2023-07-15 21:52

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0032_company_phone_job_remote"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="search_vector",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name="job",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_vector"], name="website_job_search__0dd667_gin"
            ),
        ),
    ]
