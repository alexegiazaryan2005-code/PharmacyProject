#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Файл: run.py
Назначение: Точка входа (entry point) для локального запуска Flask-приложения.
Роль в архитектуре: orchestration-скрипт — создаёт app, инициализирует БД и стартует dev-сервер.

Импорты:
- app.create_app: фабрика приложения.
- app.extensions.db: объект ORM для вызова create_all().
- sys: завершение процесса с кодом ошибки.

Связи:
- Использует конфигурацию из app/__init__.py.
- Работает с моделями из app/models.py через metadata в db.
"""

from app import create_app
from app.extensions import db
import sys


def main():
    """
    Запускает приложение и выполняет первичную инициализацию базы данных.

    Параметры:
        Нет.

    Возвращает:
        None.

    Исключения:
        Не пробрасывает наружу: любые исключения перехватываются в try/except,
        после чего процесс завершается с кодом 1.

    Примеры:
        >>> main()
        # Приложение стартует на http://127.0.0.1:5000
    """
    try:
        # Создаем приложение
        app = create_app()

        # Проверяем, что приложение создано
        if app is None:
            print("Ошибка: не удалось создать приложение")
            sys.exit(1)

        # [БЛОК: инициализация БД]
        # app_context обязателен, потому что Flask-SQLAlchemy использует контекст приложения
        # для доступа к текущей конфигурации и соединению.
        # Альтернатива: отдельная CLI-команда (`flask --app ... init-db`) для production-окружений.
        with app.app_context():
            db.create_all()
            print("База данных успешно инициализирована")
            print(f"URL базы данных: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # [БЛОК: запуск сервера разработки]
        # debug=True полезен для разработки (автоперезагрузка, подробные ошибки),
        # но небезопасен в production.
        print("Запуск сервера разработки...")
        app.run(debug=True, host='127.0.0.1', port=5000)

    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()