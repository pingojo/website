# Generated by Django 4.2.7 on 2024-08-12 14:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0044_remove_email_from_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="html_resume",
            field=models.TextField(blank=True, null=True),
        ),
    ]
