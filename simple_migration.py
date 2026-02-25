from app import create_app, db
from app.models import Supply, Sale, Transfer
import os


def simple_migration():
    """Простая миграция без Flask-Migrate"""
    app = create_app()

    with app.app_context():
        print("🔄 Начинаем миграцию...")

        # Создаем таблицы (если их нет)
        db.create_all()

        # Проверяем создание таблиц
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