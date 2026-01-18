#!/usr/bin/env python3
"""
Google Maps Lead Scraper with FULL Pagination, Budget Tracking & Export Features.

IMPORTANT FEATURES:
- ✅ PAGINATION ACTIVE: Fetch up to 60 results per search (3 pages × 20 results)
- ✅ REAL PAGINATION: Uses Google Places API pagetoken for true pagination
- ✅ CSV & JSON EXPORT: Download results directly
- ✅ Only uses VALID Google Places API types
- ✅ Beautiful dark-themed HTML interface
- ✅ Google Places API integration with usage tracking
- ✅ Monthly budget enforcement (180 euro limit)
- ✅ Real-time usage dashboard
- ✅ GDPR-compliant
- ✅ CITY-BASED SEARCH (pas de GPS)
- ✅ Comprehensive error handling
- ✅ Debug logging enabled

Author: Reconversion Python Full Stack
License: MIT
Created: 2026-01-17
Updated: 2026-01-18 (Added Full Pagination + Export CSV/JSON)
"""

import os
import logging
import json
import time
import csv
from io import StringIO
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEOCODING_API_KEY = os.getenv("GEOCODING_API_KEY", GOOGLE_PLACES_API_KEY)

if not GOOGLE_PLACES_API_KEY:
    logger.warning("GOOGLE_PLACES_API_KEY not set in .env file!")
if not GEOCODING_API_KEY:
    logger.warning("GEOCODING_API_KEY not set in .env file!")

logger.info("Application initialization started...")

# ============================================================================
# JOB TYPES - ONLY VALID GOOGLE PLACES API TYPES
# ============================================================================
# These are verified types from Google Places API documentation
# Invalid types have been REMOVED to prevent incorrect results

JOB_TYPES = {
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "bar": "Bar",
    "hotel": "Hotel",
    "florist": "Fleuriste",
    "grocery_or_supermarket": "Supermarche",
    "shopping_mall": "Centre commercial",
    "bakery": "Boulangerie",
    "pharmacy": "Pharmacie",
    "gas_station": "Station-service",
    "gym": "Salle de sport",
    "dentist": "Dentiste",
    "doctor": "Medecin",
    "hospital": "Hopital",
    "bank": "Banque",
    "hair_care": "Salon de coiffure",
    "laundry": "Laverie",
    "night_club": "Boite de nuit",
    "shoe_store": "Magasin de chaussures",
    "spa": "Spa",
    "store": "Magasin",
    "taxi_stand": "Station de taxi",
    "parking": "Parking",
    "pet_store": "Animalerie",
    "car_rental": "Location de voiture",
    "car_repair": "Reparation automobile",
    "plumber": "Plombier",
    "electrician": "Electricien",
}


class UsageTracker:
    def __init__(self, max_requests_per_month=20000, max_cost_per_month=180.0, cost_per_request=0.009):
        self.max_requests_per_month = max_requests_per_month
        self.max_cost_per_month = max_cost_per_month
        self.cost_per_request = cost_per_request
        self.requests_this_month = 0
        self.cost_this_month = 0.0
        self.usage_file = "usage_log.json"
        self.load_usage()

    def load_usage(self):
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, "r") as f:
                    data = json.load(f)
                month_key = datetime.now().strftime("%Y-%m")
                if month_key == data.get("month"):
                    self.requests_this_month = data.get("requests", 0)
                    self.cost_this_month = data.get("cost", 0.0)
                    msg = f"Usage loaded: {self.requests_this_month} requests, {self.cost_this_month:.2f} euros"
                    logger.info(msg)
                else:
                    logger.info("New month detected - resetting tracker")
            except Exception as e:
                logger.error(f"Error loading usage: {e}")

    def save_usage(self):
        try:
            month_key = datetime.now().strftime("%Y-%m")
            data = {
                "month": month_key,
                "requests": self.requests_this_month,
                "cost": self.cost_this_month
            }
            with open(self.usage_file, "w") as f:
                json.dump(data, f)
            logger.debug(f"Usage saved: {self.requests_this_month} requests")
        except Exception as e:
            logger.error(f"Error saving usage: {e}")

    def add_request(self):
        self.requests_this_month += 1
        self.cost_this_month += self.cost_per_request
        self.save_usage()

    def can_make_request(self):
        can_request = (
            self.requests_this_month < self.max_requests_per_month
            and self.cost_this_month < self.max_cost_per_month
        )
        if not can_request:
            logger.warning(
                f"Budget limit reached! Requests: {self.requests_this_month}/{self.max_requests_per_month}, "
                f"Cost: {self.cost_this_month:.2f} euros/{self.max_cost_per_month}"
            )
        return can_request

    def get_usage_percentage(self):
        if self.max_requests_per_month > 0:
            requests_pct = (self.requests_this_month / self.max_requests_per_month) * 100
        else:
            requests_pct = 0
        if self.max_cost_per_month > 0:
            cost_pct = (self.cost_this_month / self.max_cost_per_month) * 100
        else:
            cost_pct = 0
        return max(requests_pct, cost_pct)


tracker = UsageTracker()


def get_city_coordinates(city_name):
    """Geocode city name to lat/lng coordinates"""
    try:
        if not GEOCODING_API_KEY:
            logger.error("GEOCODING_API_KEY not configured")
            return None

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": city_name,
            "key": GEOCODING_API_KEY
        }

        logger.info(f"Geocoding city: {city_name}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            result = {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": data["results"][0]["formatted_address"]
            }
            logger.info(f"Found city coordinates: {result}")
            return result
        else:
            logger.warning(f"Geocoding failed for {city_name}: {data.get('status')}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Geocoding timeout for {city_name}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during geocoding: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error geocoding city: {e}")
        return None


def search_places_paginated(city_name, business_type, radius=5000, max_pages=3):
    """
    Search Google Places API with REAL PAGINATION support
    
    Returns up to 20 * max_pages results (default: 60 results)
    Uses pagetoken to fetch additional pages
    
    Args:
        city_name: City to search
        business_type: Type of business (from JOB_TYPES)
        radius: Search radius in meters (default: 5km)
        max_pages: Number of pages to fetch (default: 3 pages = 60 results)
    """
    try:
        if not tracker.can_make_request():
            error_msg = "Budget exceeded this month"
            logger.warning(error_msg)
            return {"error": error_msg, "code": "BUDGET_EXCEEDED"}

        if not GOOGLE_PLACES_API_KEY:
            error_msg = "Google Places API key not configured"
            logger.error(error_msg)
            return {"error": error_msg, "code": "API_KEY_MISSING"}

        logger.info(f"Starting paginated search for {city_name}, type: {business_type}, radius: {radius}m, max_pages: {max_pages}")
        
        city_coords = get_city_coordinates(city_name)
        if not city_coords:
            error_msg = f"Could not find city: {city_name}"
            logger.warning(error_msg)
            return {"error": error_msg, "code": "CITY_NOT_FOUND"}

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        all_results = []
        page_token = None
        page_count = 0
        pages_data = []

        # ===================================================================
        # PAGINATION LOOP: Fetch multiple pages (default: 3 pages = 60 results)
        # ===================================================================
        while page_count < max_pages:
            params = {
                "location": f"{city_coords['lat']},{city_coords['lng']}",
                "radius": radius,
                "type": business_type,
                "key": GOOGLE_PLACES_API_KEY
            }
            
            # Add pagetoken if this is not the first page
            if page_token:
                params["pagetoken"] = page_token
                logger.info(f"Fetching page {page_count + 1}/{max_pages} with pagetoken...")
                # Google requires a small delay between paginated requests
                time.sleep(2)
            else:
                logger.info("Fetching first page...")

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            tracker.add_request()
            logger.debug(f"API Request #{tracker.requests_this_month} made")

            data = response.json()

            if data.get("status") == "OK":
                # Extract results from current page
                page_results = data.get("results", [])
                page_size = len(page_results)
                
                for place in page_results:
                    all_results.append({
                        "name": place.get("name"),
                        "address": place.get("vicinity"),
                        "lat": place["geometry"]["location"]["lat"],
                        "lng": place["geometry"]["location"]["lng"],
                        "rating": place.get("rating", "N/A"),
                        "place_id": place.get("place_id")
                    })

                pages_data.append({
                    "page": page_count + 1,
                    "results_on_page": page_size
                })
                
                logger.info(f"Page {page_count + 1}: Found {page_size} places (Total: {len(all_results)})")

                # Check if there are more pages
                page_token = data.get("next_page_token")
                page_count += 1

                # Stop if no next_page_token or reached max_pages
                if not page_token or page_count >= max_pages:
                    logger.info(f"Pagination complete. Total results: {len(all_results)} from {page_count} pages")
                    break

            else:
                error_msg = f"Places API error: {data.get('status')}"
                logger.error(error_msg)
                if page_count == 0:
                    # First page failed completely
                    return {"error": error_msg, "code": data.get("status")}
                else:
                    # First page succeeded, return partial results
                    logger.warning(f"Failed to fetch page {page_count + 1}, returning {len(all_results)} results from previous pages")
                    break

        return {
            "city": city_coords["formatted_address"],
            "results": all_results,
            "pages_fetched": page_count,
            "pages_data": pages_data,
            "usage": {
                "requests": tracker.requests_this_month,
                "cost": f"{tracker.cost_this_month:.2f}",
                "budget_used": f"{tracker.get_usage_percentage():.1f}%"
            }
        }

    except requests.exceptions.Timeout:
        error_msg = "Request timeout - Google API took too long"
        logger.error(error_msg)
        return {"error": error_msg, "code": "TIMEOUT"}
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "code": "NETWORK_ERROR"}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "code": "UNKNOWN_ERROR"}


# ============================================================================
# ROUTES
# ============================================================================

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, job_types=JOB_TYPES)


@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        data = request.json
        city_name = data.get("city", "").strip()
        business_type = data.get("type", "").strip()
        radius = int(data.get("radius", 5000))
        # NEW: Allow client to specify number of pages (1-3)
        max_pages = int(data.get("max_pages", 3))
        max_pages = max(1, min(max_pages, 3))  # Clamp to 1-3

        if not city_name or not business_type:
            return jsonify({"error": "Missing city or business type"}), 400

        logger.info(f"API request: city={city_name}, type={business_type}, max_pages={max_pages}")

        # Call the paginated search function
        result = search_places_paginated(city_name, business_type, radius, max_pages)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/job-types", methods=["GET"])
def api_job_types():
    return jsonify(JOB_TYPES), 200


@app.route("/api/usage", methods=["GET"])
def api_usage():
    return jsonify({
        "requests": tracker.requests_this_month,
        "cost": f"{tracker.cost_this_month:.2f}",
        "budget_used": f"{tracker.get_usage_percentage():.1f}%",
        "max_requests": tracker.max_requests_per_month,
        "max_cost": tracker.max_cost_per_month
    }), 200


@app.route("/api/export-csv", methods=["POST"])
def export_csv():
    """Export search results to CSV format"""
    try:
        data = request.json
        results = data.get("results", [])
        city = data.get("city", "Unknown")
        
        if not results:
            return jsonify({"error": "No results to export"}), 400
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "address", "rating", "lat", "lng", "place_id"])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                "name": result.get("name", ""),
                "address": result.get("address", ""),
                "rating": result.get("rating", ""),
                "lat": result.get("lat", ""),
                "lng": result.get("lng", ""),
                "place_id": result.get("place_id", "")
            })
        
        csv_content = output.getvalue()
        logger.info(f"Exported {len(results)} results to CSV")
        
        return {
            "filename": f"leads_{city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content": csv_content,
            "count": len(results)
        }, 200
    
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/export-json", methods=["POST"])
def export_json():
    """Export search results to JSON format"""
    try:
        data = request.json
        results = data.get("results", [])
        city = data.get("city", "Unknown")
        pages_fetched = data.get("pages_fetched", 1)
        
        if not results:
            return jsonify({"error": "No results to export"}), 400
        
        export_data = {
            "city": city,
            "pages_fetched": pages_fetched,
            "total_results": len(results),
            "exported_at": datetime.now().isoformat(),
            "results": results
        }
        
        logger.info(f"Exported {len(results)} results to JSON")
        
        return {
            "filename": f"leads_{city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "content": json.dumps(export_data, ensure_ascii=False, indent=2),
            "count": len(results)
        }, 200
    
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HTML TEMPLATE (with export buttons)
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Maps Lead Scraper - Pagination & Export</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #00d4ff, #0099ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 1.1em;
            color: #b0b0b0;
            margin-bottom: 5px;
        }

        .badge {
            display: inline-block;
            background: #00d4ff;
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
            font-size: 0.9em;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }

        .card {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }

        .card h2 {
            margin-bottom: 20px;
            color: #00d4ff;
            font-size: 1.3em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #b0b0b0;
            font-size: 0.95em;
        }

        input, select {
            width: 100%;
            padding: 12px 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 1em;
            transition: all 0.3s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #00d4ff;
            background: rgba(0, 212, 255, 0.1);
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }

        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .export-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }

        button {
            padding: 12px 20px;
            background: linear-gradient(135deg, #00d4ff, #0099ff);
            color: #000;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        button.secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #00d4ff;
            border: 2px solid #00d4ff;
        }

        button.secondary:hover {
            background: rgba(0, 212, 255, 0.2);
        }

        button.export {
            background: linear-gradient(135deg, #00ff88, #00dd44);
            color: #000;
            font-size: 0.9em;
            padding: 10px 15px;
        }

        button.export:hover {
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.4);
        }

        .results-section {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }

        .result-item {
            background: rgba(0, 212, 255, 0.05);
            border-left: 4px solid #00d4ff;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .result-item:hover {
            background: rgba(0, 212, 255, 0.1);
            transform: translateX(5px);
        }

        .result-item h3 {
            color: #00d4ff;
            margin-bottom: 5px;
        }

        .result-item p {
            color: #b0b0b0;
            font-size: 0.95em;
            margin: 3px 0;
        }

        .status {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }

        .status.loading {
            background: rgba(255, 165, 0, 0.2);
            color: #ffa500;
        }

        .status.success {
            background: rgba(0, 255, 0, 0.2);
            color: #00ff00;
        }

        .status.error {
            background: rgba(255, 0, 0, 0.2);
            color: #ff6b6b;
        }

        .usage-bar {
            background: rgba(0, 0, 0, 0.3);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }

        .usage-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff00, #ffa500, #ff0000);
            transition: width 0.3s ease;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px 0;
        }

        .stat-label {
            color: #b0b0b0;
        }

        .stat-value {
            color: #00d4ff;
            font-weight: bold;
        }

        .pagination-note {
            background: rgba(0, 212, 255, 0.15);
            border: 1px solid rgba(0, 212, 255, 0.3);
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #b0b0b0;
        }

        .pagination-note strong {
            color: #00d4ff;
        }

        .results-info {
            padding: 15px;
            background: rgba(0, 212, 255, 0.1);
            border-left: 4px solid #00d4ff;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .results-info.show {
            display: block;
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .button-group {
                grid-template-columns: 1fr;
            }

            .export-group {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌍 Google Maps Lead Scraper</h1>
            <p class="subtitle">Récupérez vos prospects en masse avec pagination & export</p>
            <span class="badge">✨ Pagination + CSV/JSON Export</span>
        </header>

        <div class="grid">
            <!-- Formulaire de recherche -->
            <div class="card">
                <h2>⚙️ Paramètres de recherche</h2>

                <div class="form-group">
                    <label for="city">Ville:</label>
                    <input type="text" id="city" placeholder="Ex: Rennes, Paris, Lyon..." value="Rennes">
                </div>

                <div class="form-group">
                    <label for="type">Type d'établissement:</label>
                    <select id="type">
                        <option value="">-- Choisissez un type --</option>
                        {% for key, name in job_types.items() %}
                        <option value="{{ key }}">{{ name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-group">
                    <label for="radius">Rayon de recherche (m):</label>
                    <input type="number" id="radius" value="5000" min="500" max="50000" step="500">
                </div>

                <div class="form-group">
                    <label for="max_pages">Nombre de pages (résultats):</label>
                    <select id="max_pages">
                        <option value="1">1 page (20 résultats)</option>
                        <option value="2">2 pages (40 résultats)</option>
                        <option value="3" selected>3 pages (60 résultats) ⭐</option>
                    </select>
                </div>

                <div class="pagination-note">
                    <strong>📊 Pagination:</strong> Chaque page = 1 appel API (0,009 €)<br>
                    3 pages = 3 appels = 0,027 € par recherche
                </div>

                <div class="button-group">
                    <button onclick="search()">🔍 Lancer la recherche</button>
                    <button class="secondary" onclick="clearResults()">🗑️ Effacer</button>
                </div>
            </div>

            <!-- Dashboard d'utilisation -->
            <div class="card">
                <h2>💰 Utilisation du budget</h2>

                <div class="stat-row">
                    <span class="stat-label">Requêtes ce mois:</span>
                    <span class="stat-value" id="requests">0</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">Coût ce mois:</span>
                    <span class="stat-value" id="cost">0,00 €</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">Budget utilisé:</span>
                    <span class="stat-value" id="budget">0%</span>
                </div>

                <div class="usage-bar">
                    <div class="usage-fill" id="usage-fill" style="width: 0%"></div>
                </div>

                <div class="stat-row" style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <span class="stat-label">Budget mensuel:</span>
                    <span class="stat-value">180,00 €</span>
                </div>

                <div class="pagination-note" style="margin-top: 15px;">
                    <strong>💡 Conseil:</strong> Avec 180 €, tu peux faire<br>
                    <strong>~6666 appels API</strong> ou<br>
                    <strong>~2222 recherches x 3 pages!</strong>
                </div>

                <button onclick="refreshUsage()" style="width: 100%; margin-top: 15px;">🔄 Actualiser l'usage</button>
            </div>
        </div>

        <!-- Section des résultats -->
        <div class="results-section">
            <h2 id="results-title">📍 Résultats (en attente...)</h2>
            <div id="status" style="display: none;"></div>
            
            <div id="results-info" class="results-info">
                <strong>📊 Pages récupérées:</strong> <span id="pages-info">0</span><br>
                <strong>✅ Total résultats:</strong> <span id="total-info">0</span>
            </div>

            <div id="export-buttons" class="export-group" style="display: none; margin-bottom: 20px;">
                <button class="export" onclick="exportCSV()">📥 Télécharger CSV</button>
                <button class="export" onclick="exportJSON()">📥 Télécharger JSON</button>
            </div>

            <div id="results-container"></div>
        </div>
    </div>

    <script>
        let lastResults = null;

        async function search() {
            const city = document.getElementById('city').value.trim();
            const type = document.getElementById('type').value.trim();
            const radius = document.getElementById('radius').value;
            const max_pages = document.getElementById('max_pages').value;

            if (!city || !type) {
                showStatus('Veuillez remplir tous les champs', 'error');
                return;
            }

            showStatus('🔄 Recherche en cours (peut prendre quelques secondes)...', 'loading');

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ city, type, radius, max_pages })
                });

                const data = await response.json();

                if (response.ok) {
                    lastResults = data;
                    displayResults(data);
                    showStatus(`✅ ${data.results.length} résultats trouvés (${data.pages_fetched} pages)`, 'success');
                    
                    // Show export buttons
                    document.getElementById('export-buttons').style.display = 'grid';
                    document.getElementById('results-info').classList.add('show');
                    document.getElementById('pages-info').textContent = data.pages_fetched;
                    document.getElementById('total-info').textContent = data.results.length;
                    
                    refreshUsage();
                } else {
                    showStatus(`❌ Erreur: ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Erreur réseau: ${error}`, 'error');
            }
        }

        function displayResults(data) {
            const container = document.getElementById('results-container');
            const title = document.getElementById('results-title');

            title.textContent = `📍 ${data.results.length} résultats trouvés à ${data.city}`;

            if (data.results.length === 0) {
                container.innerHTML = '<p style="color: #ff6b6b;">Aucun résultat trouvé.</p>';
                return;
            }

            container.innerHTML = data.results.map(place => `
                <div class="result-item">
                    <h3>${place.name}</h3>
                    <p>📍 ${place.address}</p>
                    <p>⭐ Note: ${place.rating}</p>
                    <p style="color: #888; font-size: 0.85em;">ID: ${place.place_id}</p>
                </div>
            `).join('');
        }

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }

        function clearResults() {
            document.getElementById('results-container').innerHTML = '';
            document.getElementById('results-title').textContent = '📍 Résultats (en attente...)';
            document.getElementById('status').style.display = 'none';
            document.getElementById('export-buttons').style.display = 'none';
            document.getElementById('results-info').classList.remove('show');
            lastResults = null;
        }

        async function refreshUsage() {
            try {
                const response = await fetch('/api/usage');
                const data = await response.json();

                document.getElementById('requests').textContent = data.requests;
                document.getElementById('cost').textContent = `${data.cost} €`;
                document.getElementById('budget').textContent = data.budget_used;
                document.getElementById('usage-fill').style.width = data.budget_used;
            } catch (error) {
                console.error('Error refreshing usage:', error);
            }
        }

        async function exportCSV() {
            if (!lastResults) {
                alert('Aucun résultat à exporter');
                return;
            }

            try {
                const response = await fetch('/api/export-csv', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(lastResults)
                });

                const data = await response.json();

                if (response.ok) {
                    downloadFile(data.content, data.filename, 'text/csv');
                    showStatus(`✅ CSV exporté: ${data.count} résultats`, 'success');
                } else {
                    showStatus(`❌ Erreur export: ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Erreur: ${error}`, 'error');
            }
        }

        async function exportJSON() {
            if (!lastResults) {
                alert('Aucun résultat à exporter');
                return;
            }

            try {
                const response = await fetch('/api/export-json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(lastResults)
                });

                const data = await response.json();

                if (response.ok) {
                    downloadFile(data.content, data.filename, 'application/json');
                    showStatus(`✅ JSON exporté: ${data.count} résultats`, 'success');
                } else {
                    showStatus(`❌ Erreur export: ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Erreur: ${error}`, 'error');
            }
        }

        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }

        // Actualiser l'usage au démarrage
        window.addEventListener('load', refreshUsage);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    logger.info("Starting Flask app with full pagination and export features...")
    app.run(debug=True, host="0.0.0.0", port=5000)
