name: openmeteo
description: Получение точного прогноза погоды через Open-Meteo API (без ключа).
functions:
  - name: get_weather
    description: Возвращает текущую температуру и условия по координатам.
    parameters:
      type: object
      properties:
        lat:
          type: number
          description: Широта (latitude)
        lon:
          type: number
          description: Долгота (longitude)
      required: [lat, lon]
