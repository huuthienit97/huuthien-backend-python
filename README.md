# Django Backend Project

## Cấu trúc dự án

```
huuthien-be-python/
├── apps/                   # Thư mục chứa các ứng dụng Django
│   └── core/              # Ứng dụng core
├── config/                # Cấu hình Django project
│   ├── settings.py       # Cài đặt dự án
│   ├── urls.py          # URL routing chính
│   ├── asgi.py         # ASGI config
│   └── wsgi.py         # WSGI config
├── static/               # File tĩnh (CSS, JavaScript, Images)
├── templates/            # Template HTML
├── utils/                # Tiện ích và helper functions
├── manage.py            # Command-line utility cho Django
├── requirements.txt     # Dependencies
└── .env                # Biến môi trường (không được commit)
```

## Cài đặt

1. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
.\venv\Scripts\activate  # Windows
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file .env từ .env.example và cập nhật các biến môi trường

4. Chạy migrations:
```bash
python manage.py migrate
```

5. Khởi chạy server:
```bash
python manage.py runserver
```

## Công nghệ sử dụng

- Django 5.1.4
- Django REST Framework
- Django Channels
- PostgreSQL
- CORS Headers

## Phát triển

1. Tạo ứng dụng mới:
```bash
python manage.py startapp <app_name> apps/<app_name>
```

2. Thêm ứng dụng vào INSTALLED_APPS trong config/settings.py:
```python
INSTALLED_APPS = [
    ...
    'apps.<app_name>',
]
```# huuthien-backend-python
