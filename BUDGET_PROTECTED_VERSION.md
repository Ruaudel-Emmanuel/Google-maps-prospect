# 📦 BUDGET-PROTECTED VERSION – Files Summary

This is your **NEW complete version** with API budget tracking and protection.

---

## 🆕 New/Updated Files

### 1. **`usage_tracker.py`** (NEW - 300+ lines)

Independent module that:
- Tracks API requests & cost per month
- Stores data in SQLite database (`usage.db`)
- Enforces budget limits (default: 20,000 requests/$180/month)
- Provides real-time usage stats
- Generates alerts and logs

**What it does:**
```python
tracker = UsageTracker(
    max_requests_per_month=20000,
    max_cost_per_month=180.0,
    cost_per_request=0.009
)

# Check if request allowed
can_request, reason = tracker.can_make_request()

# Log successful request
tracker.log_request(endpoint="search_nearby", query_type="plumber")

# Get current usage
usage = tracker.get_current_usage()
# Returns: {requests: 50, cost: 0.45, percent_used: 0%, status: 'ok', ...}
```

### 2. **`app.py`** (COMPLETE REWRITE - 500+ lines)

Fully redesigned Flask app with:
- **Two-column layout:** Search form on left, results on right
- **Real-time usage dashboard:** Shows % used, remaining requests, cost
- **Budget protection:** Automatically blocks requests when limit reached
- **Friendly error messages:** Users know exactly why they can't search
- **Integration with tracker:** Every API call is logged
- **Responsive design:** Works on desktop, tablet, mobile
- **Better UX:** Progress bar, alerts, detailed stats

**New endpoints:**
- `GET /` – Main HTML interface
- `POST /api/scrape` – Search for leads (with budget check)
- `GET /api/usage` – Get current usage stats
- `GET /api/usage/history` – Get 12-month history
- `GET /api/usage/log` – Get detailed request log

**New HTML features:**
- Usage bar with color coding (green → yellow → orange → red)
- Real-time alerts ("Budget exceeded", "Warning", etc.)
- 4-stat dashboard: Requests used, Cost, % used, Remaining
- Better error handling for budget exceeded

### 3. **`.env.example`** (UPDATED)

Added budget tracking configuration:
```
MAX_REQUESTS_PER_MONTH=20000
MAX_COST_PER_MONTH=180.0
COST_PER_REQUEST=0.009
USAGE_DB_PATH=usage.db
```

Explains:
- How many requests = $200 free Google credit
- Why these defaults are conservative
- Different API pricing for different query types

### 4. **`GOOGLE_PLACES_API_SETUP.md`** (NEW - Complete guide)

Step-by-step guide to:
- Create Google Cloud project
- Enable Places API
- Get API Key
- Set up billing & alerts
- Replace mock data with real API
- Handle email extraction
- Pricing examples
- Troubleshooting

---

## 📊 How It Works

### Request Flow with Budget Protection

```
User clicks "Generate Leads"
    ↓
app.py: POST /api/scrape
    ↓
Check: Can we make request?
    ├─ tracker.can_make_request()
    ├─ Is budget exceeded? → YES: Return error message, stop
    └─ Is budget exceeded? → NO: Continue
    ↓
Call Google Places API (or use mock data)
    ↓
Log the request:
    └─ tracker.log_request(endpoint, query_type)
    ├─ Increment request counter
    ├─ Add cost to monthly total
    ├─ Record timestamp
    └─ Store in database
    ↓
Return leads to user
    ↓
User clicks "Export CSV"
    └─ Download happens
```

### Usage Dashboard Flow

```
Page loads
    ↓
JavaScript: fetch('/api/usage')
    ↓
Flask returns JSON with stats:
    {
        "requests": 45,
        "cost": 0.405,
        "requests_remaining": 19955,
        "cost_remaining": 179.595,
        "percent_used": 0,
        "status": "ok"
    }
    ↓
UI renders:
    ├─ Progress bar (0% filled, green)
    ├─ Alert: "✅ API usage normal"
    ├─ 4 stats: Requests / Cost / % / Remaining
    └─ Button enabled (can search)
```

### When Budget is Hit

```
User searches → 100% limit reached
    ↓
tracker.can_make_request() → returns False
    ↓
app.py returns error with message:
    "❌ API Budget Exceeded
     You've used 20,000 requests ($180)
     out of 20,000 allowed.
     Please wait until next month..."
    ↓
User sees error in UI
UI disables search button
Usage dashboard shows 🔴 CRITICAL
```

---

## 💾 Database Schema

SQLite database (`usage.db`) contains:

### Table: `monthly_usage`
```
id (int)           - Auto-increment ID
year (int)         - Calendar year (2026)
month (int)        - Calendar month (1-12)
requests (int)     - Total requests this month
cost (float)       - Total cost in USD
created_at (timestamp) - When record created
```

### Table: `request_log`
```
id (int)           - Auto-increment ID
timestamp (timestamp) - When request was made
endpoint (text)    - API endpoint (search_nearby, place_details)
query_type (text)  - Search type (plumber, restaurant, etc)
cost (float)       - Cost of this request
status (text)      - success | failed | blocked
notes (text)       - Additional info
```

---

## 🚀 How to Use

### 1. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env
cp .env.example .env
# (Don't add Google API key yet, use mock data first)

# Run
python app.py

# Open browser
http://127.0.0.1:5000

# Search for: "plumber" + "Rennes"
# Should see mock data + usage dashboard
```

### 2. Monitor Usage

- Usage stats update in real-time on dashboard
- Check database directly: `sqlite3 usage.db`
- View API logs via `/api/usage/log` endpoint
- Check history via `/api/usage/history` endpoint

### 3. Add Real Google API

Follow `GOOGLE_PLACES_API_SETUP.md` to:
1. Create Google Cloud project
2. Enable Places API
3. Get API Key
4. Add to `.env`: `GOOGLE_PLACES_API_KEY=AIzaSy...`
5. Replace `generate_mock_leads()` function with real API call
6. Test and deploy

### 4. Deploy

Same as before:
- Push to GitHub
- Connect to Render / Heroku
- Set `GOOGLE_PLACES_API_KEY` in environment
- Go live

---

## 📈 Budget Scenarios

### Scenario A: Small freelancer (50 queries/month)

```
Queries per month: 50
Results per query: 5
API calls: 50 + (50 × 5 × 1.004) ≈ 300 calls
Cost: ~$2-3/month
Progress: 0.15% of budget ✅ Comfortable
```

### Scenario B: Growing agency (200 queries/month)

```
Queries per month: 200
Results per query: 10
API calls: 200 + (200 × 10 × 1.004) ≈ 2,300 calls
Cost: ~$25/month
Progress: 14% of budget ✅ Still safe
```

### Scenario C: At maximum (monthly limit reached)

```
Requests: 20,000
Cost: $180
Status: Stopped (budget exceeded)
Message: "Budget exceeded, wait until next month"
```

**With $200 free credit from Google:**
- You can afford ~22,000 requests/month
- App limits to 20,000 to stay safely under
- Monthly reset on billing date (usually 1st)

---

## 🔐 Security Reminders

- API Key is in `.env` (never commit)
- Usage database stored locally (SQLite)
- All requests logged for audit trail
- Budget cannot be exceeded (hard limit in code)
- Error messages are safe (no API keys exposed)

---

## 📚 File Organization

```
google-maps-scraper/
├── app.py                           # Main Flask app (500+ lines)
├── usage_tracker.py                 # Budget tracker module (300+ lines)
├── requirements.txt                 # Dependencies
├── .env.example                     # Config template (updated)
├── GOOGLE_PLACES_API_SETUP.md      # How to set up real API
├── QUICK_START.md                   # Fast setup guide
├── DEPLOYMENT.md                    # Deploy to Render/Heroku
├── business_context.json            # Market data
├── README.md                        # Main documentation
├── PROJECT_STRUCTURE.md             # Project organization
├── COMPLETE_PROJECT_MANIFEST.md     # All files summary
├── .gitignore                       # Protect secrets
├── Procfile                         # Heroku config
├── render.yaml                      # Render config
└── usage.db                         # SQLite (git-ignored, auto-created)
```

---

## ✅ Checklist Before Deploy

- [ ] `usage_tracker.py` in project root
- [ ] `app.py` updated with new code
- [ ] `.env.example` has budget config
- [ ] `requirements.txt` includes `google-maps-services` (when ready)
- [ ] Run locally: `python app.py`
- [ ] Test search with mock data
- [ ] Check usage dashboard loads
- [ ] Try to exceed budget (optional test)
- [ ] Push to GitHub
- [ ] Deploy to Render/Heroku
- [ ] Test live version
- [ ] Share with first customers

---

## 🎯 Next Steps (In Order)

### This Week
1. Copy new `app.py` and `usage_tracker.py` to your repo
2. Run locally: `python app.py`
3. Test the UI and usage dashboard
4. Commit changes to GitHub

### Next Week
1. Follow `GOOGLE_PLACES_API_SETUP.md`
2. Get Google API key
3. Replace mock data with real API
4. Test with real queries
5. Deploy to Render

### Later
1. Add email enrichment (Hunter.io or RocketReach)
2. Build admin dashboard for budget management
3. Add user authentication (if SaaS)
4. Create tiered pricing plans

---

## 💡 Key Features Recap

| Feature | What It Does |
|---------|-------------|
| **Budget Tracking** | Counts requests and cost in real-time |
| **Automatic Blocking** | Stops API calls when limit reached |
| **Usage Dashboard** | Live stats visible to users |
| **Detailed Logging** | Every request recorded for audit |
| **Smart Alerts** | Notifies user when approaching limit |
| **SQLite Database** | Persistent, no external DB needed |
| **Google Places API Ready** | Drop-in replacement for mock data |
| **Responsive UI** | Works on any device |

---

**You're ready to go. Build it. Deploy it. Start protecting your budget.** 🚀

*Version 2.0: Budget-Protected Edition*  
*Created: January 15, 2026*
