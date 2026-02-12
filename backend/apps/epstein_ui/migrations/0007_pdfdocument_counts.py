from django.db import migrations, models


def backfill_counts(apps, schema_editor):
    PdfDocument = apps.get_model("epstein_ui", "PdfDocument")
    Annotation = apps.get_model("epstein_ui", "Annotation")
    PdfVote = apps.get_model("epstein_ui", "PdfVote")

    for doc in PdfDocument.objects.all():
        ann_total = Annotation.objects.filter(pdf_key=doc.filename).count()
        vote_score = PdfVote.objects.filter(pdf_id=doc.id).aggregate(total=models.Sum("value")).get("total") or 0
        PdfDocument.objects.filter(id=doc.id).update(annotation_count=ann_total, vote_score=vote_score)


class Migration(migrations.Migration):
    dependencies = [
        ("epstein_ui", "0006_pdfvote"),
    ]

    operations = [
        migrations.AddField(
            model_name="pdfdocument",
            name="annotation_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="pdfdocument",
            name="vote_score",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(backfill_counts, migrations.RunPython.noop),
    ]
