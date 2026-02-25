# Простой тест импорта
print("Тестируем импорт моделей...")

try:
    from app import create_app
    print("✅ Flask app импортирован")
except Exception as e:
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