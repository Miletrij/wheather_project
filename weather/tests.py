from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware

from .models import CitySearch, CityPopularity
from .views import WeatherView, city_autocomplete, search_statistics
import json
from unittest.mock import patch



class ModelTests(TestCase):
    """тесты моделей данных"""
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_city_search_creation(self):
        """Тестируем создание записи поиска города"""
        search = CitySearch.objects.create(
            user=self.user,
            city='Москва',
            ip_address='127.0.0.1'
        )
        self.assertEqual(search.city, 'Москва')
        self.assertEqual(search.user.username, 'testuser')

    def test_city_popularity(self):
        """Тестируем подсчет популярности городов"""
        CityPopularity.objects.create(city='Москва', search_count=5)
        popularity = CityPopularity.objects.get(city='Москва')
        self.assertEqual(popularity.search_count, 5)


class ViewTests(TestCase):
    """тесты основных представлений"""
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def add_session_to_request(self, request):
        """Добавляем сессию к тестовому запросу"""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

    @patch('weather.views.requests.get')
    def test_weather_view_post(self, mock_get):
        """Тестируем POST-запрос с валидным городом"""
        # Мокаем API ответы
        mock_get.side_effect = [
            # Ответ геокодинга
            type('MockResponse', (), {
                'json': lambda: {
                    'results': [{
                        'name': 'Москва',
                        'latitude': 55.75,
                        'longitude': 37.61
                    }]
                }
            }),
            # Ответ погоды
            type('MockResponse', (), {
                'json': lambda: {
                    'current_weather': {
                        'temperature': 20,
                        'windspeed': 10,
                        'weathercode': 1
                    }
                }
            })
        ]

        request = self.factory.post('/', {'city': 'Москва'})
        self.add_session_to_request(request)
        request.user = self.user

        response = WeatherView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Москва')

        # Проверяем, что поиск сохранился в БД
        self.assertTrue(CitySearch.objects.filter(city='Москва').exists())
        self.assertTrue(CityPopularity.objects.filter(city='Москва').exists())


    def test_weather_view_get(self):
        """Тестируем GET-запрос"""
        request = self.factory.get('/')
        self.add_session_to_request(request)
        request.user = self.user

        # Добавляем тестовые данные
        CitySearch.objects.create(user=self.user, city='Москва')
        CitySearch.objects.create(user=self.user, city='Санкт-Петербург')

        response = WeatherView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Москва')
        self.assertContains(response, 'Санкт-Петербург')


class APITests(TestCase):
    """API-тесты"""
    def setUp(self):
        self.factory = RequestFactory()

    @patch('weather.views.requests.get')
    def test_city_autocomplete(self, mock_get):
        """Тестируем автодополнение городов"""
        mock_get.return_value.json.return_value = {
            'results': [
                {'name': 'Москва'},
                {'name': 'Московская область'}
            ]
        }

        request = self.factory.get('/autocomplete/?query=Моск')
        response = city_autocomplete(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['results'], ['Москва', 'Московская область'])

    def test_search_statistics(self):
        """Тестируем API статистики"""
        # Создаем тестовые данные
        CityPopularity.objects.create(city='Москва', search_count=10)
        CityPopularity.objects.create(city='Санкт-Петербург', search_count=5)

        request = self.factory.get('/api/stats/')
        response = search_statistics(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['city'], 'Москва')
        self.assertEqual(data[0]['count'], 10)


class AnonymousUserTests(TestCase):
    """Тесты для анонимных пользователей"""
    def setUp(self):
        self.factory = RequestFactory()

    def add_middleware(self, request):
        """Добавляем необходимые middleware к запросу"""
        middleware = [
            SessionMiddleware(lambda req: None),
            MessageMiddleware(lambda req: None),
            AuthenticationMiddleware(lambda req: None),
        ]
        for m in middleware:
            m.process_request(request)
        request.session.save()
        request.user = AnonymousUser()  # Явно устанавливаем анонимного пользователя

    def test_anonymous_user_history(self):
        """Тестируем историю поиска для анонимных пользователей"""
        request = self.factory.get('/')
        self.add_middleware(request)

        # Добавляем сессию
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Добавляем тестовые данные с IP
        CitySearch.objects.create(ip_address='127.0.0.1', city='Москва')
        CitySearch.objects.create(ip_address='127.0.0.1', city='Казань')

        response = WeatherView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Москва')
        self.assertContains(response, 'Казань')

