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
            ),  # Replace GinIndex with Index
        ),
        migrations.RunSQL(
            "ALTER TABLE website_job ADD FULLTEXT(search_vector);"
        ),  # Adding FULLTEXT index for MySQL
    ]
