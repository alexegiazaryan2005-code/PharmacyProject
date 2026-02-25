#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import create_app
from app.extensions import db
import sys


def main():
    """Главная функция запуска приложения"""
    try:
        # Создаем приложение
        app = create_app()

        # Проверяем, что приложение создано
        if app is None:
            print("Ошибка: не удалось создать приложение")
            sys.exit(1)

        # Инициализируем базу данных в контексте приложения
        with app.app_context():
            db.create_all()
            print("База данных успешно инициализирована")
            print(f"URL базы данных: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Запускаем приложение
        print("Запуск сервера разработки...")
        app.run(debug=True, host='127.0.0.1', port=5000)

    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()