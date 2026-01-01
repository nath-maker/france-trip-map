#!/usr/bin/env python3
"""
Weather Update Script for France Trip Map
Fetches weather data from Open-Meteo API and updates index.html

This script is run by GitHub Actions every 6 hours to keep
the weather data fresh for the interactive map.
"""

import json
import re
import requests
from datetime import datetime, timedelta

# City coordinates for Open-Meteo API
CITIES = {
    "loctudy": {"lat": 47.8344, "lon": -4.1714, "name": "Loctudy"},
    "quimper": {"lat": 47.9960, "lon": -4.1024, "name": "Quimper"},
    "rennes": {"lat": 48.1173, "lon": -1.6778, "name": "Rennes"},
    "cancale": {"lat": 48.6703, "lon": -1.8514, "name": "Cancale"},
    "avranches": {"lat": 48.6839, "lon": -1.3567, "name": "Avranches"},
    "caen": {"lat": 49.1829, "lon": -0.3707, "name": "Caen"},
    "leMans": {"lat": 47.9959, "lon": 0.1920, "name": "Le Mans"},
    "rouen": {"lat": 49.4432, "lon": 1.0999, "name": "Rouen"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
    "ambleville": {"lat": 49.1456, "lon": 1.7008, "name": "Ambleville"},
}

# Days to fetch (Jan 3-10, 2026)
TARGET_DATES = [
    "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06",
    "2026-01-07", "2026-01-08", "2026-01-09", "2026-01-10"
]

DAY_KEYS = ["jan3", "jan4", "jan5", "jan6", "jan7", "jan8", "jan9", "jan10"]


def fetch_weather(city_key: str) -> dict:
    """Fetch weather data for a city from Open-Meteo API."""
    city = CITIES[city_key]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum",
        "timezone": "Europe/Paris",
        "start_date": TARGET_DATES[0],
        "end_date": TARGET_DATES[-1],
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def calculate_risk(high: float, low: float, snow: float, precip: float) -> tuple:
    """
    Calculate risk level based on weather conditions.
    Returns (risk_level, risk_label) tuple.
    
    Risk factors:
    - Freezing temps (< 0°C overnight)
    - Snow accumulation
    - Rain + freeze = black ice (verglas)
    """
    # Safe conditions: no freezing, no snow
    if low > 2 and snow == 0:
        if high > 8:
            return ("safe", "Parfait")
        return ("safe", "Pas de gel")
    
    # Caution: light frost
    if low > -1 and snow == 0:
        return ("caution", f"Gel léger")
    
    # Danger conditions
    if snow > 5:
        return ("danger", f"NEIGE {snow}cm!")
    elif snow > 2:
        return ("danger", f"NEIGE {snow}cm")
    elif snow > 0:
        return ("danger", f"NEIGE {snow}cm")
    
    # Regel (refreeze) danger: warm day followed by freezing night
    if high > 8 and low < -2:
        return ("danger", f"REGEL {low}°C!")
    
    # Rain + freeze = verglas
    if precip > 0 and low < 0:
        if low < -3:
            return ("danger", "VERGLAS!")
        return ("danger", f"Pluie + gel")
    
    # Severe frost
    if low < -4:
        return ("danger", f"Gel SÉVÈRE {low}°C")
    elif low < -1:
        return ("danger", f"Gel {low}°C")
    
    return ("caution", "Prudence")


def build_weather_data() -> dict:
    """Fetch weather for all cities and build the weatherData object."""
    weather_data = {}
    
    for day_key in DAY_KEYS:
        weather_data[day_key] = {}
    
    for city_key in CITIES:
        print(f"Fetching weather for {city_key}...")
        try:
            data = fetch_weather(city_key)
            daily = data["daily"]
            
            for i, date in enumerate(TARGET_DATES):
                day_key = DAY_KEYS[i]
                
                high = round(daily["temperature_2m_max"][i], 1)
                low = round(daily["temperature_2m_min"][i], 1)
                precip = round(daily["precipitation_sum"][i], 1) if daily["precipitation_sum"][i] else 0
                snow = round(daily["snowfall_sum"][i], 1) if daily["snowfall_sum"][i] else 0
                
                risk, risk_label = calculate_risk(high, low, snow, precip)
                
                weather_data[day_key][city_key] = {
                    "high": high,
                    "low": low,
                    "precip": precip,
                    "snow": snow,
                    "risk": risk,
                    "riskLabel": risk_label
                }
                
        except Exception as e:
            print(f"Error fetching {city_key}: {e}")
            # Keep existing data if fetch fails
            continue
    
    return weather_data


def format_weather_js(weather_data: dict) -> str:
    """Format weather data as JavaScript object literal."""
    lines = ["        const weatherData = {"]
    
    for day_key in DAY_KEYS:
        lines.append(f'            "{day_key}": {{')
        
        city_lines = []
        for city_key, data in weather_data[day_key].items():
            city_line = (
                f'                {city_key}: {{ '
                f'high: {data["high"]}, low: {data["low"]}, '
                f'precip: {data["precip"]}, snow: {data["snow"]}, '
                f'risk: "{data["risk"]}", riskLabel: "{data["riskLabel"]}" }}'
            )
            city_lines.append(city_line)
        
        lines.append(",\n".join(city_lines))
        lines.append("            },")
    
    lines.append("        };")
    return "\n".join(lines)


def update_html(weather_data: dict):
    """Update the weatherData in index.html."""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # Pattern to match the weatherData block between markers
    pattern = r'(// WEATHER_DATA_START\n)(.*?)(// WEATHER_DATA_END)'
    
    new_weather_js = format_weather_js(weather_data)
    replacement = f"// WEATHER_DATA_START\n{new_weather_js}\n        // WEATHER_DATA_END"
    
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    # Update timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    new_html = re.sub(
        r'Données météo mises à jour.*?\|',
        f'Données météo mises à jour: {timestamp} |',
        new_html
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)
    
    print(f"Updated index.html at {timestamp}")


def main():
    print("=" * 50)
    print("Weather Update Script")
    print("=" * 50)
    
    weather_data = build_weather_data()
    
    if weather_data and all(weather_data[day] for day in DAY_KEYS):
        update_html(weather_data)
        print("✅ Weather data updated successfully!")
    else:
        print("❌ Failed to fetch complete weather data")
        exit(1)


if __name__ == "__main__":
    main()
