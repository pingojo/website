# Generated by Django 3.2.18 on 2023-03-19 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_auto_20230319_0441'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='careers_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='careers_url_status',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='careers_url_status_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='website_status',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='website_status_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
