# Generated by Django 4.2.7 on 2024-08-12 21:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0047_requestlog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requestlog",
            name="referer",
            field=models.URLField(blank=True, null=True),
        ),
    ]
