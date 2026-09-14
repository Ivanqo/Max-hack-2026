# MaxHack Backend

Django REST API backend for MaxHack platform.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login (get JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh access token
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PATCH /api/auth/profile/` - Update user profile
- `POST /api/auth/change-password/` - Change password

## Testing

Run tests with pytest:
```bash
pytest
```

## Project Structure

```
backend/
├── config/                 # Django project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI configuration
├── apps/                  # Django applications
│   └── accounts/         # User authentication app
│       ├── models.py     # Custom User model
│       ├── serializers.py # DRF serializers
│       ├── views.py      # API views
│       └── urls.py       # App URLs
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env.example         # Example environment variables
```
