import uuid
from django.db import migrations, models


def backfill_hashes(apps, schema_editor):
    PdfComment = apps.get_model("epstein_ui", "PdfComment")
    for comment in PdfComment.objects.filter(hash__isnull=True):
        comment.hash = uuid.uuid4()
        comment.save(update_fields=["hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("epstein_ui", "0010_pdf_comment_votes"),
    ]

    operations = [
        migrations.AddField(
            model_name="pdfcomment",
            name="hash",
            field=models.UUIDField(null=True, editable=False, unique=False),
        ),
        migrations.RunPython(backfill_hashes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="pdfcomment",
            name="hash",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
