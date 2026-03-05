import pandas as pd
import matplotlib
import os

# Configuración para servidores (Headless)
if os.environ.get('RENDER') or os.environ.get('PORT'):
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
from datetime import datetime

# Configuración y Silenciado de avisos
warnings.filterwarnings("ignore")

# --- CONFIGURACIÓN GLOBAL ---
URL_SHEETS = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vStSj3DCaJLNOlruyL7dbV1xA1U2ctBLmPMJwKQKnco8lZpzgVI1CcR9gvn-GL88oQBQbn3A688Gp4f/pub?gid=0&single=true&output=csv'
ARCHIVO_LOCAL = 'tasas.csv'
CARPETA_GRAFICOS = 'graficos'
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

def cargar_datos(fuente=URL_SHEETS, respaldo=ARCHIVO_LOCAL):
    """Carga datos desde Google Sheets con respaldo local."""
    try:
        print(f"🌐 Conectando con Google Sheets...")
        df = pd.read_csv(fuente, storage_options={'timeout': 10})
        df['fecha'] = pd.to_datetime(df['fecha'])
        df.set_index('fecha', inplace=True)
        print("✅ Datos cargados exitosamente desde la nube.")
        return df.sort_index()
    except Exception as e:
        print(f"⚠️ Fallo conexión a la nube. Buscando respaldo local...")
        if os.path.exists(respaldo):
            try:
                df = pd.read_csv(respaldo)
                df['fecha'] = pd.to_datetime(df['fecha'])
                df.set_index('fecha', inplace=True)
                print(f"📂 Usando archivo local: '{respaldo}'")
                return df.sort_index()
            except Exception as e_local:
                print(f"❌ Error en archivo local: {e_local}")
        else:
            print(f"❌ Error crítico: No se encontró '{respaldo}'.")
    return None

def mostrar_resumen_semanal(df_relleno):
    """Calcula y muestra estadísticas de la última semana."""
    print("\n" + "="*45)
    print("📊 ANALISTA DE MERCADO: REPORTE SEMANAL")
    print("="*45)

    actual = df_relleno.tail(7)
    previa = df_relleno.iloc[-14:-7]

    if len(previa) < 7:
        print("ℹ️ Datos insuficientes para comparación semanal.")
        return
    
    promedio_actual = actual['precio'].mean()
    promedio_previo = previa['precio'].mean()
    variacion = ((promedio_actual - promedio_previo) / promedio_previo) * 100
    tasa_hoy = df_relleno['precio'].iloc[-1]

    estado = "🚀 ACELERANDO" if variacion > 2 else "📉 ESTABLE/LENTO"
    print(f"🔹 Tasa actual: {tasa_hoy} Bs.")
    print(f"🔹 Variación promedio semanal: {round(variacion, 2)}%")
    print(f"🔹 Tendencia detectada: {estado}")
    print("="*45 + "\n")

def realizar_prediccion(series, fecha_meta):
    """Entrena el modelo SARIMAX y genera el pronóstico."""
    model = SARIMAX(series, order=SARIMAX_ORDER, seasonal_order=SARIMAX_SEASONAL)
    model_fit = model.fit(disp=False)
    
    pasos = (fecha_meta - series.index[-1]).days
    pronostico = model_fit.get_forecast(steps=pasos)
    intervalos = pronostico.conf_int(alpha=0.05)
    
    return pronostico, intervalos

def generar_reporte_visual(df_historial, pronostico, intervalos, fecha_meta):
    """Crea y muestra el gráfico de la proyección (guardado manual)."""
    tasa_actual = df_historial['precio'].iloc[-1]
    precio_final = round(pronostico.predicted_mean.iloc[-1], 2)
    p_min, p_max = round(intervalos.iloc[-1, 0], 2), round(intervalos.iloc[-1, 1], 2)
    inc_bs = round(precio_final - tasa_actual, 2)
    inc_pct = round((inc_bs / tasa_actual) * 100, 2)

    plt.figure(figsize=(11, 6))
    
    # Historial (últimos 15 días) y Proyección
    plt.plot(df_historial.index[-15:], df_historial['precio'].tail(15), label='Historial Real', marker='o', color='#1f77b4', linewidth=2)
    
    fechas_proy = pd.date_range(df_historial.index[-1], fecha_meta, freq='D')
    valores_proy = [tasa_actual] + list(pronostico.predicted_mean)
    plt.plot(fechas_proy, valores_proy, 'r--', label='Proyección SARIMAX', alpha=0.8)

    # Margen de confianza
    plt.fill_between(fechas_proy[1:], intervalos.iloc[:, 0], intervalos.iloc[:, 1], color='red', alpha=0.1, label='Margen Probable')

    # Cuadro de texto informativo
    texto = (f"📊 REPORTE DE PROYECCIÓN\n--------------------------\n"
             f"Fecha Meta:   {fecha_meta.date()}\n"
             f"Tasa Est.:    {precio_final} Bs.\n"
             f"Rango Mín:    {p_min} Bs.\n"
             f"Rango Máx:    {p_max} Bs.\n--------------------------\n"
             f"Incremento:   +{inc_bs} Bs.\n"
             f"Variación:    {inc_pct}%")
    
    plt.text(0.02, 0.96, texto, transform=plt.gca().transAxes, verticalalignment='top', 
             fontsize=10, fontfamily='monospace', bbox=dict(boxstyle='round,pad=0.8', facecolor='#fdfdfd', alpha=0.9, edgecolor='#d62728'))

    plt.title(f"Tendencia Cambiaria: Análisis al {fecha_meta.date()}", fontsize=14, fontweight='bold', pad=20)
    plt.ylabel("Bolívares por Dólar (Bs/USD)")
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.legend(loc='lower right')
    plt.tight_layout()

    # Mostrar la ventana interactiva para guardado manual
    plt.show()

def ejecutar_sistema():
    df_original = cargar_datos()
    if df_original is None: return
    
    df_relleno = df_original.asfreq('D').ffill()
    mostrar_resumen_semanal(df_relleno)
    
    print(f"Opciones: Consultar historial (desde {df_original.index.min().date()}) o predecir futuro.")
    entrada = input(f"📅 Ingrese fecha (AAAA-MM-DD): ")
    
    try:
        fecha_meta = pd.to_datetime(entrada)
        
        # Caso 1: Predicción Futura
        if fecha_meta > df_original.index.max():
            pronostico, intervalos = realizar_prediccion(df_relleno['precio'], fecha_meta)
            print(f"✨ PREDICCIÓN: {round(pronostico.predicted_mean.iloc[-1], 2)} Bs.")
            generar_reporte_visual(df_relleno, pronostico, intervalos, fecha_meta)

        # Caso 2: Consulta Histórica
        elif fecha_meta in df_relleno.index:
            tasa = df_relleno.loc[fecha_meta, 'precio']
            tipo = "Oficial" if fecha_meta in df_original.index else "Vigente (Fin de semana/Feriado)"
            print(f"📖 {tipo}: El {fecha_meta.date()} la tasa fue {tasa} Bs.")
        
        else:
            print("⚠️ La fecha ingresada está fuera del rango histórico disponible.")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")

if __name__ == "__main__":
    ejecutar_sistema()
