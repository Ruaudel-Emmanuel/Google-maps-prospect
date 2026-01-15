# 📦 Project Structure – Google Maps Lead Scraper

```
google-maps-scraper/
│
├── 📄 README.md                  # Main documentation
├── 📄 DEPLOYMENT.md              # How to deploy to Render, Heroku, etc.
├── 📄 requirements.txt           # Python dependencies
├── 📄 Procfile                   # For Heroku deployment
├── 📄 render.yaml                # For Render deployment
├── 📄 app.py                     # Flask backend + HTML interface
├── 📄 business_context.json      # Reusable market data & strategy
│
├── 📄 .gitignore                 # Files to ignore in git
├── 📄 .env.example               # Example environment variables
│
├── 📁 docs/                      # Extended documentation
│   ├── ARCHITECTURE.md           # Technical architecture overview
│   ├── API_REFERENCE.md          # Detailed API docs
│   └── GDPR_COMPLIANCE.md        # Legal & compliance notes
│
├── 📁 tests/                     # Unit tests (optional)
│   ├── __init__.py
│   ├── test_api.py
│   └── test_scraper.py
│
├── 📁 config/                    # Configuration files
│   ├── __init__.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
│
├── 📁 scraper/                   # Scraping logic (future)
│   ├── __init__.py
│   ├── google_maps.py            # Google Maps scraper
│   ├── google_api.py             # Google Places API wrapper
│   ├── parser.py                 # Data parsing utilities
│   └── validators.py             # Input validation
│
├── 📁 models/                    # Database models (future)
│   ├── __init__.py
│   ├── lead.py
│   └── search.py
│
├── 📁 static/                    # Static assets (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── logo.png
│
├── 📁 templates/                 # HTML templates (future)
│   ├── base.html
│   ├── index.html
│   └── results.html
│
├── 📁 logs/                      # Application logs (git-ignored)
│   └── app.log
│
└── 📁 migrations/                # Database migrations (future)
    └── versions/
```

---

## 🗂️ File Descriptions

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Main documentation, quick start guide |
| `DEPLOYMENT.md` | Instructions for deploying to Render, Heroku, etc. |
| `requirements.txt` | Python dependencies (Flask, gunicorn, etc.) |
| `Procfile` | Heroku deployment config |
| `render.yaml` | Render.com deployment config |
| `app.py` | Main Flask app with all routes and HTML |
| `business_context.json` | Reusable market data, pricing, segments, strategy |
| `.gitignore` | Files to exclude from git repo |
| `.env.example` | Template for environment variables |

### `docs/` – Extended Documentation

As project grows, add detailed docs here:

- **ARCHITECTURE.md** – System design, API flow, database schema
- **API_REFERENCE.md** – Detailed API endpoint documentation
- **GDPR_COMPLIANCE.md** – Legal notes, data retention, privacy

### `tests/` – Unit Tests (Future)

```python
# tests/test_api.py
import pytest
from app import app

def test_api_scrape():
    client = app.test_client()
    response = client.post('/api/scrape', json={
        "query": "plumber",
        "location": "Rennes"
    })
    assert response.status_code == 200
    assert "leads" in response.json
```

### `config/` – Configuration

Separate environment-specific configs:

```python
# config/production.py
DEBUG = False
FLASK_ENV = 'production'

# config/development.py
DEBUG = True
FLASK_ENV = 'development'
```

Then in `app.py`:
```python
import os
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(f'config.{config_name}')
```

### `scraper/` – Scraping Logic

As you build real scrapers, organize them here:

```python
# scraper/google_maps.py
def scrape_google_maps(query, location):
    """Scrape real Google Maps data using Selenium or Playwright."""
    pass

# scraper/google_api.py
def search_places_api(query, location, api_key):
    """Use official Google Places API."""
    pass

# scraper/parser.py
def parse_lead(raw_data):
    """Convert raw data to standardized lead format."""
    pass
```

### `models/` – Database Models

When you add a database (SQLite, PostgreSQL):

```python
# models/lead.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    rating = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### `static/` & `templates/` – Frontend

When app grows beyond single `app.py`:

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>

<!-- templates/index.html -->
{% extends "base.html" %}
{% block content %}
    <h1>Search Leads</h1>
    <!-- form here -->
{% endblock %}
```

---

## 🚀 How to Start

### Day 1: MVP (what you have now)

```
google-maps-scraper/
├── app.py
├── business_context.json
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

✅ **Deploy this to Render or Heroku**

### Week 1: Add documentation & testing

```
+ docs/
  + ARCHITECTURE.md
  + GDPR_COMPLIANCE.md
+ tests/
  + test_api.py
+ DEPLOYMENT.md
```

### Week 2: Add real scraping

```
+ scraper/
  + google_maps.py
  + google_api.py
  + parser.py
  + validators.py
+ config/
  + development.py
  + production.py
```

### Week 3: Add database

```
+ models/
  + lead.py
  + search.py
+ migrations/
  + versions/
```

### Month 1+: Scale up

```
+ templates/  (separate HTML files)
+ static/     (separate CSS, JS)
+ api/        (modular routes)
+ auth/       (user authentication)
+ admin/      (dashboard)
```

---

## 📊 Git Workflow

### Initialize repo

```bash
git init
git add .
git commit -m "Initial commit: Google Maps Lead Scraper MVP"
git remote add origin https://github.com/YOUR_USERNAME/google-maps-scraper.git
git branch -M main
git push -u origin main
```

### After updates

```bash
git add .
git commit -m "Add real scraper with Selenium"
git push origin main
```

### Deploy to Render / Heroku

Just push to GitHub, and auto-deployment takes care of the rest.

---

## 🔑 Key Principles

1. **Start simple** – One file (`app.py`) is fine to begin
2. **Separate concerns** – Business logic, config, tests in different files
3. **Scale gradually** – Add folders only when needed
4. **Keep it clean** – Remove old code, use version control
5. **Document as you go** – Docs help future you and your clients

---

## ✅ Checklist Before First Commit

- [ ] All secrets in `.env.example` (no real keys in code)
- [ ] `requirements.txt` is up-to-date
- [ ] README has clear setup instructions
- [ ] Code follows PEP 8 style
- [ ] No TODO comments without context
- [ ] `.gitignore` includes `__pycache__/`, `.env`, `venv/`
- [ ] At least one test passes
- [ ] Deployment instructions clear

---

**Happy coding! Push to GitHub and deploy. Your first version is ready.** 🚀
