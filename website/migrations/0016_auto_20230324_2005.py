# Generated by Django 3.2.18 on 2023-03-24 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0015_rename_email_id_email_gmail_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='date_applied',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='date_of_last_email',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
