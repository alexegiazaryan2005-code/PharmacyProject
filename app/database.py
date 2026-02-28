"""
Файл: app/database.py
Назначение: Совместимость с «классическим» стилем SQLAlchemy (Base/Session/engine) поверх Flask-SQLAlchemy.
Роль в архитектуре: адаптерный модуль (adapter), чтобы старый код или утилиты могли работать без полной переработки.

Импорты:
- app.extensions.db: единый ORM-объект проекта.

Связи:
- Используется скриптами миграции/обновления, где ожидаются атрибуты Base, SessionLocal и engine.
"""

from app.extensions import db

# Для обратной совместимости со стилем «чистого SQLAlchemy».
# Альтернатива: везде использовать только db.Model / db.session напрямую.
# Текущий подход полезен, когда проект эволюционирует и часть кода написана в другом стиле.
Base = db.Model
metadata = db.metadata
SessionLocal = db.session
engine = db.engine


def get_db():
    """
    Возвращает сессию БД в виде генератора для паттерна dependency injection.

    Параметры:
        Нет.

    Возвращает:
        Generator[Session, None, None]: объект сессии SQLAlchemy (`db.session`).

    Исключения:
        Явно не выбрасывает, но при проблемах соединения/запросов исключения произойдут
        в месте использования сессии.

    Примеры:
        db_gen = get_db()
        session = next(db_gen)
        # ... работа с session ...
    """
    db_session = db.session
    try:
        # **Почему генератор**: удобно для фреймворков и тестов, где нужна гарантированная очистка ресурса.
        # Альтернатива: возвращать сессию напрямую (return db.session), но тогда закрытие нужно контролировать вручную.
        yield db_session
    finally:
        # Блок finally выполняется всегда: и при успехе, и при исключении.
        db_session.close()