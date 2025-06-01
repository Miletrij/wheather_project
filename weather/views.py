from django.shortcuts import render
import requests
from django.conf import settings


def get_weather(city_name):
    """Получаем данные о погоде через Open-Meteo API"""
    # Сначала получаем координаты города
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
    geo_response = requests.get(geo_url).json()

    if not geo_response.get('results'):
        return None

    location = geo_response['results'][0]
    lat, lon = location['latitude'], location['longitude']

    # Затем получаем прогноз погоды
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather_data = requests.get(weather_url).json()

    return {
        'city': location['name'],
        'temperature': weather_data['current_weather']['temperature'],
        'windspeed': weather_data['current_weather']['windspeed'],
        'weathercode': weather_data['current_weather']['weathercode'],
    }


def weather_view(request):
    context = {}

    if request.method == 'POST':
        city = request.POST.get('city')
        if city:
            weather_data = get_weather(city)
            if weather_data:
                context['weather_data'] = weather_data
            else:
                context['error'] = "Город не найден"

    return render(request, 'weather/index.html', context)