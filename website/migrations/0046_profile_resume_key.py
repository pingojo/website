# Generated by Django 4.2.7 on 2024-08-12 15:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0045_profile_html_resume"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="resume_key",
            field=models.URLField(blank=True, null=True),
        ),
    ]