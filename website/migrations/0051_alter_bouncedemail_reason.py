# Generated by Django 4.2.7 on 2024-08-16 00:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0050_skill_created_skill_modified"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bouncedemail",
            name="reason",
            field=models.TextField(blank=True, null=True),
        ),
    ]
