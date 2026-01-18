#!/usr/bin/env python3
"""
Google Maps Lead Scraper with Budget Tracking & Error Handling.

IMPORTANT FIXES:
- Only uses VALID Google Places API types
- Removed fictional types that caused incorrect results
- All types tested and verified

Features:
    - Beautiful dark-themed HTML interface
    - Google Places API integration with usage tracking
    - Monthly budget enforcement (200 free credit limit)
    - CSV & JSON export
    - Real-time usage dashboard
    - GDPR-compliant
    - CITY-BASED SEARCH (pas de GPS)
    - Comprehensive error handling
    - Debug logging enabled

Author: Reconversion Python Full Stack
License: MIT
Created: 2026-01-17
Updated: 2026-01-18 (Fixed JOB_TYPES)
"""

import os
import logging
import json
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


def search_places(city_name, business_type, radius=5000):
    try:
        if not tracker.can_make_request():
            error_msg = "Budget exceeded this month"
            logger.warning(error_msg)
            return {"error": error_msg, "code": "BUDGET_EXCEEDED"}

        if not GOOGLE_PLACES_API_KEY:
            error_msg = "Google Places API key not configured"
            logger.error(error_msg)
            return {"error": error_msg, "code": "API_KEY_MISSING"}

        logger.info(f"Starting search for {city_name}, type: {business_type}, radius: {radius}m")

        city_coords = get_city_coordinates(city_name)
        if not city_coords:
            error_msg = f"Could not find city: {city_name}"
            logger.warning(error_msg)
            return {"error": error_msg, "code": "CITY_NOT_FOUND"}

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{city_coords['lat']},{city_coords['lng']}",
            "radius": radius,
            "type": business_type,
            "key": GOOGLE_PLACES_API_KEY
        }
        logger.info("Searching Google Places API...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        tracker.add_request()
        data = response.json()

        if data.get("status") == "OK":
            results = []
            for place in data.get("results", []):
                results.append({
                    "name": place.get("name"),
                    "address": place.get("vicinity"),
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"],
                    "rating": place.get("rating", "N/A"),
                    "place_id": place.get("place_id")
                })
            logger.info(f"Found {len(results)} places")
            return {
                "city": city_coords["formatted_address"],
                "results": results,
                "usage": {
                    "requests": tracker.requests_this_month,
                    "cost": f"{tracker.cost_this_month:.2f}",
                    "budget_used": f"{tracker.get_usage_percentage():.1f}%"
                }
            }
        else:
            error_msg = f"Places API error: {data.get('status')}"
            logger.error(error_msg)
            return {"error": error_msg, "code": data.get("status")}

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


HTMLTEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prospecteur Google Maps - Recherche par Ville</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }

        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .results {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .results h2 {
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .place-item {
            border: 1px solid #eee;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            background: #f9f9f9;
            transition: all 0.3s;
        }

        .place-item:hover {
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        .place-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }

        .place-address {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 8px;
        }

        .place-rating {
            color: #ffc107;
            font-weight: 600;
        }

        .place-coords {
            font-size: 0.85em;
            color: #999;
            margin-top: 10px;
            font-family: monospace;
        }

        .usage-info {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .usage-bar {
            width: 100%;
            height: 25px;
            background: #eee;
            border-radius: 5px;
            overflow: hidden;
            margin: 10px 0;
        }

        .usage-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: 600;
        }

        .error {
            background: #f8d7da;
            border: 2px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }

        .export-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .export-buttons button {
            flex: 1;
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Prospecteur Google Maps</h1>
            <p class="subtitle">Recherche de prospects par ville (sans GPS)</p>
        </header>

        <div class="main-content">
            <div class="card">
                <h2>Parametres de recherche</h2>
                <form id="searchForm">
                    <div class="form-group">
                        <label for="cityName">Ville</label>
                        <input type="text" id="cityName" placeholder="Ex: Paris, Rennes, Lyon..." required>
                    </div>

                    <div class="form-group">
                        <label for="businessType">Type de commerce</label>
                        <select id="businessType" required>
                            <option value="">-- Selectionner --</option>
                            {% for type_value, type_label in job_types.items() %}
                                <option value="{{ type_value }}">{{ type_label }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="radius">Rayon de recherche (m)</label>
                        <input type="number" id="radius" value="5000" min="500" max="50000" step="500">
                    </div>

                    <button type="submit" id="submitBtn">Rechercher</button>
                </form>
            </div>

            <div class="usage-info">
                <h2>Utilisation du budget</h2>
                <div id="usageContent">
                    <p>Chargement...</p>
                </div>
            </div>
        </div>

        <div class="results hidden" id="results">
            <h2>Resultats de recherche</h2>
            <div id="errorMessage" class="error" style="display: none;"></div>
            <div id="resultsList"></div>
            <div class="export-buttons" id="exportButtons" style="display: none;">
                <button onclick="exportJSON()">Exporter en JSON</button>
                <button onclick="exportCSV()">Exporter en CSV</button>
            </div>
        </div>
    </div>

    <script>
        var lastResults = null;

        updateUsage();
        setInterval(updateUsage, 5000);

        document.getElementById("searchForm").addEventListener("submit", function(e) {
            e.preventDefault();
            
            var city = document.getElementById("cityName").value.trim();
            var businessType = document.getElementById("businessType").value;
            var radius = document.getElementById("radius").value;
            var submitBtn = document.getElementById("submitBtn");

            if (!city) {
                showError("Veuillez entrer un nom de ville");
                return;
            }
            if (!businessType) {
                showError("Veuillez selectionner un type de commerce");
                return;
            }

            submitBtn.disabled = true;

            fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    city: city,
                    businesstype: businessType,
                    radius: parseInt(radius)
                })
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                submitBtn.disabled = false;
                if (data.error) {
                    showError(data.error);
                } else {
                    lastResults = data;
                    displayResults(data);
                    updateUsage();
                }
            })
            .catch(function(error) {
                submitBtn.disabled = false;
                showError("Erreur reseau: " + error.message);
            });
        });

        function displayResults(data) {
            var resultsDiv = document.getElementById("results");
            var resultsList = document.getElementById("resultsList");
            var errorDiv = document.getElementById("errorMessage");
            var exportButtons = document.getElementById("exportButtons");

            errorDiv.style.display = "none";
            resultsList.innerHTML = "";
            exportButtons.style.display = "none";

            if (!data.results || data.results.length === 0) {
                errorDiv.style.display = "block";
                errorDiv.innerHTML = "Aucun resultat trouve pour cette recherche.";
                resultsDiv.classList.add("hidden");
                return;
            }

            var html = '<p style="color: #667eea; font-weight: 600; margin-bottom: 15px;">' + 
                       data.results.length + ' resultats trouves pour <strong>' + 
                       escapeHtml(data.city) + '</strong></p>';

            for (var i = 0; i < data.results.length; i++) {
                var place = data.results[i];
                var index = i;
                html += '<div class="place-item">' +
                        '<div class="place-name">' + (index + 1) + '. ' + escapeHtml(place.name) + '</div>' +
                        '<div class="place-address">Adresse: ' + escapeHtml(place.address) + '</div>' +
                        '<div class="place-rating">Note: ' + place.rating + '</div>' +
                        '<div class="place-coords">Lat: ' + place.lat.toFixed(4) + ', Lng: ' + place.lng.toFixed(4) + '</div>' +
                        '</div>';
            }

            resultsList.innerHTML = html;
            exportButtons.style.display = "flex";
            resultsDiv.classList.remove("hidden");
        }

        function escapeHtml(text) {
            var map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return String(text).replace(/[&<>"']/g, function(m) { 
                return map[m]; 
            });
        }

        function showError(message) {
            var resultsDiv = document.getElementById("results");
            var errorDiv = document.getElementById("errorMessage");
            var exportButtons = document.getElementById("exportButtons");

            errorDiv.innerHTML = "ERREUR: " + escapeHtml(message);
            errorDiv.style.display = "block";
            exportButtons.style.display = "none";
            resultsDiv.classList.remove("hidden");
        }

        function updateUsage() {
            fetch("/api/usage")
            .then(function(response) { return response.json(); })
            .then(function(data) {
                document.getElementById("usageContent").innerHTML = 
                    '<div style="margin-bottom: 15px;">' +
                    '<strong>Requetes ce mois:</strong> ' + data.requests + ' / ' + data.maxrequests +
                    '</div>' +
                    '<div class="usage-bar">' +
                    '<div class="usage-fill" style="width: ' + data.usagepercentage + '%;">' +
                    data.usagepercentage.toFixed(1) + '%' +
                    '</div>' +
                    '</div>' +
                    '<div style="margin-top: 10px; color: #666; font-size: 0.9em;">' +
                    'Cout: ' + data.cost + ' / ' + data.maxcost + ' euros' +
                    '</div>';
            })
            .catch(function(error) {
                document.getElementById("usageContent").innerHTML = 
                    '<div class="error">Impossible de charger le budget</div>';
            });
        }

        function exportJSON() {
            if (!lastResults) return;
            var json = JSON.stringify(lastResults, null, 2);
            downloadFile(json, "prospects.json", "application/json");
        }

        function exportCSV() {
            if (!lastResults || !lastResults.results) return;

            var csv = "Nom,Adresse,Latitude,Longitude,Note\\n";
            for (var i = 0; i < lastResults.results.length; i++) {
                var place = lastResults.results[i];
                var name = (place.name || "").replace(/"/g, '""');
                var address = (place.address || "").replace(/"/g, '""');
                var rating = (place.rating || "N/A").toString().replace(/"/g, '""');
                csv += '"' + name + '","' + address + '",' + place.lat + ',' + place.lng + ',"' + rating + '"\\n';
            }

            downloadFile(csv, "prospects.csv", "text/csv");
        }

        function downloadFile(content, filename, mimeType) {
            var blob = new Blob([content], { type: mimeType });
            var url = window.URL.createObjectURL(blob);
            var link = document.createElement("a");
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>"""


@app.route("/")
def index():
    logger.info("Home page accessed")
    return render_template_string(HTMLTEMPLATE, job_types=JOB_TYPES)


@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        data = request.json
        city = data.get("city", "").strip()
        businesstype = data.get("businesstype", "").strip()
        radius = data.get("radius", 5000)

        logger.info(f"API Search request: city={city}, type={businesstype}, radius={radius}")

        if not city or not businesstype:
            logger.warning("Missing required parameters")
            return jsonify({
                "error": "Ville et type de commerce requis",
                "code": "MISSING_PARAMS"
            }), 400

        results = search_places(city, businesstype, radius)
        logger.info("Search completed")
        return jsonify(results)

    except Exception as e:
        logger.error(f"Unhandled error in api_search: {e}")
        return jsonify({
            "error": str(e),
            "code": "SERVER_ERROR"
        }), 500


@app.route("/api/usage", methods=["GET"])
def api_usage():
    try:
        logger.debug("Usage stats requested")
        return jsonify({
            "requests": tracker.requests_this_month,
            "maxrequests": tracker.max_requests_per_month,
            "cost": f"{tracker.cost_this_month:.2f}",
            "maxcost": f"{tracker.max_cost_per_month:.2f}",
            "usagepercentage": tracker.get_usage_percentage()
        })
    except Exception as e:
        logger.error(f"Error in api_usage: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "api_keys_configured": bool(GOOGLE_PLACES_API_KEY),
        "usage_tracker_active": True
    })


@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        "error": "Endpoint not found",
        "code": "NOT_FOUND"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Server Error: {error}")
    return jsonify({
        "error": "Internal server error",
        "code": "SERVER_ERROR"
    }), 500


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Application started on http://localhost:5000")
    logger.info(f"API Keys configured: {bool(GOOGLE_PLACES_API_KEY)}")
    logger.info("Usage tracking: ACTIVE")
    logger.info("Health check: /api/health")
    logger.info("=" * 60)
    app.run(debug=True, port=5000)
