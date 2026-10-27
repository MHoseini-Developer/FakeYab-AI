from django.db import models


class Analysis(models.Model):

    image_name = models.CharField(max_length=255)

    result = models.CharField(max_length=10)

    confidence = models.FloatField()

    fake_probability = models.FloatField()

    real_probability = models.FloatField()

    processing_time = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.image_name} - {self.result}"