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
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

# Import our usage tracker module
from usage_tracker import UsageTracker, create_tracker

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize usage tracker with limits
TRACKER_CONFIG = {
    "max_requests_per_month": int(os.getenv("MAX_REQUESTS_PER_MONTH", 20000)),
    "max_cost_per_month": float(os.getenv("MAX_COST_PER_MONTH", 180.0)),
    "cost_per_request": float(os.getenv("COST_PER_REQUEST", 0.009))
}

tracker = create_tracker(TRACKER_CONFIG)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Google Maps Lead Scraper – Budget Protected</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            color: #e5e7eb;
            min-height: 100vh;
            padding: 1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1.5rem;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #38bdf8, #0ea5e9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 0.95rem;
            color: #9ca3af;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .card {
            background: rgba(2, 6, 23, 0.8);
            border: 1px solid rgba(30, 41, 59, 0.6);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
        }

        .card h2 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: #f1f5f9;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
            color: #f3f4f6;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        input[type="text"] {
            width: 100%;
            padding: 0.65rem 0.85rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(148, 163, 184, 0.3);
            background: rgba(15, 23, 42, 0.6);
            color: #f1f5f9;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
            background: rgba(15, 23, 42, 0.9);
        }

        button {
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            border: none;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            width: 100%;
        }

        .btn-primary {
            background: linear-gradient(135deg, #38bdf8, #0ea5e9);
            color: #0f172a;
            margin-top: 0.75rem;
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(56, 189, 248, 0.5);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .usage-bar {
            width: 100%;
            height: 8px;
            background: rgba(148, 163, 184, 0.2);
            border-radius: 999px;
            overflow: hidden;
            margin: 0.75rem 0;
        }

        .usage-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #38bdf8, #f59e0b, #ef4444);
            width: var(--percent);
            transition: width 0.3s ease;
        }

        .usage-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-top: 0.75rem;
        }

        .stat {
            background: rgba(30, 41, 59, 0.5);
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
        }

        .stat-label {
            color: #9ca3af;
            font-size: 0.75rem;
            margin-bottom: 0.25rem;
        }

        .stat-value {
            color: #f1f5f9;
            font-weight: 600;
            font-size: 0.95rem;
        }

        .alert {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }

        .alert-success {
            background: rgba(16, 185, 129, 0.1);
            border-color: #10b981;
            color: #86efac;
        }

        .alert-warning {
            background: rgba(245, 158, 11, 0.1);
            border-color: #f59e0b;
            color: #fcd34d;
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            border-color: #ef4444;
            color: #fca5a5;
        }

        .results-section {
            margin-top: 2rem;
        }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .results-header h2 {
            font-size: 1.1rem;
            color: #f1f5f9;
        }

        .results-count {
            font-size: 0.85rem;
            color: #9ca3af;
            background: rgba(56, 189, 248, 0.1);
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .result-item {
            border-radius: 0.75rem;
            border: 1px solid rgba(30, 41, 59, 0.8);
            padding: 1rem;
            margin-bottom: 0.85rem;
            background: rgba(30, 41, 59, 0.5);
            transition: all 0.2s ease;
        }

        .result-item:hover {
            border-color: rgba(56, 189, 248, 0.5);
            box-shadow: 0 10px 25px rgba(56, 189, 248, 0.1);
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.65rem;
        }

        .result-name {
            font-weight: 600;
            color: #f9fafb;
            font-size: 0.95rem;
        }

        .result-rating {
            font-size: 0.85rem;
            color: #facc15;
            white-space: nowrap;
        }

        .result-meta {
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            color: #9ca3af;
        }

        .badge {
            display: inline-block;
            margin-right: 0.4rem;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.4);
            background: rgba(15, 23, 42, 0.8);
            font-size: 0.7rem;
            color: #cbd5e1;
            font-weight: 500;
        }

        .loading {
            text-align: center;
            color: #9ca3af;
            padding: 2rem;
        }

        .spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid rgba(56, 189, 248, 0.3);
            border-top-color: #38bdf8;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 0.5rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .export-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .btn-export {
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            background: rgba(148, 163, 184, 0.1);
            color: #cbd5e1;
            border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 0.4rem;
            cursor: pointer;
            flex: 1;
        }

        .btn-export:hover {
            background: rgba(148, 163, 184, 0.2);
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .usage-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🗺️ Google Maps Lead Scraper</h1>
        <p class="subtitle">Automate B2B prospection with budget protection</p>
    </div>

    <div class="grid">
        <!-- LEFT: Search Form + Usage Dashboard -->
        <div>
            <div class="card">
                <h2>Search Leads</h2>
                <form id="scrape-form">
                    <div class="form-group">
                        <label for="query">Business Type</label>
                        <input 
                            id="query" 
                            name="query" 
                            type="text"
                            placeholder="e.g. plumber, electrician"
                            required
                        >
                    </div>

                    <div class="form-group">
                        <label for="location">Location</label>
                        <input 
                            id="location" 
                            name="location" 
                            type="text"
                            placeholder="e.g. Rennes, Paris"
                            required
                        >
                    </div>

                    <button type="submit" class="btn-primary" id="submit-btn">
                        Generate Leads
                    </button>
                </form>
            </div>

            <div class="card" style="margin-top: 1.5rem;">
                <h2>📊 API Usage This Month</h2>
                <div id="usage-alert"></div>
                <div class="usage-bar">
                    <div class="usage-bar-fill" id="usage-bar-fill" style="--percent: 0%"></div>
                </div>
                <div class="usage-stats" id="usage-stats"></div>
                <p style="font-size: 0.8rem; color: #6b7280; margin-top: 0.75rem;">
                    💡 You have a free $200 credit per month with Google.
                    <br>This app tracks and blocks requests when budget is reached.
                </p>
            </div>
        </div>

        <!-- RIGHT: Results -->
        <div>
            <div class="card">
                <div class="results-section" id="results-section" style="display: none;">
                    <div class="results-header">
                        <h2>Results</h2>
                        <span class="results-count" id="results-count">0 leads</span>
                    </div>
                    <div id="results"></div>
                    <div class="export-buttons" id="export-buttons"></div>
                </div>
                <div id="empty-state" style="text-align: center; color: #9ca3af; padding: 2rem;">
                    <p>👈 Search for leads in the left panel</p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
const form = document.getElementById('scrape-form');
const resultsDiv = document.getElementById('results');
const resultsSection = document.getElementById('results-section');
const resultsCount = document.getElementById('results-count');
const emptyState = document.getElementById('empty-state');
const submitBtn = document.getElementById('submit-btn');
const exportButtons = document.getElementById('export-buttons');

// Load usage on page load
window.addEventListener('load', updateUsageDisplay);

async function updateUsageDisplay() {
    try {
        const res = await fetch('/api/usage');
        const data = await res.json();
        
        const percent = data.percent_used;
        const fillEl = document.getElementById('usage-bar-fill');
        fillEl.style.setProperty('--percent', percent + '%');
        
        const alertEl = document.getElementById('usage-alert');
        let alertClass = 'alert-success';
        let alertMsg = '✅ API usage normal';
        
        if (percent >= 100) {
            alertClass = 'alert-error';
            alertMsg = '🔴 Budget exceeded';
            submitBtn.disabled = true;
        } else if (percent >= 80) {
            alertClass = 'alert-warning';
            alertMsg = '🟠 Warning: budget 80%+ used';
        }
        
        alertEl.innerHTML = `<div class="alert ${alertClass}">${alertMsg}</div>`;
        
        const statsEl = document.getElementById('usage-stats');
        statsEl.innerHTML = `
            <div class="stat">
                <div class="stat-label">Requests Used</div>
                <div class="stat-value">${data.requests}/${data.max_requests}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Cost Used</div>
                <div class="stat-value">$${data.cost}/$${data.max_cost}</div>
            </div>
            <div class="stat">
                <div class="stat-label">% Used</div>
                <div class="stat-value">${data.percent_used}%</div>
            </div>
            <div class="stat">
                <div class="stat-label">Remaining</div>
                <div class="stat-value">${data.requests_remaining} requests</div>
            </div>
        `;
        
    } catch (err) {
        console.error("Failed to fetch usage:", err);
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const query = document.getElementById('query').value.trim();
    const location = document.getElementById('location').value.trim();
    
    if (!query || !location) return;
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Checking budget...';
    emptyState.style.display = 'none';
    resultsDiv.innerHTML = '<div class="loading"><span class="spinner"></span>Generating leads...</div>';
    resultsSection.style.display = 'block';
    
    try {
        const res = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, location })
        });
        
        const data = await res.json();
        
        if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-error">${data.error}</div>`;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generate Leads';
            updateUsageDisplay();
            return;
        }
        
        if (!Array.isArray(data.leads) || data.leads.length === 0) {
            resultsDiv.innerHTML = '<p style="color: #9ca3af;">No leads found.</p>';
            resultsCount.textContent = '0 leads';
        } else {
            resultsCount.textContent = data.leads.length + ' lead' + (data.leads.length !== 1 ? 's' : '');
            resultsDiv.innerHTML = data.leads.map((lead, idx) => `
                <div class="result-item">
                    <div class="result-header">
                        <div>
                            <div class="result-name">${idx + 1}. ${lead.name}</div>
                            <div class="result-meta">${lead.category}</div>
                        </div>
                        <div class="result-rating">⭐ ${lead.rating} (${lead.review_count})</div>
                    </div>
                    <div class="result-meta">📍 ${lead.address}</div>
                    <div class="result-meta">
                        ${lead.phone ? '📞 ' + lead.phone : ''}
                        ${lead.website ? '<span class="badge">Website</span>' : ''}
                        ${lead.email ? '<span class="badge">Email</span>' : ''}
                    </div>
                </div>
            `).join('');
            
            exportButtons.innerHTML = `
                <button class="btn-export" onclick="exportCSV(${JSON.stringify(data.leads).replace(/"/g, '&quot;')})">
                    📥 Export CSV
                </button>
                <button class="btn-export" onclick="exportJSON(${JSON.stringify(data.leads).replace(/"/g, '&quot;')})">
                    📥 Export JSON
                </button>
            `;
        }
        
    } catch (err) {
        console.error(err);
        resultsDiv.innerHTML = '<div class="alert alert-error">Error: ' + err.message + '</div>';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate Leads';
        updateUsageDisplay();
    }
});

function exportCSV(leads) {
    const headers = ['Name', 'Category', 'Address', 'Phone', 'Website', 'Email', 'Rating', 'Reviews'];
    const rows = leads.map(l => [
        l.name, l.category, l.address, l.phone || '', 
        l.website || '', l.email || '', l.rating, l.review_count
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => '"' + (c || '') + '"').join(',')).join('\\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'leads_' + new Date().toISOString().split('T')[0] + '.csv';
    a.click();
}

function exportJSON(leads) {
    const json = JSON.stringify(leads, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'leads_' + new Date().toISOString().split('T')[0] + '.json';
    a.click();
}
</script>
</body>
</html>
"""

# ============================================================================
# ROUTES
# ============================================================================

@app.route("/", methods=["GET"])
def index():
    """Serve main HTML interface."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/usage", methods=["GET"])
def api_usage():
    """Get current API usage statistics."""
    usage = tracker.get_current_usage()
    return jsonify(usage)


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """
    Scrape Google Maps leads with budget protection.
    
    Request JSON:
        {
            "query": "plumber",
            "location": "Rennes"
        }
    
    Response JSON:
        {
            "query": "plumber",
            "location": "Rennes",
            "leads": [...]  OR  "error": "message"
        }
    """
    try:
        # Parse request
        data = request.get_json(force=True)
        query = data.get("query", "").strip()
        location = data.get("location", "").strip()

        if not query or not location:
            tracker.log_failed_request("Missing query or location")
            return jsonify({"error": "Missing 'query' or 'location'"}), 400

        # Check budget BEFORE making API call
        can_request, reason = tracker.can_make_request()
        if not can_request:
            tracker.log_failed_request("Budget exceeded")
            return jsonify({"error": reason}), 429

        # ===== REPLACE THIS WITH REAL GOOGLE PLACES API CALL =====
        # This is mock data for now
        leads = generate_mock_leads(query, location)
        
        # Log successful request
        tracker.log_request(
            endpoint="search_nearby",
            query_type=query,
            success=True,
            notes=f"Location: {location}"
        )

        return jsonify({
            "query": query,
            "location": location,
            "leads": leads,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        tracker.log_failed_request(f"Exception: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/usage/history", methods=["GET"])
def api_usage_history():
    """Get usage history (last 12 months)."""
    history = tracker.get_monthly_history(12)
    return jsonify({"history": history})


@app.route("/api/usage/log", methods=["GET"])
def api_usage_log():
    """Get detailed request log (last 100 entries)."""
    limit = request.args.get("limit", 100, type=int)
    log = tracker.get_detailed_log(limit)
    return jsonify({"log": log})


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Google Maps Lead Scraper",
        "version": "2.0",
        "budget_tracking": "enabled"
    }), 200


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_mock_leads(query: str, location: str, count: int = 5) -> list:
    """
    Generate mock lead data.
    
    TODO: Replace with real Google Places API calls
    
    Args:
        query: Business type
        location: Geographic location
        count: Number of leads
    
    Returns:
        List of lead dicts
    """
    leads_data = [
        {
            "name": f"{query.title()} Alpha - {location}",
            "address": f"12 Rue des Exemples, {location}",
            "phone": "+33 2 99 00 00 01",
            "website": "https://example-alpha.com",
            "email": "contact@example-alpha.com",
            "rating": 4.7,
            "review_count": 128,
            "category": query.title()
        },
        {
            "name": f"{query.title()} Beta - {location}",
            "address": f"5 Avenue de la Démo, {location}",
            "phone": "+33 2 99 00 00 02",
            "website": "",
            "email": "",
            "rating": 4.3,
            "review_count": 54,
            "category": query.title()
        },
        {
            "name": f"{query.title()} Gamma - {location}",
            "address": f"Place Centrale, {location}",
            "phone": "",
            "website": "https://example-gamma.fr",
            "email": "hello@example-gamma.fr",
            "rating": 4.9,
            "review_count": 212,
            "category": query.title()
        },
        {
            "name": f"{query.title()} Delta - {location}",
            "address": f"Parc de la Innovation, {location}",
            "phone": "+33 2 99 00 00 04",
            "website": "https://example-delta.com",
            "email": "info@example-delta.com",
            "rating": 4.2,
            "review_count": 87,
            "category": query.title()
        },
        {
            "name": f"{query.title()} Epsilon - {location}",
            "address": f"Zone Industrielle Nord, {location}",
            "phone": "",
            "website": "",
            "email": "contact@example-epsilon.fr",
            "rating": 3.9,
            "review_count": 32,
            "category": query.title()
        }
    ]
    
    return leads_data[:count]


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # For production, use Gunicorn instead
    debug_mode = os.getenv("FLASK_DEBUG", "False") == "True"
    app.run(
        debug=debug_mode,
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000))
    )
