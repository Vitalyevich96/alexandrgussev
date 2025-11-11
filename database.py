from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Project, Service, ContactMessage, AdminUser
import os

# Создаем папку для данных если не существует
os.makedirs('data', exist_ok=True)

# Подключение к SQLite базе данных
SQLALCHEMY_DATABASE_URL = "sqlite:///data/portfolio.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация базы данных с тестовыми данными"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Создаем администратора по умолчанию
    if db.query(AdminUser).count() == 0:
        admin = AdminUser(username="admin")
        admin.set_password("admin123") 
        db.add(admin)
        db.commit()

    
    # Проверяем, есть ли уже сервисы
    if db.query(Service).count() == 0:
        services = [
            Service(
                title="Веб-приложения на Python",
                description="Разработка полнофункциональных веб-приложений с использованием FastAPI, Django или Flask.",
                icon="fas fa-laptop-code",
                price_range="от 15 000 ₽",
                featured=True
            ),
            Service(
                title="REST API разработка",
                description="Создание мощных и безопасных REST API для мобильных приложений и фронтенда.",
                icon="fas fa-server",
                price_range="от 10 000 ₽",
                featured=True
            ),
            Service(
                title="Интеграция с внешними API",
                description="Интеграция с платежными системами, социальными сетями, почтовыми сервисами.",
                icon="fas fa-plug",
                price_range="от 8 000 ₽",
                featured=True
            ),
            Service(
                title="Техническая консультация",
                description="Консультации по архитектуре, оптимизации кода, выбору технологий.",
                icon="fas fa-hands-helping",
                price_range="от 2 000 ₽/час",
                featured=False
            )
        ]
        
        for service in services:
            db.add(service)
    
    # Проверяем, есть ли уже проекты
    if db.query(Project).count() == 0:
        projects = [
            Project(
                title="Интернет-магазин на Django",
                description="Полнофункциональный интернет-магазин с корзиной, оплатой и системой управления заказами.",
                technologies="Django, PostgreSQL, Redis, Celery",
                image_url="/static/images/project1.jpg",
                project_url="https://example-shop.com",
                github_url="https://github.com/username/django-shop",
                featured=True
            ),
            Project(
                title="REST API для мобильного приложения",
                description="Высоконагруженный REST API для мобильного приложения с аутентификацией.",
                technologies="FastAPI, MongoDB, JWT, WebSockets",
                image_url="/static/images/project2.jpg",
                project_url="https://api.example.com",
                github_url="https://github.com/username/fastapi-mobile",
                featured=True
            ),
            Project(
                title="Система аналитики данных",
                description="Система для сбора и визуализации аналитических данных с дашбордом.",
                technologies="Flask, Pandas, Matplotlib, SQLite",
                image_url="/static/images/project3.jpg",
                project_url="https://analytics.example.com",
                github_url="https://github.com/username/data-analytics",
                featured=True
            )
        ]
        
        for project in projects:
            db.add(project)
    
    db.commit()
    db.close()