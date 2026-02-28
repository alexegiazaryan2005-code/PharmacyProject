"""
Файл: check_db_file.py
Назначение: Проверка физического файла SQLite-базы (путь, наличие, размер, права доступа).
Роль в проекте: low-level диагностика файловой системы, когда ORM-подключение вызывает вопросы.
"""

import os
from app import create_app

app = create_app()

with app.app_context():
    # [БЛОК: нормализация пути к БД]
    # SQLite URI может быть относительным; приводим к абсолютному пути для надёжной проверки.
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

    # Проверяем абсолютный путь
    if not os.path.isabs(db_path):
        # Если относительный путь, делаем абсолютным
        db_path = os.path.join(app.instance_path, db_path)

    print(f"📁 Путь к файлу БД: {db_path}")
    print(f"📁 Папка instance: {app.instance_path}")

    # [БЛОК: ветвление по существованию файла]
    # if/else здесь проще и понятнее, чем исключения по `open`,
    # потому что нужно ещё обработать отсутствие папки instance.
    if os.path.exists(db_path):
        print(f"✅ Файл БД существует")
        print(f"📏 Размер файла: {os.path.getsize(db_path)} байт")
        print(f"🔐 Права доступа: {oct(os.stat(db_path).st_mode)[-3:]}")
    else:
        print(f"❌ Файл БД НЕ существует по указанному пути")

        # Проверяем, есть ли права на запись в папку
        if os.path.exists(app.instance_path):
            print(f"✅ Папка instance существует")
            print(f"🔐 Права на папку: {oct(os.stat(app.instance_path).st_mode)[-3:]}")
        else:
            print(f"❌ Папка instance не существует")
            # Создаем папку
            os.makedirs(app.instance_path, exist_ok=True)
            print(f"✅ Папка instance создана")