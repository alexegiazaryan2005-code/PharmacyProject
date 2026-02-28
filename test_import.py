"""
Файл: test_import.py
Назначение: Быстрая smoke-проверка импортов приложения и моделей.
Роль в проекте: диагностика окружения после установки зависимостей/рефакторинга.
"""

# Простой тест импорта
print("Тестируем импорт моделей...")

try:
    from app import create_app
    print("✅ Flask app импортирован")
except Exception as e:
    # Здесь перехватываем общий Exception, чтобы скрипт продолжил диагностику следующих импортов.
    # Альтернатива: падать сразу (fail fast), что полезно в CI-пайплайне.
    print(f"❌ Ошибка импорта app: {e}")

try:
    from app.models import Product, Category, Recept, Manufacturer, Pharmacy, Stock
    print("✅ Базовые модели импортированы")
except Exception as e:
    print(f"❌ Ошибка импорта базовых моделей: {e}")

try:
    from app.models import Supply, Sale, Transfer
    print("✅ Новые модели импортированы")
except Exception as e:
    print(f"❌ Ошибка импорта новых моделей: {e}")

print("\nПроверка завершена")