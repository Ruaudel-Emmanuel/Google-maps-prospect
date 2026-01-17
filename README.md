# Google Maps Lead Scraper

A professional-grade web application for scraping business information from Google Maps with intelligent budget tracking and comprehensive error handling.

## 🎯 Overview

This Flask-based application allows you to search for businesses and leads in any city using the Google Places API. It features a dark-themed web interface, real-time budget monitoring, and flexible export options (CSV/JSON).

**Key Features:**
- 🎨 Beautiful dark-themed responsive HTML interface
- 💰 Monthly budget enforcement ($200 free credit limit)
- 📊 Real-time usage dashboard showing API costs
- 📍 City-based search (no GPS required)
- 📥 Export results to CSV & JSON formats
- 🔍 Intelligent error handling and logging
- 🛡️ GDPR-compliant data handling
- 🔐 Secure API key management via environment variables

## 📋 Prerequisites

- Python 3.7 or higher
- A Google Cloud account with Places API enabled
- Google Places API key
- Google Geocoding API key (optional, can use same as Places API)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd google-maps-lead-scraper
```

### 2. Create a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
Create a `.env` file in the root directory:
```
GOOGLE_PLACES_API_KEY=your_api_key_here
GEOCODING_API_KEY=your_geocoding_api_key_here
```

**Note:** If `GEOCODING_API_KEY` is not specified, it will default to `GOOGLE_PLACES_API_KEY`.

## 🏃 Running the Application

### Development Mode
```bash
python app.py
```

The application will start on `http://localhost:5000`

### Production Mode (with Gunicorn)
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

## 📖 Usage

### Web Interface

1. **Open your browser** to `http://localhost:5000`
2. **Enter search parameters:**
   - City name (e.g., "Paris", "New York", "Tokyo")
   - Business type (e.g., "restaurant", "hospital", "plumber")
   - Search radius in meters (default: 5000m)
3. **Click "Search"** to retrieve results
4. **View results** in the table with name, address, rating, and coordinates
5. **Export data** using the CSV or JSON buttons

### API Endpoints

#### Search Places
```
POST /api/search
Content-Type: application/json

{
  "city": "Paris",
  "business_type": "cafe",
  "radius": 5000
}
```

**Response:**
```json
{
  "city": "Paris, France",
  "results": [
    {
      "name": "Coffee Shop Name",
      "address": "123 Main Street",
      "lat": 48.8566,
      "lng": 2.3522,
      "rating": 4.5,
      "place_id": "ChIJD7fib..."
    }
  ],
  "usage": {
    "requests": 15,
    "cost": "$0.14",
    "budget_used": "0.1%"
  }
}
```

#### Get Usage Statistics
```
GET /api/usage
```

**Response:**
```json
{
  "requests_this_month": 15,
  "cost_this_month": 0.14,
  "max_requests": 20000,
  "max_cost": 180.0,
  "budget_used_percentage": 0.1,
  "cost_per_request": 0.009
}
```

## 💰 Budget Configuration

The application enforces monthly budgets to prevent unexpected charges:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_requests_per_month` | 20,000 | Maximum API requests allowed |
| `max_cost_per_month` | $180 | Maximum cost allowed |
| `cost_per_request` | $0.009 | Cost per API request |

To modify these limits, edit the `UsageTracker` class initialization in `app.py`:
```python
tracker = UsageTracker(
    max_requests_per_month=20000,
    max_cost_per_month=180.0,
    cost_per_request=0.009
)
```

## 📁 Project Structure

```
google-maps-lead-scraper/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── usage_log.json        # Monthly usage tracking (auto-generated)
└── README.md             # This file
```

## 🔧 Configuration

### Logging

The application uses Python's standard logging module with DEBUG level enabled. Logs include:
- API requests and responses
- Budget tracking
- Error details

Logs are printed to console and can be redirected to a file by modifying the logging configuration in `app.py`.

### Error Handling

The application handles multiple error scenarios:
- **API Key Missing:** Returns error code `API_KEY_MISSING`
- **City Not Found:** Returns error code `CITY_NOT_FOUND`
- **Budget Exceeded:** Returns error code `BUDGET_EXCEEDED`
- **Network Timeout:** Returns error code `TIMEOUT`
- **API Errors:** Returns appropriate Google Places API status

## 📊 Usage Tracking

Usage is automatically tracked in `usage_log.json`:
```json
{
  "month": "2026-01",
  "requests": 15,
  "cost": 0.135
}
```

The tracker automatically resets monthly based on the file's month key.

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **Rotate API keys regularly** - Update in Google Cloud Console
3. **Monitor API usage** - Check the `/api/usage` endpoint regularly
4. **Use environment variables** - Never hardcode sensitive data
5. **Limit API key scope** - Restrict to specific APIs in Google Cloud Console

## 🛠️ Troubleshooting

### "GOOGLE_PLACES_API_KEY not set in .env file!"
**Solution:** Create a `.env` file with your API key (see Configuration section)

### "Could not find city"
**Solution:** Verify city name spelling and ensure Geocoding API is enabled in Google Cloud Console

### "Budget exceeded this month"
**Solution:** Delete or reset `usage_log.json` or wait until the next calendar month

### "Request timeout"
**Solution:** Check internet connection and Google API service status

### Port already in use (Error: Address already in use)
**Solution:** Run on a different port:
```bash
python -c "from app import app; app.run(port=5001)"
```

## 📝 License

MIT License - See LICENSE file for details

## ✍️ Author

Reconversion Python Full Stack Developer  
Created: January 17, 2026

## 📞 Support & Contributions

For issues, bug reports, or feature requests, please open an issue on the repository.

## 🎓 Learning Resources

- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**Last Updated:** January 17, 2026  
**Version:** 1.0.0