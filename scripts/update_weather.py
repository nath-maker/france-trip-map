#!/usr/bin/env python3
"""
Weather Update Script for France Trip Map (v2.0 - Hourly Data)
Fetches HOURLY weather data from Open-Meteo API and updates index.html

Key changes from v1:
- Uses hourly API instead of daily
- Stores 24 hourly temps per city per day
- JavaScript can calculate arrival temps based on user-selected departure time
- Keeps overnightLow for regel (black ice) warnings
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


def fetch_hourly_weather(city_key: str) -> dict:
    """Fetch HOURLY weather data for a city from Open-Meteo API."""
    city = CITIES[city_key]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "hourly": "temperature_2m,precipitation,snowfall",
        "daily": "precipitation_sum,snowfall_sum",  # Keep daily totals for snow/precip
        "timezone": "Europe/Paris",  # Critical: always use Paris timezone
        "start_date": TARGET_DATES[0],
        "end_date": TARGET_DATES[-1],
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_day_data(hourly_data: dict, daily_data: dict, day_index: int) -> dict:
    """
    Extract data for a single day from the hourly API response.
    
    Returns:
        {
            "hourly": [temp_00, temp_01, ..., temp_23],  # 24 hourly temps
            "overnightLow": float,  # Min temp from 00:00-06:00 (for regel warning)
            "dailyHigh": float,     # Max temp of day (for display)
            "dailyLow": float,      # Min temp of day (for display)
            "snow": float,          # Daily snow total
            "precip": float         # Daily precipitation total
        }
    """
    # Hourly data is indexed: day 0 = hours 0-23, day 1 = hours 24-47, etc.
    start_hour = day_index * 24
    end_hour = start_hour + 24
    
    hourly_temps = hourly_data["temperature_2m"][start_hour:end_hour]
    
    # Round all temps to 1 decimal
    hourly_temps = [round(t, 1) if t is not None else None for t in hourly_temps]
    
    # Overnight low: minimum temp from midnight to 6am (hours 0-5)
    overnight_temps = hourly_temps[0:6]
    overnight_low = min([t for t in overnight_temps if t is not None], default=None)
    
    # Daily high/low for display
    valid_temps = [t for t in hourly_temps if t is not None]
    daily_high = max(valid_temps) if valid_temps else None
    daily_low = min(valid_temps) if valid_temps else None
    
    # Snow and precipitation from daily data
    snow = daily_data["snowfall_sum"][day_index]
    snow = round(snow, 1) if snow is not None else 0
    
    precip = daily_data["precipitation_sum"][day_index]
    precip = round(precip, 1) if precip is not None else 0
    
    return {
        "hourly": hourly_temps,
        "overnightLow": overnight_low,
        "dailyHigh": daily_high,
        "dailyLow": daily_low,
        "snow": snow,
        "precip": precip
    }


def build_weather_data() -> dict:
    """Fetch hourly weather for all cities and build the weatherData object."""
    weather_data = {}
    
    for day_key in DAY_KEYS:
        weather_data[day_key] = {}
    
    for city_key in CITIES:
        print(f"Fetching hourly weather for {city_key}...")
        try:
            data = fetch_hourly_weather(city_key)
            hourly = data["hourly"]
            daily = data["daily"]
            
            for i, date in enumerate(TARGET_DATES):
                day_key = DAY_KEYS[i]
                day_data = extract_day_data(hourly, daily, i)
                weather_data[day_key][city_key] = day_data
                
        except Exception as e:
            print(f"Error fetching {city_key}: {e}")
            continue
    
    return weather_data


def format_hourly_array(temps: list) -> str:
    """Format hourly temps array as compact JavaScript."""
    # Replace None with null for JavaScript
    formatted = [str(t) if t is not None else "null" for t in temps]
    return "[" + ",".join(formatted) + "]"


def format_weather_js(weather_data: dict) -> str:
    """Format weather data as JavaScript object literal with hourly data."""
    lines = ["        const weatherData = {"]
    
    for day_key in DAY_KEYS:
        lines.append(f'            "{day_key}": {{')
        
        city_lines = []
        for city_key, data in weather_data[day_key].items():
            hourly_str = format_hourly_array(data["hourly"])
            overnight = data["overnightLow"] if data["overnightLow"] is not None else "null"
            high = data["dailyHigh"] if data["dailyHigh"] is not None else "null"
            low = data["dailyLow"] if data["dailyLow"] is not None else "null"
            
            city_line = (
                f'                {city_key}: {{ '
                f'hourly: {hourly_str}, '
                f'overnightLow: {overnight}, '
                f'dailyHigh: {high}, dailyLow: {low}, '
                f'snow: {data["snow"]}, precip: {data["precip"]} }}'
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
    print("Weather Update Script v2.0 (Hourly Data)")
    print("=" * 50)
    
    weather_data = build_weather_data()
    
    if weather_data and all(weather_data[day] for day in DAY_KEYS):
        update_html(weather_data)
        print("✅ Hourly weather data updated successfully!")
    else:
        print("❌ Failed to fetch complete weather data")
        exit(1)


if __name__ == "__main__":
    main()
