# Generated by Django 4.2.2 on 2023-07-04 15:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0028_source_created_source_modified"),
    ]

    operations = [
        migrations.AddField(
            model_name="source",
            name="search_url",
            field=models.URLField(blank=True, default="", null=True),
        ),
    ]
