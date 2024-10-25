from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0032_company_phone_job_remote"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="search_vector",
            field=models.TextField(null=True),  # Replacing SearchVectorField with TextField
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["search_vector"], name="website_job_search_vector_idx"
            ),  # Creating a regular index with key length
        ),
        migrations.RunSQL(
            "CREATE INDEX website_job_search_vector_idx ON website_job (search_vector(255));"
        ),  # Specifying key length for TEXT field index
    ]
