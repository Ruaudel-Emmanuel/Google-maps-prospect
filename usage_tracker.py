#!/usr/bin/env python3
"""
usage_tracker.py

Module indépendant pour tracker l'utilisation de l'API Google Places.
Gère:
  - Compteur mensuel de requêtes
  - Budget en dollars
  - Alertes et blocages
  - Persistance en base de données

Author: Your Name
License: MIT
Created: 2026-01-15
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional
import sqlite3


class UsageTracker:
    """
    Track Google Places API usage and enforce budget limits.
    
    Storage: SQLite database (usage.db)
    
    Attributes:
        db_path (str): Path to SQLite database
        max_requests_per_month (int): Hard limit on API requests
        max_cost_per_month (float): Hard limit on API cost in USD
        cost_per_request (float): Estimated cost per API request
    """

    def __init__(
        self,
        db_path: str = "usage.db",
        max_requests_per_month: int = 20000,
        max_cost_per_month: float = 180.0,
        cost_per_request: float = 0.009  # ~$0.009 per request (rough estimate)
    ):
        """
        Initialize UsageTracker.
        
        Args:
            db_path: Path to SQLite database file
            max_requests_per_month: Maximum allowed requests per month
            max_cost_per_month: Maximum allowed cost per month (USD)
            cost_per_request: Estimated cost per API call
        """
        self.db_path = db_path
        self.max_requests_per_month = max_requests_per_month
        self.max_cost_per_month = max_cost_per_month
        self.cost_per_request = cost_per_request
        
        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table: monthly_usage (summary)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                requests INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
            )
        """)
        
        # Table: request_log (detailed log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                query_type TEXT,
                cost REAL DEFAULT 0.0,
                status TEXT DEFAULT 'success',
                notes TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def _get_current_month_key(self) -> Tuple[int, int]:
        """Get current year and month."""
        now = datetime.utcnow()
        return (now.year, now.month)

    def _ensure_month_exists(self):
        """Ensure current month entry exists in database."""
        year, month = self._get_current_month_key()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR IGNORE INTO monthly_usage (year, month) VALUES (?, ?)",
            (year, month)
        )
        
        conn.commit()
        conn.close()

    def get_current_usage(self) -> Dict:
        """
        Get current month's usage statistics.
        
        Returns:
            Dict with keys:
                - requests: total requests this month
                - cost: estimated cost in USD
                - requests_remaining: budget remaining
                - cost_remaining: cost budget remaining
                - percent_used: % of request budget used
                - status: 'ok' | 'warning' | 'exceeded'
        """
        self._ensure_month_exists()
        
        year, month = self._get_current_month_key()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT requests, cost FROM monthly_usage WHERE year = ? AND month = ?",
            (year, month)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        requests_used = result[0] if result else 0
        cost_used = result[1] if result else 0.0
        
        requests_remaining = max(0, self.max_requests_per_month - requests_used)
        cost_remaining = max(0, self.max_cost_per_month - cost_used)
        percent_used = int((requests_used / self.max_requests_per_month) * 100) if self.max_requests_per_month > 0 else 0
        
        # Determine status
        if percent_used >= 100:
            status = "exceeded"
        elif percent_used >= 80:
            status = "warning"
        else:
            status = "ok"
        
        return {
            "requests": requests_used,
            "cost": round(cost_used, 2),
            "requests_remaining": requests_remaining,
            "cost_remaining": round(cost_remaining, 2),
            "percent_used": percent_used,
            "status": status,
            "month": f"{year}-{month:02d}",
            "max_requests": self.max_requests_per_month,
            "max_cost": self.max_cost_per_month
        }

    def can_make_request(self) -> Tuple[bool, str]:
        """
        Check if API request is allowed.
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        usage = self.get_current_usage()
        
        if usage["status"] == "exceeded":
            return False, (
                f"❌ API Budget Exceeded\n\n"
                f"You've used {usage['requests']} requests "
                f"({usage['cost']} USD) out of {self.max_requests_per_month} allowed.\n\n"
                f"Please wait until next month or upgrade your plan."
            )
        
        return True, ""

    def log_request(
        self,
        endpoint: str,
        query_type: str,
        success: bool = True,
        notes: str = None
    ) -> None:
        """
        Log an API request and increment counter.
        
        Args:
            endpoint: API endpoint called (e.g. 'search_nearby')
            query_type: Type of query (e.g. 'plumber', 'restaurant')
            success: Whether request was successful
            notes: Optional notes about request
        """
        self._ensure_month_exists()
        
        year, month = self._get_current_month_key()
        cost = self.cost_per_request
        status = "success" if success else "failed"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log detailed request
        cursor.execute("""
            INSERT INTO request_log (endpoint, query_type, cost, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (endpoint, query_type, cost, status, notes))
        
        # Update monthly summary
        cursor.execute("""
            UPDATE monthly_usage
            SET requests = requests + 1,
                cost = cost + ?
            WHERE year = ? AND month = ?
        """, (cost, year, month))
        
        conn.commit()
        conn.close()

    def log_failed_request(self, reason: str) -> None:
        """
        Log a request that was blocked (no API call made).
        
        Args:
            reason: Why the request was blocked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO request_log (endpoint, status, notes)
            VALUES (?, ?, ?)
        """, ("blocked", "blocked", reason))
        
        conn.commit()
        conn.close()

    def get_monthly_history(self, months: int = 12) -> list:
        """
        Get usage history for last N months.
        
        Args:
            months: Number of months to retrieve
        
        Returns:
            List of monthly usage dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT year, month, requests, cost
            FROM monthly_usage
            ORDER BY year DESC, month DESC
            LIMIT ?
        """, (months,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "month": f"{year}-{month:02d}",
                "requests": requests,
                "cost": round(cost, 2)
            }
            for year, month, requests, cost in results
        ]

    def get_detailed_log(self, limit: int = 100) -> list:
        """
        Get detailed request log.
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            List of request log entries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, endpoint, query_type, cost, status, notes
            FROM request_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": timestamp,
                "endpoint": endpoint,
                "query_type": query_type,
                "cost": round(cost, 2),
                "status": status,
                "notes": notes
            }
            for timestamp, endpoint, query_type, cost, status, notes in results
        ]

    def reset_month(self, year: int, month: int) -> None:
        """
        Reset usage for a specific month (admin only).
        
        Args:
            year: Year (e.g. 2026)
            month: Month (1-12)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE monthly_usage
            SET requests = 0, cost = 0.0
            WHERE year = ? AND month = ?
        """, (year, month))
        
        conn.commit()
        conn.close()

    def get_alert_message(self) -> Optional[str]:
        """
        Get alert message based on current usage.
        
        Returns:
            Message string or None if usage is OK
        """
        usage = self.get_current_usage()
        percent = usage["percent_used"]
        
        if percent >= 100:
            return (
                f"🔴 CRITICAL: API budget exceeded! "
                f"{usage['requests']} requests used ({usage['cost']}${self.max_cost_per_month})"
            )
        elif percent >= 90:
            return (
                f"🟠 WARNING: API budget 90% used. "
                f"{usage['requests_remaining']} requests remaining."
            )
        elif percent >= 75:
            return (
                f"🟡 INFO: API budget {percent}% used. "
                f"{usage['cost']}${self.max_cost_per_month}."
            )
        
        return None


def create_tracker(config: Dict = None) -> UsageTracker:
    """
    Factory function to create tracker with config.
    
    Args:
        config: Optional dict with keys:
            - max_requests_per_month
            - max_cost_per_month
            - cost_per_request
    
    Returns:
        Initialized UsageTracker instance
    """
    config = config or {}
    return UsageTracker(
        max_requests_per_month=config.get("max_requests_per_month", 20000),
        max_cost_per_month=config.get("max_cost_per_month", 180.0),
        cost_per_request=config.get("cost_per_request", 0.009)
    )


if __name__ == "__main__":
    # Demo / test
    tracker = UsageTracker()
    
    print("=== Current Usage ===")
    usage = tracker.get_current_usage()
    for key, value in usage.items():
        print(f"{key}: {value}")
    
    print("\n=== Alert ===")
    alert = tracker.get_alert_message()
    print(alert or "✅ No alerts")
    
    print("\n=== History (last 12 months) ===")
    history = tracker.get_monthly_history(12)
    for month_data in history:
        print(month_data)
