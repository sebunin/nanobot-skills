import requests

def get_weather(lat: float, lon: float):
    """
    Получает текущую погоду для заданных координат через Open-Meteo API.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "wind_speed_unit": "ms",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        wind = current.get("wind_speed_10m")
        code = current.get("weather_code")
        
        # Интерпретация кодов WMO (Open-Meteo)
        descriptions = {
            0: "Ясно",
            1: "Преимущественно ясно",
            2: "Переменная облачность",
            3: "Пасмурно",
            45: "Туман",
            48: "Инеистый туман",
            51: "Легкая морось",
            53: "Умеренная морось",
            55: "Сильная морось",
            61: "Слабый дождь",
            63: "Умеренный дождь",
            65: "Сильный дождь",
            71: "Слабый снег",
            73: "Умеренный снег",
            75: "Сильный снег",
            80: "Ливневой дождь",
            81: "Очень сильный ливень",
            82: "Шкваловый ливень",
            95: "Гроза",
            96: "Гроза с градом",
            99: "Сильная гроза с градом"
        }
        status = descriptions.get(code, f"неизвестные условия (код {code})")
        
        return f"Температура: {temp}°C, {status}. Ветер: {wind:.1f} м/с."
    except Exception as e:
        return f"Ошибка Open-Meteo: {str(e)}"
