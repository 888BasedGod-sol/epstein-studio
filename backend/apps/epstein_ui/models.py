from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Annotation(models.Model):
    pdf_key = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=64)
    x = models.FloatField()
    y = models.FloatField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("pdf_key", "user", "client_id")


class TextItem(models.Model):
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE, related_name="text_items")
    x = models.FloatField()
    y = models.FloatField()
    text = models.TextField(blank=True)
    font_family = models.CharField(max_length=255, blank=True)
    font_size = models.CharField(max_length=32, blank=True)
    font_weight = models.CharField(max_length=32, blank=True)
    font_style = models.CharField(max_length=32, blank=True)
    font_kerning = models.CharField(max_length=32, blank=True)
    font_feature_settings = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=32, blank=True)
    opacity = models.FloatField(default=1)


class ArrowItem(models.Model):
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE, related_name="arrow_items")
    x1 = models.FloatField()
    y1 = models.FloatField()
    x2 = models.FloatField()
    y2 = models.FloatField()
