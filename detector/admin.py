from django.contrib import admin
from .models import Analysis


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "image_name",
        "result",
        "confidence",
        "processing_time",
        "created_at",
    )

    list_filter = (
        "result",
        "created_at",
    )

    search_fields = (
        "image_name",
    )

    ordering = (
        "-created_at",
    )