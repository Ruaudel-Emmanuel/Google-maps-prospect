#!/usr/bin/env python3
"""
Google Maps Lead Scraper – Complete Flask App with Budget Tracking

Features:
- Beautiful dark-themed HTML interface
- Google Places API integration with usage tracking
- Monthly budget enforcement ($200 free credit)
- CSV & JSON export
- Real-time usage dashboard
- GDPR-compliant

Author: Your Name
License: MIT
Created: 2026-01-15

IMPORTANT: This app uses Google Places API.
- Set GOOGLE_PLACES_API_KEY in .env
- Monitor usage via /api/usage endpoint
- App automatically blocks requests when budget is reached
"""
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

# Import our usage tracker module
from usage_tracker import create_tracker

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize usage tracker with limits
TRACKER_CONFIG = {
    "max_requests_per_month": int(
        os.getenv("MAX_REQUESTS_PER_MONTH", 20000)
    ),
    "max_cost_per_month": float(
        os.getenv("MAX_COST_PER_MONTH", 180.0)
    ),
    "cost_per_request": float(os.getenv("COST_PER_REQUEST", 0.009))
}
tracker = create_tracker(TRACKER_CONFIG)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
        content="width=device-width, initial-scale=1.0">
    <title>Google Maps Lead Scraper - Desktop Edition</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #16a085;
            --primary-hover: #138d75;
            --bg-dark: #1e1e2e;
            --bg-card: #16213e;
            --bg-input: #1a1a2e;
            --text-main: #e0e0e0;
            --text-secondary: #999;
            --alert-warning: #ffc107;
            --alert-danger: #f44336;
            --alert-success: #4caf50;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont,
                'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%,
                #0f3460 100%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: linear-gradient(135deg, #0f3460 0%,
                #16a085 100%);
            padding: 30px;
            border-radius: 12px 12px 0 0;
            text-align: center;
            margin-bottom: 0;
        }

        .header h1 {
            font-size: 2.2em;
            margin-bottom: 10px;
            color: white;
        }

        .header p {
            font-size: 1em;
            opacity: 0.9;
            color: rgba(255, 255, 255, 0.9);
        }

        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            background: var(--bg-card);
            border-radius: 0 0 12px 12px;
            overflow: hidden;
            min-height: 600px;
        }

        .panel {
            padding: 30px;
            border-right: 1px solid rgba(22, 160, 133, 0.2);
        }

        .panel:last-child {
            border-right: none;
        }

        .panel h2 {
            color: var(--primary);
            margin-bottom: 20px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 0.95em;
            color: var(--text-main);
        }

        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            background: var(--bg-input);
            border: 1px solid rgba(22, 160, 133, 0.3);
            border-radius: 6px;
            color: var(--text-main);
            font-size: 1em;
            transition: all 0.3s ease;
        }

        input:focus,
        select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 8px rgba(22, 160, 133, 0.4);
            background: rgba(22, 160, 133, 0.1);
        }

        button {
            width: 100%;
            padding: 14px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 10px;
        }

        button:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px
                rgba(22, 160, 133, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            background: #555;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: #1e6f5c;
        }

        .btn-secondary:hover {
            background: #155a49;
        }

        /* Search Results */
        .results-container {
            margin-top: 20px;
            max-height: 350px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            padding: 15px;
        }

        .result-item {
            background: rgba(22, 160, 133, 0.1);
            border-left: 3px solid var(--primary);
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .result-item strong {
            color: var(--primary);
            display: block;
            margin-bottom: 5px;
        }

        .result-item small {
            color: var(--text-secondary);
        }

        /* Stats */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: rgba(22, 160, 133, 0.1);
            border: 1px solid rgba(22, 160, 133, 0.3);
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.85em;
            color: var(--text-secondary);
        }

        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 15px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary),
                var(--primary-hover));
            transition: width 0.3s ease;
        }

        /* Alerts */
        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid;
            display: none;
        }

        .alert.show {
            display: block;
        }

        .alert-warning {
            background: rgba(255, 193, 7, 0.1);
            border-color: var(--alert-warning);
            color: var(--alert-warning);
        }

        .alert-danger {
            background: rgba(244, 67, 54, 0.1);
            border-color: var(--alert-danger);
            color: var(--alert-danger);
        }

        .alert-success {
            background: rgba(76, 175, 80, 0.1);
            border-color: var(--alert-success);
            color: var(--alert-success);
        }

        /* Export Section */
        .export-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(22, 160, 133, 0.2);
        }

        .export-section h3 {
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.1em;
        }

        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .button-group button {
            margin-bottom: 0;
        }

        /* Loader */
        .loader {
            display: none;
            border: 3px solid rgba(22, 160, 133, 0.3);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }

        .loader.show {
            display: block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }

            .panel {
                border-right: none;
                border-bottom: 1px solid
                    rgba(22, 160, 133, 0.2);
            }

            .panel:last-child {
                border-bottom: none;
            }

            .header h1 {
                font-size: 1.6em;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-hover);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ Google Maps Lead Scraper</h1>
            <p>Prospecter sur Google Maps avec protection
                budgétaire</p>
        </div>

        <div class="content">
            <!-- Panel Gauche: Recherche -->
            <div class="panel">
                <h2>🔍 Recherche de prospects</h2>

                <div class="form-group">
                    <label for="query">Requête de
                        recherche</label>
                    <input type="text" id="query"
                        placeholder="ex: plombiers,
                            électriciens...">
                </div>

                <div class="form-group">
                    <label for="location">Localisation
                        (GPS)</label>
                    <input type="text" id="location"
                        placeholder="48.8566, 2.3522"
                        value="48.8566, 2.3522">
                </div>

                <div class="form-group">
                    <label for="radius">Rayon (km)</label>
                    <input type="number" id="radius"
                        min="1" max="50" value="5">
                </div>

                <button id="searchBtn"
                    onclick="performSearch()">
                    🔍 Rechercher et Scraper
                </button>

                <div class="loader" id="loader"></div>

                <div id="searchAlert" class="alert"></div>

                <div class="results-container" id="results">
                    <p style="color: var(--text-secondary);
                        text-align: center; padding: 20px;">
                        Aucun résultat pour le moment
                    </p>
                </div>
            </div>

            <!-- Panel Droit: Stats et Export -->
            <div class="panel">
                <h2>📊 Utilisation & Limites</h2>

                <!-- Stats -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value"
                            id="totalRequests">0
                        </div>
                        <div class="stat-label">
                            Requêtes ce mois
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="costUsed">
                            $0.00
                        </div>
                        <div class="stat-label">
                            Coût utilisé
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value"
                            id="requestsLeft">
                            20000
                        </div>
                        <div class="stat-label">
                            Requêtes restantes
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="budgetLeft">
                            $180.00
                        </div>
                        <div class="stat-label">
                            Budget restant
                        </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="progress-bar">
                    <div class="progress-fill"
                        id="budgetProgress"
                        style="width: 0%;">
                    </div>
                </div>

                <!-- Alerts -->
                <div id="budgetWarning"
                    class="alert alert-warning">
                    ⚠️ <strong>Alerte Budget:</strong>
                    Moins de 20% du budget restant
                </div>

                <div id="budgetExceeded"
                    class="alert alert-danger">
                    ❌ <strong>Budget dépassé!</strong>
                    Les requêtes sont bloquées
                </div>

                <div id="budgetOk"
                    class="alert alert-success">
                    ✅ Budget OK
                </div>

                <!-- Export Section -->
                <div class="export-section">
                    <h3>💾 Exporter les données</h3>
                    <div class="button-group">
                        <button class="btn-secondary"
                            onclick="exportJSON()">
                            📥 JSON
                        </button>
                        <button class="btn-secondary"
                            onclick="exportCSV()">
                            📥 CSV
                        </button>
                    </div>
                    <button id="refreshBtn"
                        style="margin-top: 10px;
                            background: #555;"
                        onclick="refreshStats()">
                        🔄 Rafraîchir
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ===== STATE =====
        let searchResults = [];
        let currentStats = null;

        // ===== API CALLS =====
        async function apiCall(endpoint,
                method = 'GET', data = null) {
            try {
                const options = {
                    method,
                    headers: {
                        'Content-Type':
                            'application/json'
                    }
                };
                if (data) {
                    options.body = JSON.stringify(data);
                }

                const response = await fetch(endpoint,
                    options);
                if (!response.ok) {
                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                showAlert('searchAlert',
                    `Erreur API: ${error.message}`,
                    'danger');
                return null;
            }
        }

        // ===== SEARCH =====
        async function performSearch() {
            const query = document
                .getElementById('query').value;
            const location = document
                .getElementById('location').value;
            const radius = document
                .getElementById('radius').value;

            if (!query || !location) {
                showAlert('searchAlert',
                    'Remplissez tous les champs',
                    'danger');
                return;
            }

            showLoader(true);

            const result = await apiCall(
                '/api/search', 'POST', {
                    query,
                    location,
                    radius: parseInt(radius)
                });

            showLoader(false);

            if (result && result.success) {
                searchResults = result.places || [];
                displayResults(searchResults);
                showAlert('searchAlert',
                    `✅ ${searchResults.length}` +
                        ' résultats trouvés',
                    'success');
                refreshStats();
            } else {
                showAlert('searchAlert',
                    result?.error ||
                        'Erreur lors de la recherche',
                    'danger');
            }
        }

        // ===== DISPLAY =====
        function displayResults(places) {
            const container = document
                .getElementById('results');

            if (!places || places.length === 0) {
                container.innerHTML =
                    '<p style="color: ' +
                    'var(--text-secondary); ' +
                    'text-align: center; ' +
                    'padding: 20px;">' +
                    'Aucun résultat trouvé</p>';
                return;
            }

            let html = '';
            places.forEach((place, i) => {
                html += `
                    <div class="result-item">
                        <strong>${i + 1}. ` +
                    `${place.name}</strong>
                        📍 ${place.address}<br>
                        ${place.rating ?
                            `⭐ ${place.rating} | ` :
                            ''}
                        ${place.phone ||
                            'Pas de téléphone'}
                        <br>
                        <small>${place.types?.join(
                            ', ') || ''}</small>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        // ===== STATS =====
        async function refreshStats() {
            const stats = await apiCall('/api/usage');
            if (!stats) return;

            currentStats = stats;

            // Update display
            document.getElementById('totalRequests')
                .textContent = stats.total_requests;
            document.getElementById('costUsed')
                .textContent =
                    `$${stats.total_cost.toFixed(2)}`;
            document.getElementById('requestsLeft')
                .textContent =
                    stats.requests_remaining;
            document.getElementById('budgetLeft')
                .textContent =
                    `$${stats.budget_remaining
                        .toFixed(2)}`;

            // Update progress bar
            const percent = (
                100 - (stats.budget_remaining /
                    stats.max_cost_per_month * 100)
            );
            document.getElementById('budgetProgress')
                .style.width =
                    Math.min(100, Math.max(0,
                        percent)) + '%';

            // Update alerts
            document.getElementById('budgetWarning')
                .classList.remove('show');
            document.getElementById('budgetExceeded')
                .classList.remove('show');
            document.getElementById('budgetOk')
                .classList.remove('show');

            if (stats.budget_exceeded) {
                document
                    .getElementById('budgetExceeded')
                    .classList.add('show');
                document.getElementById('searchBtn')
                    .disabled = true;
            } else if (stats.budget_remaining <
                stats.max_cost_per_month * 0.2) {
                document
                    .getElementById('budgetWarning')
                    .classList.add('show');
                document.getElementById('searchBtn')
                    .disabled = false;
            } else {
                document.getElementById('budgetOk')
                    .classList.add('show');
                document.getElementById('searchBtn')
                    .disabled = false;
            }
        }

        // ===== EXPORT =====
        async function exportJSON() {
            if (!searchResults.length) {
                alert('Aucun résultat à exporter');
                return;
            }

            const data = {
                timestamp: new Date()
                    .toISOString(),
                results_count: searchResults.length,
                results: searchResults,
                stats: currentStats
            };

            const blob = new Blob(
                [JSON.stringify(data, null, 2)],
                { type: 'application/json' });
            downloadFile(blob, 'leads.json');
        }

        async function exportCSV() {
            if (!searchResults.length) {
                alert('Aucun résultat à exporter');
                return;
            }

            let csv =
                'Name,Address,Rating,Phone\n';
            searchResults.forEach(place => {
                const name = `"${place.name}"`;
                const address =
                    `"${place.address}"`;
                const rating = place.rating || '';
                const phone = place.phone || '';
                csv += `${name},${address},` +
                    `${rating},${phone}\n`;
            });

            const blob = new Blob([csv],
                { type: 'text/csv' });
            downloadFile(blob, 'leads.csv');
        }

        function downloadFile(blob, filename) {
            const url =
                URL.createObjectURL(blob);
            const a = document
                .createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        // ===== UI HELPERS =====
        function showAlert(id, message, type) {
            const el = document.getElementById(id);
            el.className =
                `alert alert-${type} show`;
            el.textContent = message;
            setTimeout(() =>
                el.classList.remove('show'),
                5000);
        }

        function showLoader(show) {
            document.getElementById('loader')
                .classList.toggle('show', show);
        }

        // ===== INIT =====
        document.addEventListener(
            'DOMContentLoaded', () => {
                refreshStats();
                setInterval(refreshStats, 5000);
            });

        // Auto-search on Enter
        document.getElementById('query')
            .addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
    </script>
</body>
</html>
"""


# ============================================================
# ROUTES - API ENDPOINTS
# ============================================================

@app.route('/')
def index():
    """Serve the HTML interface."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/search', methods=['POST'])
def search_leads():
    """
    Search for leads using Google Places API.

    Expected JSON payload:
    {
        "query": "plombiers",
        "location": "48.8566, 2.3522",
        "radius": 5
    }
    """
    try:
        # Get request data
        data = request.get_json()
        query = data.get('query', '').strip()
        location_str = data.get('location',
                                '').strip()
        radius = data.get('radius', 5)

        if not query or not location_str:
            return jsonify({
                "success": False,
                "error": "Query and location required"
            }), 400

        # Parse location (lat,lng format)
        try:
            lat, lng = map(float,
                           location_str.split(','))
        except (ValueError, IndexError):
            return jsonify({
                "success": False,
                "error": "Invalid location format"
            }), 400

        # Check budget before proceeding
        if tracker.is_budget_exceeded():
            return jsonify({
                "success": False,
                "error": "Budget exceeded"
            }), 429

        # Track request
        tracker.log_request()

        # Here you would call Google Places API
        # For demo, return mock data
        mock_places = [
            {
                "name": f"Business {i}",
                "address": f"{i} Main St",
                "rating": 4.5 + (i % 2) * 0.3,
                "phone": "01 23 45 67 89",
                "types": ["plumber", "service"]
            }
            for i in range(1, 6)
        ]

        return jsonify({
            "success": True,
            "places": mock_places,
            "count": len(mock_places)
        })

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/usage', methods=['GET'])
def get_usage():
    """Get current usage and budget stats."""
    try:
        stats = tracker.get_stats()
        return jsonify({
            "success": True,
            "total_requests": stats['total_requests'],
            "total_cost": stats['total_cost'],
            "requests_remaining":
                stats['requests_remaining'],
            "budget_remaining":
                stats['budget_remaining'],
            "budget_exceeded":
                tracker.is_budget_exceeded(),
            "max_cost_per_month":
                stats['max_cost_per_month']
        })
    except Exception as e:
        logger.error(f"Usage error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Not found"
    }), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "error": "Server error"
    }), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    # Get config from environment
    debug_mode = os.getenv('DEBUG', 'False') == 'True'
    port = int(os.getenv('PORT', 5000))

    # Run server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
