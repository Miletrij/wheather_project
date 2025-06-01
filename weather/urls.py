from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather_view, name='weather'),
    path('autocomplete/', views.city_autocomplete, name='city_autocomplete'),
]