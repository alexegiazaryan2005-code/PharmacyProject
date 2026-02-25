from flask import Flask
from app.extensions import db

def create_app():
    app = Flask(__name__)

    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharmacy.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # Инициализация расширений
    db.init_app(app)

    # Регистрация пользовательского фильтра (если он у вас есть)
    @app.template_filter('safe_count')
    def safe_count_filter(collection):
        """Безопасный подсчет элементов в коллекции"""
        if hasattr(collection, 'count') and callable(collection.count):
            if not isinstance(collection, (list, tuple)):
                return collection.count()
        return len(collection)

    # Регистрация blueprint
    from app.routes import main
    app.register_blueprint(main)

    return app