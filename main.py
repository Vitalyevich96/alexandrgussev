from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import models
import database
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta

app = FastAPI(
    title="Python Web Development Services",
    description="Профессиональная разработка веб-приложений на Python",
    version="1.0.0"
)

# Инициализация шаблонов и статики
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Простой секретный ключ для подписи сессий
SECRET_KEY = "your-secret-key-change-this-in-production"
session_storage = {}

# Модели Pydantic
class ContactForm(BaseModel):
    name: str
    email: str
    phone: str = None
    company: str = None
    budget: str = None
    message: str

class LoginForm(BaseModel):
    username: str
    password: str

class ChangePasswordForm(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

# Инициализация БД при старте
@app.on_event("startup")
def startup():
    database.init_db()

# Функция для проверки аутентификации
def get_current_admin(request: Request, db: Session = Depends(database.get_db)):
    """Получение текущего администратора из сессии"""
    session_id = request.cookies.get("admin_session")
    if not session_id or session_id not in session_storage:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"}
        )
    
    session_data = session_storage[session_id]
    if datetime.now() > session_data["expires"]:
        del session_storage[session_id]
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"}
        )
    
    admin = db.query(models.AdminUser).filter(models.AdminUser.username == session_data["username"]).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"}
        )
    
    return admin

# Маршруты для публичной части (остаются без изменений)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(database.get_db)):
    featured_projects = db.query(models.Project).filter(models.Project.featured == True).limit(3).all()
    featured_services = db.query(models.Service).filter(models.Service.featured == True).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": featured_projects,
        "services": featured_services
    })

@app.get("/services", response_class=HTMLResponse)
async def services(request: Request, db: Session = Depends(database.get_db)):
    services_list = db.query(models.Service).all()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "services": services_list
    })

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request, db: Session = Depends(database.get_db)):
    projects = db.query(models.Project).all()
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "projects": projects
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact_form(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.post("/contact")
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    company: str = Form(None),
    budget: str = Form(None),
    message: str = Form(...),
    db: Session = Depends(database.get_db)
):
    contact_message = models.ContactMessage(
        name=name,
        email=email,
        phone=phone,
        company=company,
        budget=budget,
        message=message
    )
    
    db.add(contact_message)
    db.commit()
    
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "success": True,
        "message": "Ваше сообщение успешно отправлено! Я свяжусь с вами в ближайшее время."
    })

# Маршруты для админ-панели с аутентификацией
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
    if not admin or not admin.check_password(password):
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль"
        })
    
    # Создаем сессию
    session_id = secrets.token_urlsafe(32)
    session_storage[session_id] = {
        "username": username,
        "expires": datetime.now() + timedelta(hours=24)
    }
    
    # Устанавливаем cookie
    response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="admin_session",
        value=session_id,
        httponly=True,
        max_age=24*60*60,  # 24 часа
        secure=False  # В продакшене установите True для HTTPS
    )
    
    return response

@app.get("/admin/logout")
async def admin_logout(response: Response):
    """Выход из системы"""
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("admin_session")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request, 
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin)
):
    messages = db.query(models.ContactMessage).order_by(models.ContactMessage.created_at.desc()).all()
    projects_count = db.query(models.Project).count()
    services_count = db.query(models.Service).count()
    unread_messages = db.query(models.ContactMessage).filter(models.ContactMessage.read == False).count()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "messages": messages,
        "projects_count": projects_count,
        "services_count": services_count,
        "unread_messages": unread_messages,
        "admin_username": admin.username
    })

# Маршруты для смены пароля
@app.get("/admin/change-password", response_class=HTMLResponse)
async def change_password_page(
    request: Request,
    admin: models.AdminUser = Depends(get_current_admin)
):
    return templates.TemplateResponse("change_password.html", {
        "request": request,
        "admin_username": admin.username
    })

@app.post("/admin/change-password")
async def change_password(
    request: Request,
    response: Response,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin)
):
    # Проверяем текущий пароль
    if not admin.check_password(current_password):
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "admin_username": admin.username,
            "error": "Неверный текущий пароль"
        })
    
    # Проверяем совпадение новых паролей
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "admin_username": admin.username,
            "error": "Новые пароли не совпадают"
        })
    
    # Проверяем длину пароля
    if len(new_password) < 6:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "admin_username": admin.username,
            "error": "Пароль должен содержать минимум 6 символов"
        })
    
    # Меняем пароль
    admin.set_password(new_password)
    db.commit()
    
    # Удаляем все сессии пользователя (принудительный выход)
    session_id = request.cookies.get("admin_session")
    if session_id in session_storage:
        del session_storage[session_id]
    
    # Перенаправляем на страницу входа с сообщением об успехе
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("admin_session")
    
    return response

@app.post("/admin/message/{message_id}/read")
async def mark_message_read(
    message_id: int, 
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin)
):
    message = db.query(models.ContactMessage).filter(models.ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.read = True
    db.commit()
    
    return {"status": "success"}

@app.delete("/admin/message/{message_id}/delete")
async def delete_message(
    message_id: int,
    db: Session = Depends(database.get_db),
    admin: models.AdminUser = Depends(get_current_admin)
):
    message = db.query(models.ContactMessage).filter(models.ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    
    return {"status": "success", "message": "Message deleted successfully"}

from fastapi.responses import FileResponse

@app.get("/googleddd09674c4d97235.html", include_in_schema=False)
async def google_verification():
    return FileResponse("googleddd09674c4d97235.html", media_type="text/html")

@app.get("/yandex_3d12f0d5421d9e74.html", include_in_schema=False)
async def yandex_verification():
    return FileResponse("yandex_3d12f0d5421d9e74.html", media_type="text/html")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    return FileResponse("sitemap.xml", media_type="application/xml")

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return FileResponse("robots.txt", media_type="text/plain")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Python Portfolio"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
