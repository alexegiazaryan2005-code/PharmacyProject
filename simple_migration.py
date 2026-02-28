"""
Файл: simple_migration.py
Назначение: Упрощённая проверка доступности новых таблиц без использования Flask-Migrate.
Роль в проекте: быстрый smoke-test миграции.
"""

from app import create_app, db
from app.models import Supply, Sale, Transfer
import os


def simple_migration():
    """
    Создаёт отсутствующие таблицы и проверяет, что к ним можно выполнить базовый запрос.

    Параметры:
        Нет.

    Возвращает:
        None.

    Исключения:
        Внутри функции исключения перехватываются локально в каждом блоке `try/except`,
        чтобы диагностика продолжалась даже при проблеме с одной таблицей.

    Примеры:
        imple_migration()
        # Выведет статус проверки таблиц supply/sale/transfer
    """
    app = create_app()

    with app.app_context():
        print("🔄 Начинаем миграцию...")

        # Создаем таблицы (если их нет)
        db.create_all()

        # [БЛОК: поочерёдная диагностика таблиц]
        # Почему три отдельных try/except:
        # - ошибка в одной проверке не должна останавливать остальные,
        # - так проще локализовать проблему по конкретной таблице.
        # Альтернатива: цикл по списку моделей + универсальный обработчик, он короче, но менее нагляден новичкам.
        try:
            # Проверяем Supply
            Supply.query.first()
            print("✅ Таблица supply готова")
        except Exception as e:
            print(f"❌ Ошибка с supply: {e}")

        try:
            # Проверяем Sale
            Sale.query.first()
            print("✅ Таблица sale готова")
        except Exception as e:
            print(f"❌ Ошибка с sale: {e}")

        try:
            # Проверяем Transfer
            Transfer.query.first()
            print("✅ Таблица transfer готова")
        except Exception as e:
            print(f"❌ Ошибка с transfer: {e}")

        print("\n✅ Миграция завершена!")


if __name__ == '__main__':
    simple_migration()