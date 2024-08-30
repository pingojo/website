# Generated by Django 4.2.7 on 2024-08-26 23:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0051_alter_bouncedemail_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="skills",
            field=models.ManyToManyField(
                blank=True, related_name="jobs", to="website.skill"
            ),
        ),
    ]