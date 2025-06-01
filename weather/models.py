from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CitySearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    city = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
        ]


class CityPopularity(models.Model):
    city = models.CharField(max_length=100, unique=True)
    search_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Популярность городов"