# Generated by Django 4.2.7 on 2023-11-10 01:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0040_profile_is_public"),
    ]

    operations = [
        migrations.AddField(
            model_name="link",
            name="title",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
