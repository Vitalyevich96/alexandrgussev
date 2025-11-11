from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
import secrets

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    technologies = Column(String(300))
    image_url = Column(String(500), default="/static/images/default-project.jpg")
    project_url = Column(String(500))
    github_url = Column(String(500))
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(50), default="fas fa-code")
    price_range = Column(String(100))
    featured = Column(Boolean, default=False)

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    company = Column(String(100))
    budget = Column(String(50))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

class AdminUser(Base):  # ← Этот класс должен быть на одном уровне с другими классами
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password: str):
        """Установка пароля с солью"""
        self.salt = secrets.token_hex(16)
        password_with_salt = password + self.salt
        self.password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Проверка пароля"""
        password_with_salt = password + self.salt
        return hashlib.sha256(password_with_salt.encode()).hexdigest() == self.password_hash