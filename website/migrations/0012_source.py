# Generated by Django 3.2.18 on 2023-03-22 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0011_auto_20230321_2353'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('website', models.URLField()),
                ('url_structure', models.TextField()),
                ('job_count', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
