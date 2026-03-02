"""
Файл: temp_test.py
Назначение: Самодостаточный тестовый Flask-сервер с inline-шаблонами для проверки вёрстки списков.
Роль в проекте: изолированная песочница (sandbox) для ручного UI-тестирования без основной БД.

Импорты:
- flask.Flask: минимальное веб-приложение.
- flask.render_template_string: рендер HTML-шаблонов из строк.
"""

from flask import Flask, render_template_string

app = Flask(__name__)

# ========== ШАБЛОН ПРОДАЖ ==========
# Встроенный шаблон выбран для изолированного теста: не зависит от файловой системы templates/.
# Альтернатива: render_template('sales_list.html') с реальным шаблоном проекта.
# Это ближе к production, но усложняет локальную диагностику конкретного фрагмента.
SALES_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Список продаж</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; background-color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .btn { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin-bottom: 20px; }
        .btn:hover { background-color: #45a049; }
        .btn-edit { background-color: #2196F3; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px; margin-right: 5px; }
        .btn-delete { background-color: #f44336; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px; }
        .btn-edit:hover { background-color: #1976D2; }
        .btn-delete:hover { background-color: #d32f2f; }
    </style>
</head>
<body>
    <h1>Список продаж</h1>

    <a href="/sales/create/" class="btn">Добавить новую продажу</a>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Продукт</th>
                <th>Количество</th>
                <th>Цена за единицу</th>
                <th>Общая сумма</th>
                <th>Дата продажи</th>
                <th>Покупатель</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for sale in sales %}
                {#
                    Конструкция for...else в Jinja:
                    - блок for выполняется, если список sales не пустой;
                    - блок else выполняется, если элементов нет.
                    Альтернатива: отдельный if sales перед циклом.
                #}
            <tr>
                <td>{{ sale.id }}</td>
                <td>{{ sale.product.name }}</td>
                <td>{{ sale.quantity }}</td>
                <td>{{ sale.unit_price }}</td>
                <td>{{ sale.total_amount }}</td>
                <td>{{ sale.sale_date }}</td>
                <td>{{ sale.customer.name }}</td>
                <td>
                    <a href="/sales/{{ sale.id }}/edit/" class="btn-edit">Редактировать</a>
                    <a href="/sales/{{ sale.id }}/delete/" class="btn-delete" onclick="return confirm('Вы уверены?')">Удалить</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="8" style="text-align: center;">Нет доступных продаж</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

# ========== ШАБЛОН ПЕРЕМЕЩЕНИЙ ==========
# Аналогичный подход со строковым шаблоном позволяет быстро тестировать только UI-логику.
TRANSFERS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Список перемещений</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #FF9800; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; background-color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #FF9800; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .btn { display: inline-block; padding: 10px 20px; background-color: #FF9800; color: white; text-decoration: none; border-radius: 4px; margin-bottom: 20px; }
        .btn:hover { background-color: #F57C00; }
        .btn-edit { background-color: #2196F3; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px; margin-right: 5px; }
        .btn-delete { background-color: #f44336; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px; }
        .btn-edit:hover { background-color: #1976D2; }
        .btn-delete:hover { background-color: #d32f2f; }
        .status-completed { color: green; font-weight: bold; }
        .status-pending { color: orange; font-weight: bold; }
        .status-cancelled { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Список перемещений</h1>

    <a href="/transfers/create/" class="btn">Добавить новое перемещение</a>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Продукт</th>
                <th>Количество</th>
                <th>Откуда</th>
                <th>Куда</th>
                <th>Дата перемещения</th>
                <th>Статус</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for transfer in transfers %}
                {#
                    Ветка if/elif/else в шаблоне маппит внутренние статусы на человекочитаемые подписи.
                    Альтернатива: подготовить display_status на стороне Python и упростить HTML.
                #}
            <tr>
                <td>{{ transfer.id }}</td>
                <td>{{ transfer.product.name }}</td>
                <td>{{ transfer.quantity }}</td>
                <td>{{ transfer.from_location.name }}</td>
                <td>{{ transfer.to_location.name }}</td>
                <td>{{ transfer.transfer_date }}</td>
                <td>
                    {% if transfer.status == 'completed' %}
                        <span class="status-completed">Завершено</span>
                    {% elif transfer.status == 'pending' %}
                        <span class="status-pending">В ожидании</span>
                    {% elif transfer.status == 'cancelled' %}
                        <span class="status-cancelled">Отменено</span>
                    {% else %}
                        {{ transfer.status }}
                    {% endif %}
                </td>
                <td>
                    <a href="/transfers/{{ transfer.id }}/edit/" class="btn-edit">Редактировать</a>
                    <a href="/transfers/{{ transfer.id }}/delete/" class="btn-delete" onclick="return confirm('Вы уверены?')">Удалить</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="8" style="text-align: center;">Нет доступных перемещений</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""


# ========== МАРШРУТЫ ==========
@app.route('/')
# Главная страница сайта
def index():
    """
    Отдаёт стартовую страницу с ссылками на тестовые сценарии.

    Возвращает:
        str: HTML-фрагмент.

    Исключения:
        Явно не выбрасывает; потенциальные ошибки ограничены формированием строки.

    Примеры:
        GET /
    """
    return '''
    <h1>✅ ТЕСТОВЫЙ СЕРВЕР РАБОТАЕТ!</h1>
    <p>Проверка исправленных шаблонов:</p>
    <ul>
        <li><a href="/test-sales">/test-sales</a> - продажи (пустой список)</li>
        <li><a href="/test-transfers">/test-transfers</a> - перемещения (пустой список)</li>
        <li><a href="/test-sales-with-data">/test-sales-with-data</a> - продажи с данными</li>
        <li><a href="/test-transfers-with-data">/test-transfers-with-data</a> - перемещения с данными</li>
    </ul>
    '''


@app.route('/test-sales')
# Тест продаж: проверка работы с БД
def test_sales():
    """
    Проверяет шаблон продаж на граничном случае пустого списка.

    Почему важно:
        В Jinja-блоке `{% for %} ... {% else %}` должно отработать сообщение «нет данных».

    Возвращает:
        Response: HTML, собранный через `render_template_string`.

    Примеры:
        GET /test-sales
    """
    return render_template_string(SALES_TEMPLATE, sales=[])


@app.route('/test-transfers')
# Тест переводов: проверка перемещения средств
def test_transfers():
    """
    Проверяет шаблон перемещений на пустом наборе данных.

    Возвращает:
        Response: HTML с fallback-строкой «Нет доступных перемещений».
    """
    return render_template_string(TRANSFERS_TEMPLATE, transfers=[])


@app.route('/test-sales-with-data')
# Тест продаж с предварительным заполнением данных
def test_sales_with_data():
    """
    Проверяет шаблон продаж с искусственными данными.

    Подход:
        Внутренние классы Test* имитируют структуру реальных ORM-объектов.
        Альтернатива: использовать фикстуры pytest или мок-объекты.

    Возвращает:
        Response: HTML таблица с тестовыми продажами.

    Примеры:
        GET /test-sales-with-data
    """

    class TestProduct:
        """
        Минимальная модель товара для шаблона.

        Что моделирует:
            Сущность продукта с полем `name`.

        ООП:
            **Инкапсуляция** — состояние объекта (`name`) хранится внутри экземпляра.
        """
        def __init__(self):
            """Инициализирует тестовый продукт с фиксированным названием."""
            self.name = "Тестовый продукт"

    class TestCustomer:
        """Минимальная модель покупателя, содержащая только отображаемое имя."""
        def __init__(self):
            """Инициализирует тестового покупателя с фиктивным ФИО."""
            self.name = "Иванов И.И."

    class TestSale:
        """
        Тестовая модель продажи, повторяющая поля, которые ожидает HTML-шаблон.

        Параметры:
            id (int): идентификатор продажи.
            quantity (int): количество единиц товара.
            price (float): цена одной единицы.

        Возвращает:
            None: конструктор только заполняет атрибуты экземпляра.
        """
        def __init__(self, id, quantity, price):
            self.id = id
            self.product = TestProduct()
            self.quantity = quantity
            self.unit_price = price
            self.total_amount = quantity * price
            self.sale_date = "2026-02-19"
            self.customer = TestCustomer()

    # [БЛОК: генерация тестовых данных]
    # Список выбран как упорядоченная коллекция, которую удобно итерировать в шаблоне.
    test_sales = [
        TestSale(1, 5, 100.50),
        TestSale(2, 2, 250.00),
        TestSale(3, 10, 75.25)
    ]

    return render_template_string(SALES_TEMPLATE, sales=test_sales)


@app.route('/test-transfers-with-data')
# Тест переводов с предварительным заполнением данных
def test_transfers_with_data():
    """
    Проверяет шаблон перемещений с тестовыми записями разных статусов.

    Возвращает:
        Response: HTML-таблица, где видна работа цветовой маркировки статусов.
    """

    class TestProduct:
        """Упрощённая тестовая сущность товара для отображения в шаблоне."""
        def __init__(self):
            """Инициализирует товар с фиксированным названием."""
            self.name = "Тестовый продукт"

    class TestLocation:
        """
        Тестовая сущность локации (аптеки/склада).

        Параметры:
            name (str): человекочитаемое имя локации.
        """
        def __init__(self, name):
            self.name = name

    class TestTransfer:
        """
        Тестовая модель перемещения между локациями.

        Параметры:
            id (int): идентификатор перемещения.
            quantity (int): количество единиц.
            status (str): один из ожидаемых статусов (`completed`, `pending`, `cancelled`).
            from_loc (str): название исходной локации.
            to_loc (str): название целевой локации.
        """
        def __init__(self, id, quantity, status, from_loc, to_loc):
            self.id = id
            self.product = TestProduct()
            self.quantity = quantity
            self.from_location = TestLocation(from_loc)
            self.to_location = TestLocation(to_loc)
            self.transfer_date = "2026-02-19"
            self.status = status

    # [БЛОК: тестовые сценарии статусов]
    # Подбираем три разных статуса, чтобы проверить все ветки if/elif в шаблоне.
    test_transfers = [
        TestTransfer(1, 10, "completed", "Аптека №1", "Аптека №2"),
        TestTransfer(2, 5, "pending", "Аптека №2", "Аптека №3"),
        TestTransfer(3, 15, "cancelled", "Аптека №1", "Аптека №4")
    ]

    return render_template_string(TRANSFERS_TEMPLATE, transfers=test_transfers)


if __name__ == '__main__':
    # [БЛОК: ручной запуск тестового сервера]
    # debug=True выбран для учебного режима (автоперезагрузка, подробный traceback).
    # Для production обычно используют WSGI-сервер (gunicorn/uwsgi/waitress) и debug=False.
    print("\n" + "=" * 60)
    print("🚀 ТЕСТОВЫЙ СЕРВЕР ЗАПУЩЕН")
    print("📌 Адрес: http://127.0.0.1:5001")
    print("📌 Проверяемые исправления:")
    print("   - {% empty %} заменен на {% else %} в циклах")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5001)