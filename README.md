Simple Messenger

📨 Небольшой, но функциональный мессенджер, написанный на FastAPI с поддержкой real-time общения.
Поддерживает регистрацию, авторизацию, создание чатов, мгновенную и отложенную отправку сообщений.

🚀 Функционал

🔐 Регистрация и авторизация пользователей

💬 Личные чаты

⚡ Real-time обмен сообщениями (через WebSocket)

⏰ Отложенная отправка сообщений (Celery + Redis)

🐘 Хранение данных в PostgreSQL

📦 Контейнеризация через Docker + docker-compose

🛠️ Технологии

Backend: FastAPI

База данных: PostgreSQL + SQLAlchemy + Alembic

Очереди и фоновые задачи: Celery + Redis

Frontend: HTML/CSS/JS 

Инфраструктура: Docker, docker-compose

⚙️ Установка и запуск
1. Клонируй репозиторий
git clone https://github.com/AnastasiaYuhimenko/simple_messanger.git
cd simple_messanger

2. Запуск через Docker
docker-compose up --build


После запуска приложение будет доступно по адресу:
👉 http://0.0.0.0:8000/users/ 

3. (Альтернативно) Локальный запуск
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

fastapi dev main.py

📂 Структура проекта
simple_messanger/
│── alembic/        
│── frontend/        
│── models/        
│── routers/      
│── schemas/        
│── services/       
│── celery_app.py   
│── websocket.py    
│── docker-compose.yml
│── Dockerfile
│── main.py           # точка входа
