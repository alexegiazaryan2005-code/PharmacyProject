from app.extensions import db

# Для обратной совместимости
Base = db.Model
metadata = db.metadata
SessionLocal = db.session
engine = db.engine

def get_db():
    """Функция для получения сессии"""
    db_session = db.session
    try:
        yield db_session
    finally:
        db_session.close()