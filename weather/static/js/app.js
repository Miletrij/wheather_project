$(document).ready(function() {
    // Автодополнение городов при вводе
    $('#city').on('input', function() {
        const query = $(this).val();
        if (query.length < 2) {
            $('#autocomplete-list').empty();
            return;
        }

        // Запрос к нашему API автодополнения
        $.get('/autocomplete/', {query: query}, function(data) {
            const suggestions = $('#autocomplete-list');
            suggestions.empty();

            // Добавляем каждый вариант в список
            data.results.forEach(function(city) {
                $('<div>')
                    .append($("<strong>").text(city))
                    .appendTo(suggestions)
                    .on("click", function() {
                        $('#city').val(city);
                        suggestions.empty();
                    });
            });
        });
    });

    // Загрузка статистики популярных городов
    function loadPopularCities() {
        $.get('/api/stats/', function(data) {
            let html = '';
            data.forEach(function(item) {
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>${item.city}</span>
                        <span class="badge bg-primary rounded-pill">${item.count}</span>
                    </div>
                `;
            });
            $('#popular-cities').html(html || '<p>Нет данных</p>');

            // Для авторизованных пользователей добавляем кнопку истории
            {% if user.is_authenticated %}
            $('<a href="/api/history/" class="btn btn-sm btn-link mt-2" target="_blank">Вся история</a>')
                .appendTo('#popular-cities');
            {% endif %}
        });
    }

    // Инициализация загрузки статистики
    loadPopularCities();
});