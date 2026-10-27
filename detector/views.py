from django.http import JsonResponse
from django.shortcuts import render
from PIL import Image

from .model_service import predict
import time
from .models import Analysis

from django.db.models import Count
from django.db.models.functions import TruncDate

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

import logging

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "detector/index.html")


def analyze(request):
    return render(request, "detector/analyze.html")


def dashboard(request):
    total_analyses = Analysis.objects.count()

    fake_count = Analysis.objects.filter(result="FAKE").count()
    real_count = Analysis.objects.filter(result="REAL").count()

    if total_analyses > 0:
        fake_percentage = (fake_count / total_analyses) * 100
        real_percentage = (real_count / total_analyses) * 100
    else:
        fake_percentage = 0
        real_percentage = 0

    if total_analyses > 0:
        average_confidence = (
            sum(
                analysis.confidence
                for analysis in Analysis.objects.all()
            ) / total_analyses
        ) * 100
    else:
        average_confidence = 0

    recent_analyses = Analysis.objects.order_by("-created_at")[:5]

    daily_stats = (
        Analysis.objects
        .filter(created_at__gte=timezone.now() - timedelta(days=30))
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            total=Count("id"),
            fake=Count("id", filter=Q(result="FAKE")),
        )
        .order_by("day")
    )

    daily_stats = list(daily_stats)

    max_total = max(
        (item["total"] for item in daily_stats),
        default=1
    )

    chart_data = []

    for item in daily_stats:
        total_height = (item["total"] / max_total) * 100
        fake_height = (item["fake"] / max_total) * 100

        chart_data.append({
            "day": item["day"],
            "total_height": round(total_height, 2),
            "fake_height": round(fake_height, 2),
        })

    context = {
        "total_analyses": total_analyses,
        "fake_count": fake_count,
        "real_count": real_count,
        "average_confidence": average_confidence,
        "recent_analyses": recent_analyses,
        "daily_stats": daily_stats,
        "chart_data": chart_data,
        "fake_percentage": fake_percentage,
        "real_percentage": real_percentage,
    }

    return render(
        request,
        "detector/dashboard.html",
        context
    )


def about(request):
    return render(request, "detector/about.html")


def contact(request):
    return render(request, "detector/contact.html")



def analyze_api(request):
    start_time = time.perf_counter()

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405
        )

    if "image" not in request.FILES:
        return JsonResponse(
            {"error": "No image was uploaded."},
            status=400
        )

    uploaded_file = request.FILES["image"]

    allowed_extensions = ["jpg", "jpeg", "png", "webp"]
    extension = uploaded_file.name.split(".")[-1].lower()

    if extension not in allowed_extensions:
        return JsonResponse(
            {"error": "Invalid image format."},
            status=400
        )

    max_size = 10 * 1024 * 1024

    if uploaded_file.size > max_size:
        return JsonResponse(
            {"error": "Image size must be less than 10MB."},
            status=400
        )

    # اعتبارسنجی فایل تصویر
    try:
        image = Image.open(uploaded_file)
        image.verify()

        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image = image.convert("RGB")

    except Exception:
        return JsonResponse(
            {"error": "Invalid image file."},
            status=400
        )

    # اجرای مدل و ذخیره نتیجه
    try:
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()

        prediction = predict(image_bytes)

        fake_probability = prediction["fake_probability"]
        real_probability = prediction["real_probability"]
        result = "FAKE" if prediction["is_fake"] else "REAL"

        confidence = max(fake_probability, real_probability)
        processing_time = time.perf_counter() - start_time

        Analysis.objects.create(
            image_name=uploaded_file.name,
            result=result,
            confidence=confidence,
            fake_probability=fake_probability,
            real_probability=real_probability,
            processing_time=processing_time,
        )

        return JsonResponse({
            "result": result,
            "is_fake": prediction["is_fake"],
            "confidence": confidence,
            "fake_probability": fake_probability,
            "real_probability": real_probability,
            "processing_time": processing_time,
        })

    except Exception:
        logger.exception("Image analysis failed")

        return JsonResponse(
            {"error": "An error occurred while analyzing the image."},
            status=500
        )
