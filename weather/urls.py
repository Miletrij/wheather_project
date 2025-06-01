from django.urls import path
from . import views

urlpatterns = [
    path('', views.WeatherView.as_view(), name='weather'),
    path('autocomplete/', views.city_autocomplete, name='city_autocomplete'),
    path('api/stats/', views.search_statistics, name='search_stats'),
    path('api/history/', views.user_search_history, name='user_history'),
]