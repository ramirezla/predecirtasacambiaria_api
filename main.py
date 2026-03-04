import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from datetime import datetime
import pandas as pd

# Añadir el directorio raíz al path para poder importar el modelo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import modelo_prediccion_lineal as modelo

app = FastAPI(
    title="API Predictor de Tasas - PrediccionAlCambio",
    description="API para obtener predicciones de tasas de cambio usando modelos SARIMAX.",
    version="1.0.0"
)

# --- CONFIGURACIÓN DE SEGURIDAD ---
API_KEY_NAME = "X-API-KEY"
# En producción, cambia esto por una variable de entorno real
API_KEY_VALUE = os.getenv("PREDICCION_API_KEY", "Vzla_2026_Secure_Key_99")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validar_api_key(api_key: str = Depends(api_key_header)):
    if api_key == API_KEY_VALUE:
        return api_key
    raise HTTPException(
        status_code=403,
        detail="Acceso denegado: API Key inválida o ausente"
    )

@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido a la API de Predicción al Cambio",
        "estado": "Operacional",
        "documentacion": "/docs"
    }

@app.get("/predecir/{fecha_buscada}")
async def obtener_prediccion(
    fecha_buscada: str, 
    api_key: str = Depends(validar_api_key)
):
    """
    Genera una predicción para la fecha solicitada (AAAA-MM-DD).
    Requiere una API Key válida en el header 'X-API-KEY'.
    """
    try:
        # 1. Validar formato de fecha
        fecha_obj = pd.to_datetime(fecha_buscada)
        
        # 2. Cargar datos usando la función modular que ya tenemos
        df_original = modelo.cargar_datos()
        if df_original is None:
            raise HTTPException(status_code=503, detail="Error al cargar datos de la fuente")
        
        df_relleno = df_original.asfreq('D').ffill()
        tasa_actual = df_relleno['precio'].iloc[-1]
        ultimo_registro = df_original.index.max()

        # CASO 1: Predicción Futura
        if fecha_obj > ultimo_registro:
            pronostico, intervalos = modelo.realizar_prediccion(df_relleno['precio'], fecha_obj)
            
            valor_final = round(pronostico.predicted_mean.iloc[-1], 2)
            p_min = round(intervalos.iloc[-1, 0], 2)
            p_max = round(intervalos.iloc[-1, 1], 2)
            
            # Cálculo de variación respecto al último dato real
            variacion_bs = round(valor_final - tasa_actual, 2)
            variacion_pct = round((variacion_bs / tasa_actual) * 100, 2)

            return {
                "tipo": "Predicción Futura",
                "fecha_meta": fecha_buscada,
                "tasa_estimada_bs": valor_final,
                "rango_confianza_95": [p_min, p_max],
                "variacion_respecto_hoy": {
                    "bolivares": variacion_bs,
                    "porcentaje": f"{variacion_pct}%"
                },
                "ultimo_dato_real": {
                    "fecha": ultimo_registro.strftime('%Y-%m-%d'),
                    "tasa": tasa_actual
                }
            }

        # CASO 2: Consulta Histórica
        elif fecha_obj in df_relleno.index:
            tasa = df_relleno.loc[fecha_obj, 'precio']
            es_real = fecha_obj in df_original.index
            return {
                "tipo": "Consulta Histórica",
                "fecha": fecha_buscada,
                "tasa_bs": tasa,
                "fuente": "BCV Oficial" if es_real else "Vigente (Feriado/Fin de semana)"
            }
        
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Fecha fuera de rango. El historial comienza en {df_original.index.min().date()}"
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use AAAA-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
