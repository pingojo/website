# Generated by Django 3.2.18 on 2023-03-24 19:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0014_auto_20230324_1925'),
    ]

    operations = [
        migrations.RenameField(
            model_name='email',
            old_name='email_id',
            new_name='gmail_id',
        ),
    ]
