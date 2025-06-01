from django.contrib import admin
from .models import CitySearch, CityPopularity

@admin.register(CitySearch)
class CitySearchAdmin(admin.ModelAdmin):
    list_display = ('city', 'user', 'ip_address', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('city', 'user__username', 'ip_address')

@admin.register(CityPopularity)
class CityPopularityAdmin(admin.ModelAdmin):
    list_display = ('city', 'search_count')
    ordering = ('-search_count',)