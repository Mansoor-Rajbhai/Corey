# X:\Corey\utilities\weather.py
import requests

API_KEY = "d1bb6c23f09b4582123694eed1e2b56b"

def get_weather(location: str):
    """
    Fetches hyper-local atmospheric data via OpenWeatherMap API with robust error handling.
    """
    try:
        search_query = location if "karachi" in location.lower() else f"{location},Karachi,PK"
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={search_query}&limit=1&appid={API_KEY}"
        
        geo_res = requests.get(geo_url, timeout=10)
        
        # Handle 401 right here if the geocoding endpoint rejects the key
        if geo_res.status_code == 401:
            return {
                "status": "error",
                "message": "OpenWeatherMap API Key is invalid or not activated yet. It can take up to 2 hours for newly generated keys to function globally."
            }
            
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        
        if not geo_data:
            lat, lon = 24.8608, 67.0104
            resolved_name = f"{location} (Estimated via Karachi Center)"
        else:
            lat = geo_data[0].get("lat")
            lon = geo_data[0].get("lon")
            resolved_name = f"{location} ({geo_data[0].get('name')})"

        # Step 2: Query weather by Lat/Lon coordinates
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        
        response = requests.get(weather_url, timeout=10)
        
        if response.status_code == 401:
            return {
                "status": "error",
                "message": "OpenWeatherMap API Key is unauthorized for this weather request profile."
            }
            
        response.raise_for_status()
        data = response.json()
        
        main_metrics = data.get("main", {})
        wind = data.get("wind", {})
        weather_info = data.get("weather", [{}])[0]
        
        temp_c = main_metrics.get("temp", 0.0)
        temp_f = round((temp_c * 9/5) + 32, 1)
        wind_speed_kmh = round(wind.get("speed", 0.0) * 3.6, 1)
        
        return {
            "status": "success",
            "location": f"{resolved_name}, Pakistan",
            "weather_service": "OpenWeatherMap",
            "coordinates": f"{lat}, {lon}",
            "temperature_celsius": f"{temp_c}°C",
            "temperature_fahrenheit": f"{temp_f}°F",
            "condition": weather_info.get("description", "Unknown").title(),
            "humidity": f"{main_metrics.get('humidity')}%",
            "wind_speed": f"{wind_speed_kmh} km/h",
            "feels_like_celsius": f"{main_metrics.get('feels_like')}°C"
        }
        
    except requests.exceptions.HTTPError as http_err:
        return {"status": "error", "message": f"HTTP network pipeline fault: {str(http_err)}"}
    except Exception as e:
        return {"status": "error", "message": f"System execution crash: {str(e)}"}