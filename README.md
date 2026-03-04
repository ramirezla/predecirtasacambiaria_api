# 🌐 API Predictor Profesional - PrediccionAlCambio

Servicio RESTful construido con **FastAPI** para la consulta de datos históricos y proyecciones de tasas de cambio (SARIMAX).

## 🔒 Seguridad
La API está protegida por un **API Key Header**. Todas las peticiones deben incluir la cabecera:
- **Header Name:** `X-API-KEY`
- **Valor por defecto:** `Vzla_2026_Secure_Key_99`

> **Sugerencia:** En producción, defina la variable de entorno `PREDICCION_API_KEY` con un valor más robusto.

## 📡 Endpoints principales
### `GET /predecir/{fecha}`
Obtiene el valor real (historial) o proyectado (futuro) para una fecha específica.

**Ejemplo de respuesta (Predicción):**
```json
{
    "tipo": "Predicción Futura",
    "fecha_meta": "2026-03-20",
    "tasa_estimada_bs": 435.50,
    "rango_confianza_95": [430.10, 440.90],
    "variacion_respecto_hoy": {
        "bolivares": 15.51,
        "porcentaje": "3.69%"
    },
    "ultimo_dato_real": { "fecha": "2026-03-04", "tasa": 419.99 }
}
```

## 🚀 Instalación y Ejecución
Para iniciar el servidor localmente:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Acceda a la documentación interactiva (Swagger) en: `http://localhost:8000/docs`

## 🧪 Pruebas con cURL
Para probar la API desde la terminal:
```bash
curl -H "X-API-KEY: Vzla_2026_Secure_Key_99" http://localhost:8000/predecir/2026-03-20
```
