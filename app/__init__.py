"""
Файл: app/__init__.py
Назначение: Фабрика Flask-приложения (application factory).
Роль в архитектуре: точка сборки всех частей системы — конфигурации, расширений и маршрутов.

Импорты:
- flask.Flask: основной объект веб-приложения.
- app.extensions.db: ORM-расширение для подключения БД.

Связи:
- run.py вызывает create_app() для запуска сервера.
- app/routes.py подключается как Blueprint.
- app/models.py использует db, инициализируемый здесь через init_app.
"""

from flask import Flask
from app.extensions import db


def create_app():
    """
    Создаёт и настраивает экземпляр Flask-приложения.

    Параметры:
        Нет.

    Возвращает:
        Flask: полностью настроенный объект приложения.

    Исключения:
        Явно не выбрасывает, но может прокинуть ошибки импорта, конфигурации или
        инициализации расширений.

    Примеры:
        >>> app = create_app()
        >>> app.name
        'app'
    """
    app = Flask(__name__)

    # [БЛОК: базовая конфигурация]
    # Здесь задаются ключевые параметры приложения.
    # **Почему так**: значения определены прямо в коде для простого локального старта.
    # Альтернатива: класс Config и переменные окружения (предпочтительно для production).
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharmacy.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # [БЛОК: инициализация расширений]
    # init_app связывает заранее созданный объект db с конкретным экземпляром Flask.
    db.init_app(app)

    # [БЛОК: Jinja-фильтр для безопасного подсчёта]
    # Фильтр учитывает, что у SQLAlchemy Query есть count(), а у list/tuple обычно используют len().
    @app.template_filter('safe_count')
    def safe_count_filter(collection):
        """
        Безопасно считает элементы в разных типах коллекций.

        Параметры:
            collection (Any): список, кортеж, SQLAlchemy Query или похожий объект.

        Возвращает:
            int: количество элементов.

        Исключения:
            Может выбросить TypeError, если объект не поддерживает ни count(), ни len().

        Примеры:
            >>> safe_count_filter([1, 2, 3])
            3
        """
        # Сначала проверяем «запросоподобные» объекты с методом count().
        if hasattr(collection, 'count') and callable(collection.count):
            # Для list/tuple count() считает вхождения значения, а не длину,
            # поэтому для них этот путь запрещаем.
            if not isinstance(collection, (list, tuple)):
                return collection.count()
        return len(collection)

    # [БЛОК: регистрация маршрутов]
    # Blueprint помогает декомпозировать приложение на модули.
    # Альтернатива: объявлять все маршруты прямо в app, что хуже масштабируется.
    from app.routes import main
    app.register_blueprint(main)

    return app