# Generated by Django 4.2.7 on 2023-11-09 05:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0039_profile_bio"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
    ]
