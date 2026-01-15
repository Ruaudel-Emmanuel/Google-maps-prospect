# ⚡ QUICK START – 5 Minutes to Live App

## TL;DR – Copy/Paste These Commands

```bash
# 1. Clone and enter directory
cd google-maps-scraper

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py

# 5. Open in browser
# → http://127.0.0.1:5000/
```

Done. You're running.

---

## What You Get

A working web app with:

- ✅ Dark theme interface
- ✅ "Business Type" + "Location" search form
- ✅ Mock leads displayed (name, address, phone, website, rating)
- ✅ Export to CSV and JSON
- ✅ Before/After comparison showing business impact

---

## Replace Mock Data With Real Data

In `app.py`, find this function:

```python
def generate_mock_leads(query: str, location: str, count: int = 3) -> list:
    """Generate mock lead data for demonstration."""
```

Replace with real scraper (choose one):

### Option A: Google Places API

```python
from google.maps import places_sdk

def generate_mock_leads(query: str, location: str, count: int = 3) -> list:
    client = places_sdk.PlacesClient(api_key=os.getenv("GOOGLE_PLACES_API_KEY"))
    results = client.search_nearby(query=query, location=location, radius=50000)
    return [
        {
            "name": place.name,
            "address": place.formatted_address,
            "phone": place.phone_number,
            "website": place.website,
            "email": "N/A",
            "rating": place.rating,
            "review_count": place.review_count,
            "category": query
        }
        for place in results[:count]
    ]
```

### Option B: Selenium (More powerful)

```bash
pip install selenium webdriver-manager
```

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def generate_mock_leads(query: str, location: str, count: int = 3) -> list:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(f"https://maps.google.com/maps/search/{query}+{location}")
    
    # Wait for results to load
    time.sleep(3)
    
    # Find all business listings
    results = []
    elements = driver.find_elements(By.CLASS_NAME, "Nv2PK")[:count]
    
    for elem in elements:
        results.append({
            "name": elem.find_element(By.TAG_NAME, "h3").text,
            "address": "Address here",  # Extract from elem
            "phone": "Phone here",
            "website": "Website here",
            "email": "N/A",
            "rating": 4.5,  # Extract from elem
            "review_count": 100,
            "category": query
        })
    
    driver.quit()
    return results
```

### Option C: Third-party API (Easiest)

```bash
pip install requests
```

```python
def generate_mock_leads(query: str, location: str, count: int = 3) -> list:
    response = requests.post(
        "https://api.scrap.io/v1/search",
        headers={"Authorization": f"Bearer {os.getenv('SCRAP_IO_API_KEY')}"},
        json={"query": query, "location": location, "limit": count}
    )
    data = response.json()
    return data.get("leads", [])
```

---

## Deploy to the Internet (2 Minutes)

### Render (Easiest)

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/google-maps-scraper
git push -u origin main

# 2. Go to https://render.com
# 3. Click "New Web Service"
# 4. Select your GitHub repo
# 5. Set start command: gunicorn app:app
# 6. Click Deploy
# 7. Done! Your app is live at: https://google-maps-scraper.onrender.com
```

### Heroku

```bash
# 1. Install: https://devcenter.heroku.com/articles/heroku-cli
# 2. Login
heroku login

# 3. Create and deploy
heroku create google-maps-scraper
git push heroku main

# 4. Open app
heroku open
```

---

## Next Steps

1. **Add real scraper** – Replace mock data (see above)
2. **Test thoroughly** – Make sure export to CSV works
3. **Add your domain** – Point custom domain to app
4. **Sell it** – Use `business_context.json` to pitch clients
5. **Track usage** – Add logging, error monitoring
6. **Scale** – Add database, caching, CRM integrations

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 in use | `python app.py` → Change port in code |
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| Can't find .venv | Activate: `source .venv/bin/activate` |
| Deployed but app is blank | Check Render/Heroku logs |
| API returns 500 error | Check `.env` file and API keys |

---

## Anatomy of the App

```
User visits http://127.0.0.1:5000/
    ↓
Flask serves HTML (dark theme form)
    ↓
User types "plumber" + "Rennes"
    ↓
JavaScript sends POST to /api/scrape
    ↓
Backend calls generate_mock_leads() (or real scraper)
    ↓
Returns JSON with leads
    ↓
JavaScript renders results on page
    ↓
User clicks "Export CSV"
    ↓
Browser downloads file
```

That's the entire flow.

---

## Key Files to Know

| File | What It Does |
|------|-------------|
| `app.py` | Everything (routes + HTML + CSS + JS) |
| `business_context.json` | Market data for pitching |
| `requirements.txt` | Dependencies for pip |
| `.env.example` | Template for secrets |

---

## You're Ready

Go build. First version doesn't need to be perfect—it needs to work.

**Push to GitHub. Deploy to Render. Share the link. Sell it.**

---

*Made with ❤️ for Python developers transitioning to SaaS.* 🚀
