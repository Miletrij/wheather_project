from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count
from .models import CitySearch, CityPopularity
import requests
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_GET

User = get_user_model()


def get_client_ip(request):
    """Получаем IP пользователя для анонимного трекинга"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def track_city_search(city, request):
    """Логируем поиск города"""
    CitySearch.objects.create(
        user=request.user if request.user.is_authenticated else None,
        city=city,
        ip_address=get_client_ip(request) if not request.user.is_authenticated else None,
        session_id=request.session.session_key if not request.user.is_authenticated else None
    )

    # Обновляем статистику популярности
    city_pop, created = CityPopularity.objects.get_or_create(city=city)
    city_pop.search_count += 1
    city_pop.save()


def get_weather(city_name, request):
    """Получаем погоду и логируем запрос"""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
        geo_response = requests.get(geo_url, timeout=5).json()

        if not geo_response.get('results'):
            return {'error': 'Город не найден'}

        location = geo_response['results'][0]
        lat, lon = location['latitude'], location['longitude']

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_data = requests.get(weather_url, timeout=5).json()

        # Логируем успешный поиск
        track_city_search(location['name'], request)

        return {
            'city': location['name'],
            'temperature': weather_data['current_weather']['temperature'],
            'windspeed': weather_data['current_weather']['windspeed'],
            'weathercode': weather_data['current_weather']['weathercode'],
        }
    except requests.RequestException as e:
        return {'error': f'Ошибка сервиса погоды: {str(e)}'}


class WeatherView(TemplateView):
    template_name = 'weather/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Для авторизованных пользователей
        if self.request.user.is_authenticated:
            recent_searches = CitySearch.objects.filter(
                user=self.request.user
            ).values('city').annotate(
                count=Count('city'),
                last_search=models.Max('timestamp')
            ).order_by('-last_search')[:5]
        # Для анонимных пользователей
        else:
            session_key = self.request.session.session_key or get_client_ip(self.request)
            recent_searches = CitySearch.objects.filter(
                ip_address=get_client_ip(self.request)
            ).values('city').annotate(
                count=Count('city'),
                last_search=models.Max('timestamp')
            ).order_by('-last_search')[:5]

        context['recent_searches'] = recent_searches
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        city = request.POST.get('city')

        if city:
            weather_data = get_weather(city, request)
            if 'error' in weather_data:
                context['error'] = weather_data['error']
            else:
                context['weather_data'] = weather_data

        return self.render_to_response(context)


@require_GET
def city_autocomplete(request):
    """API для автодополнения городов"""
    query = request.GET.get('query', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5"
        response = requests.get(url, timeout=3).json()
        suggestions = [result['name'] for result in response.get('results', [])]
        return JsonResponse({'results': suggestions})
    except requests.RequestException:
        return JsonResponse({'results': []})


@require_GET
def search_statistics(request):
    """API статистики поиска"""
    stats = CityPopularity.objects.order_by('-search_count')[:10]
    data = [{'city': item.city, 'count': item.search_count} for item in stats]
    return JsonResponse(data, safe=False)


@require_GET
def user_search_history(request):
    """API истории поиска пользователя"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    history = CitySearch.objects.filter(
        user=request.user
    ).values('city').annotate(
        count=Count('city'),
        last_search=models.Max('timestamp')
    ).order_by('-last_search')

    data = [{
        'city': item['city'],
        'count': item['count'],
        'last_search': item['last_search']
    } for item in history]

    return JsonResponse(data, safe=False)