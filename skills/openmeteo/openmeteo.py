import requests

def get_weather(lat: float, lon: float):
    """
    Получает текущую погоду для заданных координат через Open-Meteo API.
    """
    url = "https://open-meteo.com"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "windspeed_unit": "ms",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current_weather", {})
        temp = current.get("temperature")
        wind = current.get("windspeed")
        code = current.get("weathercode")
        
        # Простая интерпретация кодов WMO
        descriptions = {
            0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 
            3: "Пасмурно", 45: "Туман", 48: "Инеистый туман", 
            51: "Легкая морось", 61: "Слабый дождь", 71: "Слабый снег",
            80: "Ливневый дождь", 95: "Гроза"
        }
        status = descriptions.get(code, "неизвестные условия (код " + str(code) + ")")
        
        return f"Температура: {temp}°C, {status}. Ветер: {wind} м/с."
    except Exception as e:
        return f"Ошибка Open-Meteo: {str(e)}"
