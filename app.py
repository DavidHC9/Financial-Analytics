import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Financial Analytics - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tarjetas, métricas y diseño visual limpio
st.markdown("""
<style>
    /* Estilo para tarjetas y contenedores */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 15px;
    }
    .badge-overbought {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-oversold {
        background-color: #dcfce7;
        color: #16a34a;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-neutral {
        background-color: #e0f2fe;
        color: #0284c7;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    /* Estilo del pie de página del sidebar */
    .sidebar-footer {
        font-size: 0.85rem;
        color: #64748b;
        text-align: center;
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# GESTIÓN DE API KEY Y PETICIONES A ALPHA VANTAGE
# ==============================================================================
BASE_URL = "https://www.alphavantage.co/query"

def get_api_key():
    """Obtiene la API Key desde Streamlit Secrets de forma segura."""
    try:
        if "ALPHA_VANTAGE_API_KEY" in st.secrets:
            return st.secrets["ALPHA_VANTAGE_API_KEY"]
    except Exception:
        pass
    return None

API_KEY = get_api_key()

@st.cache_data(ttl=300, show_spinner=False)
def hacer_request(params):
    """
    Función helper optimizada y en caché para consultar la API de Alpha Vantage.
    Retorna (data_json, error_message).
    """
    if not API_KEY or API_KEY == "TU_API_KEY":
        return None, "🔑 No se configuró la API Key en Streamlit Secrets (.streamlit/secrets.toml)."
    
    req_params = params.copy()
    req_params['apikey'] = API_KEY
    
    try:
        response = requests.get(BASE_URL, params=req_params, timeout=12)
        data = response.json()
        
        if 'Error Message' in data:
            return None, "❌ El símbolo ingresado no es válido o no se encontraron datos."
        elif 'Note' in data:
            return None, "⚠️ Se alcanzó temporalmente el límite de solicitudes de Alpha Vantage (5 por minuto). Intenta nuevamente en un minuto."
        elif 'Information' in data:
            info_msg = data['Information']
            if "rate limit" in info_msg.lower() or "frequency" in info_msg.lower():
                return None, "⚠️ Se alcanzó temporalmente el límite de solicitudes de Alpha Vantage. Intenta nuevamente en un minuto."
            return None, f"ℹ️ Información de la API: {info_msg}"
            
        return data, None
    except requests.exceptions.Timeout:
        return None, "⏱️ Se agotó el tiempo de espera al conectar con Alpha Vantage."
    except Exception as e:
        return None, f"❌ No fue posible conectarse con Alpha Vantage: {str(e)}"

# ==============================================================================
# FUNCIONES REUTILIZABLES DE CONVERSIÓN A DATAFRAME
# ==============================================================================
def convertir_time_series(data, key):
    if not data or key not in data:
        return None
    df = pd.DataFrame.from_dict(data[key], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    df = df.sort_index(ascending=True) # Cronológico (más antiguo al más reciente)
    return df

def convertir_commodities(data):
    if not data or 'data' not in data:
        return None
    df = pd.DataFrame(data['data'])
    if 'date' not in df.columns:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()
    return df.sort_index(ascending=True) # Cronológico

# ==============================================================================
# FUNCIONES REUTILIZABLES DE CONSULTA DE DATOS (CON CACHÉ)
# ==============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_daily(symbol, outputsize='compact'):
    params = {'function': 'TIME_SERIES_DAILY', 'symbol': symbol, 'outputsize': outputsize}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_time_series(data, 'Time Series (Daily)')
    if df is not None:
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return df, None
    return None, "No se encontraron datos diarios."

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_weekly(symbol):
    params = {'function': 'TIME_SERIES_WEEKLY', 'symbol': symbol}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_time_series(data, 'Weekly Time Series')
    if df is not None:
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return df, None
    return None, "No se encontraron datos semanales."

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_monthly(symbol):
    params = {'function': 'TIME_SERIES_MONTHLY', 'symbol': symbol}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_time_series(data, 'Monthly Time Series')
    if df is not None:
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return df, None
    return None, "No se encontraron datos mensuales."

@st.cache_data(ttl=300, show_spinner=False)
def get_rsi(symbol, time_period=14):
    params = {
        'function': 'RSI',
        'symbol': symbol,
        'interval': 'daily',
        'time_period': time_period,
        'series_type': 'close'
    }
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_time_series(data, 'Technical Analysis: RSI')
    if df is not None:
        df.columns = ['RSI']
        return df, None
    return None, "No se pudieron obtener los datos de RSI."

@st.cache_data(ttl=300, show_spinner=False)
def get_bollinger_bands(symbol, time_period=20, nbdevup=2, nbdevdn=2):
    params = {
        'function': 'BBANDS',
        'symbol': symbol,
        'interval': 'daily',
        'time_period': time_period,
        'series_type': 'close',
        'nbdevup': nbdevup,
        'nbdevdn': nbdevdn
    }
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_time_series(data, 'Technical Analysis: BBANDS')
    if df is not None:
        return df, None
    return None, "No se pudieron obtener las Bandas de Bollinger."

@st.cache_data(ttl=300, show_spinner=False)
def get_gold():
    params = {'function': 'GOLD_SILVER_HISTORY', 'symbol': 'GOLD', 'interval': 'daily'}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_commodities(data)
    if df is not None:
        price_col = 'value' if 'value' in df.columns else df.columns[0]
        df = df.rename(columns={price_col: 'Price'})
        return df[['Price']], None
    return None, "No se pudieron obtener datos del Oro."

@st.cache_data(ttl=300, show_spinner=False)
def get_silver():
    params = {'function': 'GOLD_SILVER_HISTORY', 'symbol': 'SILVER', 'interval': 'daily'}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_commodities(data)
    if df is not None:
        price_col = 'value' if 'value' in df.columns else df.columns[0]
        df = df.rename(columns={price_col: 'Price'})
        return df[['Price']], None
    return None, "No se pudieron obtener datos de la Plata."

@st.cache_data(ttl=300, show_spinner=False)
def get_wti():
    params = {'function': 'WTI', 'interval': 'daily'}
    data, err = hacer_request(params)
    if err:
        return None, err
    df = convertir_commodities(data)
    if df is not None:
        price_col = 'value' if 'value' in df.columns else df.columns[0]
        df = df.rename(columns={price_col: 'Price'})
        return df[['Price']], None
    return None, "No se pudieron obtener datos de Petróleo WTI."

# ==============================================================================
# SIDEBAR / NAVEGACIÓN
# ==============================================================================
st.sidebar.markdown("## 📊 Financial Analytics")
st.sidebar.markdown("---")

opciones_menu = [
    "🏠 Inicio",
    "📈 Acciones",
    "📊 Análisis técnico",
    "🥇 Commodities",
    "🔄 Comparador",
    "ℹ️ Información"
]

pagina_seleccionada = st.sidebar.radio("Navegación", opciones_menu)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div class="sidebar-footer">
        <p><b>Financial Analytics v2.0</b></p>
        <p>⚡ Powered by <b>Alpha Vantage API</b></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Validación inicial de API Key
if not API_KEY or API_KEY == "TU_API_KEY":
    st.warning("""
    🔑 **API Key no configurada**  
    Para habilitar la consulta de datos reales, agrega tu API Key de Alpha Vantage en `.streamlit/secrets.toml`:
    ```toml
    ALPHA_VANTAGE_API_KEY = "TU_API_KEY_AQUI"
    ```
    *(Consigue una API Key gratuita en [alphavantage.co](https://www.alphavantage.co/support/#api-key))*
    """)

# ==============================================================================
# 1. PÁGINA: 🏠 INICIO
# ==============================================================================
if pagina_seleccionada == "🏠 Inicio":
    st.title("Financial Analytics")
    st.subheader("Dashboard interactivo de análisis financiero")
    st.markdown("---")

    st.markdown("### 📋 Resumen Principal del Mercado")
    
    # Cargar datos para métricas principales
    with st.spinner("Cargando indicadores de inicio..."):
        df_stock_ibm, err_ibm = get_stock_daily("IBM")
        df_rsi_ibm, _ = get_rsi("IBM")
        df_gold, err_gold = get_gold()
        df_silver, err_silver = get_silver()
        df_wti, err_wti = get_wti()

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    # Tarjeta 1: IBM / Acción Base
    with col1:
        if df_stock_ibm is not None and len(df_stock_ibm) > 1:
            precio_actual = df_stock_ibm['Close'].iloc[-1]
            precio_anterior = df_stock_ibm['Close'].iloc[-2]
            delta = precio_actual - precio_anterior
            delta_pct = (delta / precio_anterior) * 100
            st.metric("📈 IBM (Precio)", f"${precio_actual:,.2f}", f"{delta_pct:+.2f}%")
        else:
            st.metric("📈 IBM (Precio)", "N/A", "0.00%")

    # Tarjeta 2: RSI IBM
    with col2:
        if df_rsi_ibm is not None and len(df_rsi_ibm) > 0:
            rsi_val = df_rsi_ibm['RSI'].iloc[-1]
            estado = "Sobrecompra" if rsi_val > 70 else ("Sobreventa" if rsi_val < 30 else "Neutral")
            st.metric("📊 RSI (IBM - 14d)", f"{rsi_val:.1f}", estado)
        else:
            st.metric("📊 RSI (IBM)", "N/A", "N/A")

    # Tarjeta 3: Oro
    with col3:
        if df_gold is not None and len(df_gold) > 1:
            gold_price = df_gold['Price'].iloc[-1]
            gold_prev = df_gold['Price'].iloc[-2]
            gold_delta_pct = ((gold_price - gold_prev) / gold_prev) * 100
            st.metric("🥇 Oro (USD/oz)", f"${gold_price:,.2f}", f"{gold_delta_pct:+.2f}%")
        else:
            st.metric("🥇 Oro", "N/A", "0.00%")

    # Tarjeta 4: Plata
    with col4:
        if df_silver is not None and len(df_silver) > 1:
            silver_price = df_silver['Price'].iloc[-1]
            silver_prev = df_silver['Price'].iloc[-2]
            silver_delta_pct = ((silver_price - silver_prev) / silver_prev) * 100
            st.metric("🥈 Plata (USD/oz)", f"${silver_price:,.2f}", f"{silver_delta_pct:+.2f}%")
        else:
            st.metric("🥈 Plata", "N/A", "0.00%")

    # Tarjeta 5: WTI
    with col5:
        if df_wti is not None and len(df_wti) > 1:
            wti_price = df_wti['Price'].iloc[-1]
            wti_prev = df_wti['Price'].iloc[-2]
            wti_delta_pct = ((wti_price - wti_prev) / wti_prev) * 100
            st.metric("🛢️ Petróleo WTI", f"${wti_price:,.2f}", f"{wti_delta_pct:+.2f}%")
        else:
            st.metric("🛢️ WTI", "N/A", "0.00%")

    # Tarjeta 6: Ratio Oro/Plata
    with col6:
        if df_gold is not None and df_silver is not None and not df_gold.empty and not df_silver.empty:
            merged_ratio = pd.merge(df_gold, df_silver, left_index=True, right_index=True, suffixes=('_gold', '_silver'))
            if not merged_ratio.empty:
                current_ratio = merged_ratio['Price_gold'].iloc[-1] / merged_ratio['Price_silver'].iloc[-1]
                st.metric("⚖️ Ratio Oro / Plata", f"{current_ratio:.2f}", "Ratio actual")
            else:
                st.metric("⚖️ Ratio Oro / Plata", "N/A", "N/A")
        else:
            st.metric("⚖️ Ratio Oro / Plata", "N/A", "N/A")

    st.markdown("---")
    st.markdown("### 📉 Resumen del Mercado")

    if df_stock_ibm is not None:
        fig_home = go.Figure()
        fig_home.add_trace(go.Scatter(
            x=df_stock_ibm.index,
            y=df_stock_ibm['Close'],
            mode='lines',
            name='IBM Close Price',
            line=dict(color='#1E88E5', width=2.5)
        ))
        fig_home.update_layout(
            title="Tendencia Reciente del Mercado (IBM)",
            xaxis_title="Fecha",
            yaxis_title="Precio USD ($)",
            hovermode="x unified",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_home, use_container_width=True)
    elif err_ibm:
        st.info(err_ibm)

    st.info("💡 **Acerca de esta plataforma:** Esta plataforma permite consultar y analizar datos financieros reales utilizando la API de Alpha Vantage.")
    st.warning("⚠️ **Aviso:** Esta aplicación tiene fines educativos y no constituye asesoramiento financiero.")

# ==============================================================================
# 2. PÁGINA: 📈 ACCIONES
# ==============================================================================
elif pagina_seleccionada == "📈 Acciones":
    st.title("📈 Análisis de Acciones")
    st.markdown("Consulta cotizaciones en tiempo real, tendencias diarias, semanales y velas mensuales OHLC.")
    st.markdown("---")

    col_simbolo, col_periodo, col_refresh = st.columns([2, 2, 1])

    with col_simbolo:
        simbolos_populares = ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
        simbolo_input = st.selectbox("Seleccionar acción (o escribe un ticker):", simbolos_populares, index=0)
        simbolo_custom = st.text_input("O ingresar símbolo personalizado (ej: Meta, NFLX):", value="").strip().upper()
        symbol = simbolo_custom if simbolo_custom else simbolo_input

    with col_periodo:
        periodo = st.radio("Frecuencia temporal:", ["Diario", "Semanal", "Mensual"], horizontal=True)

    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.success("Caché actualizada")

    with st.spinner(f"Obteniendo datos de {symbol}..."):
        if periodo == "Diario":
            df_data, err = get_stock_daily(symbol)
        elif periodo == "Semanal":
            df_data, err = get_stock_weekly(symbol)
        else:
            df_data, err = get_stock_monthly(symbol)

    if err:
        st.error(err)
    elif df_data is not None and not df_data.empty:
        # Métricas principales
        ultimo = df_data.iloc[-1]
        anterior = df_data.iloc[-2] if len(df_data) > 1 else ultimo
        
        c_price = ultimo['Close']
        c_change = c_price - anterior['Close']
        c_change_pct = (c_change / anterior['Close']) * 100 if anterior['Close'] != 0 else 0

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("💰 Precio Actual", f"${c_price:,.2f}", f"{c_change_pct:+.2f}%")
        m2.metric("🔓 Apertura", f"${ultimo['Open']:,.2f}")
        m3.metric("📈 Máximo", f"${ultimo['High']:,.2f}")
        m4.metric("📉 Mínimo", f"${ultimo['Low']:,.2f}")
        m5.metric("🔒 Cierre", f"${ultimo['Close']:,.2f}")
        m6.metric("📊 Volumen", f"{int(ultimo['Volume']):,}")

        st.markdown("---")

        # Gráficos según período
        if periodo == "Diario":
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(
                x=df_data.index, y=df_data['Close'], mode='lines', name='Precio Cierre',
                line=dict(color='#1E88E5', width=2)
            ), row=1, col=1)
            fig.add_trace(go.Bar(
                x=df_data.index, y=df_data['Volume'], name='Volumen',
                marker_color='#94A3B8'
            ), row=2, col=1)
            fig.update_layout(title=f'Precio Diario y Volumen - {symbol}', template='plotly_white', height=550, hovermode='x unified')

        elif periodo == "Semanal":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_data.index, y=df_data['Close'], mode='lines+markers', name='Cierre Semanal',
                line=dict(color='#F59E0B', width=2.5), marker=dict(size=4)
            ))
            fig.update_layout(title=f'Evolución Semanal de Precio - {symbol}', yaxis_title='Precio USD ($)', template='plotly_white', height=500, hovermode='x unified')

        else: # Mensual (Velas Japonesas OHLC)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            fig.add_trace(go.Candlestick(
                x=df_data.index, open=df_data['Open'], high=df_data['High'],
                low=df_data['Low'], close=df_data['Close'], name='OHLC Mensual'
            ), row=1, col=1)
            fig.add_trace(go.Bar(
                x=df_data.index, y=df_data['Volume'], name='Volumen', marker_color='#38BDF8'
            ), row=2, col=1)
            fig.update_layout(title=f'Análisis Mensual (Velas Japonesas OHLC) - {symbol}', template='plotly_white', height=600)
            fig.update_xaxes(rangeslider_visible=False, row=1, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Tabla de últimos registros
        with st.expander(f"📋 Ver tabla de registros históricos ({periodo})"):
            df_display = df_data.sort_index(ascending=False).copy()
            st.dataframe(df_display.style.format("{:,.2f}", subset=['Open', 'High', 'Low', 'Close']).format("{:,.0f}", subset=['Volume']), use_container_width=True)

# ==============================================================================
# 3. PÁGINA: 📊 ANÁLISIS TÉCNICO
# ==============================================================================
elif pagina_seleccionada == "📊 Análisis técnico":
    st.title("📊 Análisis Técnico")
    st.markdown("Indicadores de momentum y volatilidad: **RSI** y **Bandas de Bollinger**.")
    st.markdown("---")

    symbol = st.selectbox("Seleccionar acción para análisis:", ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"], index=0)

    tab_rsi, tab_bb = st.tabs(["📉 RSI (Relative Strength Index)", "📊 Bandas de Bollinger"])

    # --------------------------------------------------------------------------
    # SUBTAB: RSI
    # --------------------------------------------------------------------------
    with tab_rsi:
        st.subheader("Índice de Fuerza Relativa (RSI)")
        
        with st.spinner(f"Calculando RSI para {symbol}..."):
            df_stock, err_s = get_stock_daily(symbol)
            df_rsi, err_r = get_rsi(symbol, time_period=14)

        if err_r or err_s:
            st.error(err_r or err_s)
        elif df_rsi is not None and df_stock is not None:
            # Alinear fechas
            df_comb = pd.merge(df_stock[['Close']], df_rsi[['RSI']], left_index=True, right_index=True, how='inner')
            
            if not df_comb.empty:
                rsi_actual = df_comb['RSI'].iloc[-1]

                c_metric, c_interpret = st.columns([1, 2])
                with c_metric:
                    st.metric("RSI Actual (14 días)", f"{rsi_actual:.2f}")

                with c_interpret:
                    if rsi_actual > 70:
                        st.markdown("<div class='badge-overbought'>⚠️ SOBRECOMPRA (> 70)</div>", unsafe_allow_html=True)
                        st.markdown("El activo se encuentra en zona de sobrecompra. Existe posibilidad de corrección a la baja o toma de ganancias.")
                    elif rsi_actual < 30:
                        st.markdown("<div class='badge-oversold'>🟢 SOBREVENTA (< 30)</div>", unsafe_allow_html=True)
                        st.markdown("El activo se encuentra en zona de sobreventa. Existe posibilidad de rebote al alza.")
                    else:
                        st.markdown("<div class='badge-neutral'>🔵 NEUTRAL (30 - 70)</div>", unsafe_allow_html=True)
                        st.markdown("El indicador RSI se encuentra dentro de su rango normal sin señales extremas.")

                # Gráfico interactivo
                fig_rsi = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.4])
                
                # Precio
                fig_rsi.add_trace(go.Scatter(
                    x=df_comb.index, y=df_comb['Close'], mode='lines', name='Precio',
                    line=dict(color='#1E88E5', width=2)
                ), row=1, col=1)

                # RSI
                fig_rsi.add_trace(go.Scatter(
                    x=df_comb.index, y=df_comb['RSI'], mode='lines', name='RSI',
                    line=dict(color='#EF4444', width=2)
                ), row=2, col=1)

                # Umbrales
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecompra (70)", row=2, col=1)
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobreventa (30)", row=2, col=1)

                fig_rsi.update_layout(title=f'Precio vs RSI - {symbol}', template='plotly_white', height=600, hovermode='x unified')
                fig_rsi.update_yaxes(range=[0, 100], row=2, col=1)

                st.plotly_chart(fig_rsi, use_container_width=True)

    # --------------------------------------------------------------------------
    # SUBTAB: BOLLINGER BANDS
    # --------------------------------------------------------------------------
    with tab_bb:
        st.subheader("Bandas de Bollinger (20 períodos, 2 Desviaciones Estándar)")

        with st.spinner(f"Calculando Bandas de Bollinger para {symbol}..."):
            df_stock, err_s = get_stock_daily(symbol)
            df_bb, err_bb = get_bollinger_bands(symbol, time_period=20, nbdevup=2, nbdevdn=2)

        if err_bb or err_s:
            st.error(err_bb or err_s)
        elif df_bb is not None and df_stock is not None:
            df_comb_bb = pd.merge(df_stock[['Close']], df_bb, left_index=True, right_index=True, how='inner')

            if not df_comb_bb.empty:
                upper_col = [c for c in df_comb_bb.columns if 'Upper' in c][0]
                middle_col = [c for c in df_comb_bb.columns if 'Middle' in c][0]
                lower_col = [c for c in df_comb_bb.columns if 'Lower' in c][0]

                precio_act = df_comb_bb['Close'].iloc[-1]
                up_val = df_comb_bb[upper_col].iloc[-1]
                mid_val = df_comb_bb[middle_col].iloc[-1]
                low_val = df_comb_bb[lower_col].iloc[-1]

                b1, b2, b3, b4 = st.columns(4)
                b1.metric("💰 Precio Actual", f"${precio_act:,.2f}")
                b2.metric("🔴 Banda Superior", f"${up_val:,.2f}")
                b3.metric("🟡 Banda Media", f"${mid_val:,.2f}")
                b4.metric("🟢 Banda Inferior", f"${low_val:,.2f}")

                st.markdown("<br>", unsafe_allow_html=True)
                if precio_act > up_val:
                    st.warning("⚠️ **Interpretación:** El precio actual está por encima de la banda superior (**Posible sobrecompra**).")
                elif precio_act < low_val:
                    st.success("🟢 **Interpretación:** El precio actual está por debajo de la banda inferior (**Posible sobreventa**).")
                else:
                    st.info("✅ **Interpretación:** El precio se mantiene dentro de las bandas de volatilidad esperadas.")

                # Gráfico Plotly
                fig_bb = go.Figure()

                # Banda Superior
                fig_bb.add_trace(go.Scatter(
                    x=df_comb_bb.index, y=df_comb_bb[upper_col], mode='lines', name='Banda Superior',
                    line=dict(color='#EF4444', width=1, dash='dash')
                ))

                # Banda Inferior
                fig_bb.add_trace(go.Scatter(
                    x=df_comb_bb.index, y=df_comb_bb[lower_col], mode='lines', name='Banda Inferior',
                    line=dict(color='#10B981', width=1, dash='dash'),
                    fill='tonexty', fillcolor='rgba(226, 232, 240, 0.4)'
                ))

                # Banda Media
                fig_bb.add_trace(go.Scatter(
                    x=df_comb_bb.index, y=df_comb_bb[middle_col], mode='lines', name='Banda Media (SMA 20)',
                    line=dict(color='#F59E0B', width=1.5)
                ))

                # Precio
                fig_bb.add_trace(go.Scatter(
                    x=df_comb_bb.index, y=df_comb_bb['Close'], mode='lines', name='Precio',
                    line=dict(color='#1E88E5', width=2.5)
                ))

                fig_bb.update_layout(title=f'Bandas de Bollinger - {symbol}', yaxis_title='Precio USD ($)', template='plotly_white', height=550, hovermode='x unified')
                st.plotly_chart(fig_bb, use_container_width=True)

# ==============================================================================
# 4. PÁGINA: 🥇 COMMODITIES
# ==============================================================================
elif pagina_seleccionada == "🥇 Commodities":
    st.title("🥇 Análisis de Commodities")
    st.markdown("Seguimiento de precios de materias primas principales: **Oro**, **Plata** y **Petróleo WTI**.")
    st.markdown("---")

    with st.spinner("Consultando commodities..."):
        df_gold, err_g = get_gold()
        df_silver, err_s = get_silver()
        df_wti, err_w = get_wti()

    c_g, c_s, c_w = st.columns(3)

    with c_g:
        if df_gold is not None and not df_gold.empty:
            p_g = df_gold['Price'].iloc[-1]
            p_g_prev = df_gold['Price'].iloc[-2] if len(df_gold) > 1 else p_g
            delta_g = ((p_g - p_g_prev) / p_g_prev) * 100
            st.metric("🥇 Oro (USD/oz)", f"${p_g:,.2f}", f"{delta_g:+.2f}%")
        else:
            st.metric("🥇 Oro", "N/A")

    with c_s:
        if df_silver is not None and not df_silver.empty:
            p_s = df_silver['Price'].iloc[-1]
            p_s_prev = df_silver['Price'].iloc[-2] if len(df_silver) > 1 else p_s
            delta_s = ((p_s - p_s_prev) / p_s_prev) * 100
            st.metric("🥈 Plata (USD/oz)", f"${p_s:,.2f}", f"{delta_s:+.2f}%")
        else:
            st.metric("🥈 Plata", "N/A")

    with c_w:
        if df_wti is not None and not df_wti.empty:
            p_w = df_wti['Price'].iloc[-1]
            p_w_prev = df_wti['Price'].iloc[-2] if len(df_wti) > 1 else p_w
            delta_w = ((p_w - p_w_prev) / p_w_prev) * 100
            st.metric("🛢️ Petróleo WTI", f"${p_w:,.2f}", f"{delta_w:+.2f}%")
        else:
            st.metric("🛢️ WTI", "N/A")

    st.markdown("---")

    # Comparación Oro vs Plata
    st.subheader("⚖️ Comparación: Oro vs Plata")
    if df_gold is not None and df_silver is not None and not df_gold.empty and not df_silver.empty:
        fig_gs = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=('Precio del Oro (USD/oz)', 'Precio de la Plata (USD/oz)'))
        
        fig_gs.add_trace(go.Scatter(x=df_gold.index, y=df_gold['Price'], mode='lines', name='Oro', line=dict(color='#EAB308', width=2)), row=1, col=1)
        fig_gs.add_trace(go.Scatter(x=df_silver.index, y=df_silver['Price'], mode='lines', name='Plata', line=dict(color='#94A3B8', width=2)), row=2, col=1)
        
        fig_gs.update_layout(template='plotly_white', height=550, hovermode='x unified')
        st.plotly_chart(fig_gs, use_container_width=True)

        # Ratio Oro / Plata
        df_gs_merged = pd.merge(df_gold, df_silver, left_index=True, right_index=True, suffixes=('_gold', '_silver'))
        if not df_gs_merged.empty:
            df_gs_merged['Ratio'] = df_gs_merged['Price_gold'] / df_gs_merged['Price_silver']
            ratio_actual = df_gs_merged['Ratio'].iloc[-1]
            st.info(f"📊 **Ratio Oro/Plata Actual:** **{ratio_actual:.2f}** (Indica cuántas onzas de plata se necesitan para comprar una onza de oro).")
    else:
        st.warning("⚠️ No se pudieron obtener ambos datos de Oro y Plata para el análisis comparativo.")

    st.markdown("---")
    st.subheader("🛢️ Petróleo WTI (Crude Oil)")
    if df_wti is not None and not df_wti.empty:
        fig_wti = go.Figure()
        fig_wti.add_trace(go.Scatter(
            x=df_wti.index, y=df_wti['Price'], mode='lines+markers', name='Petróleo WTI',
            line=dict(color='#0284C7', width=2), marker=dict(size=3)
        ))
        fig_wti.update_layout(title="Precio del Petróleo WTI (USD / Barril)", yaxis_title="Precio USD ($)", template="plotly_white", height=450, hovermode="x unified")
        st.plotly_chart(fig_wti, use_container_width=True)
    elif err_w:
        st.error(err_w)

# ==============================================================================
# 5. PÁGINA: 🔄 COMPARADOR
# ==============================================================================
elif pagina_seleccionada == "🔄 Comparador":
    st.title("🔄 Comparador de Activos")
    st.markdown("Compara rendimiento acumulado, correlación y métricas de volatilidad entre múltiples activos.")
    st.markdown("---")

    activos_disponibles = ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN", "Oro", "Plata", "Petróleo WTI"]
    seleccionados = st.multiselect("Seleccionar activos a comparar:", activos_disponibles, default=["IBM", "Oro", "Petróleo WTI"])

    if len(seleccionados) < 2:
        st.warning("⚠️ Selecciona al menos 2 activos para realizar la comparación.")
    else:
        with st.spinner("Cargando y procesando datos comparativos..."):
            df_comp = pd.DataFrame()

            for item in seleccionados:
                if item == "Oro":
                    df_item, _ = get_gold()
                    if df_item is not None and not df_item.empty:
                        df_comp['Oro'] = df_item['Price']
                elif item == "Plata":
                    df_item, _ = get_silver()
                    if df_item is not None and not df_item.empty:
                        df_comp['Plata'] = df_item['Price']
                elif item == "Petróleo WTI":
                    df_item, _ = get_wti()
                    if df_item is not None and not df_item.empty:
                        df_comp['WTI'] = df_item['Price']
                else:
                    df_item, _ = get_stock_daily(item)
                    if df_item is not None and not df_item.empty:
                        df_comp[item] = df_item['Close']

            # Limpiar nulos para alineación temporal
            df_comp = df_comp.dropna()

        if df_comp.empty or len(df_comp.columns) < 2:
            st.error("❌ No hay suficientes datos coincidentes para la muestra seleccionada.")
        else:
            # Calculate daily percentage returns
            df_returns = df_comp.pct_change().dropna()

            # 1. Rendimiento Acumulado
            st.subheader("1. 📈 Rendimiento Acumulado (%)")
            cum_returns = (1 + df_returns).cumprod() - 1

            fig_cum = go.Figure()
            for col in cum_returns.columns:
                fig_cum.add_trace(go.Scatter(
                    x=cum_returns.index, y=cum_returns[col] * 100, mode='lines', name=col,
                    line=dict(width=2.5)
                ))
            fig_cum.update_layout(
                title="Rendimiento Acumulado Relativo (%)",
                yaxis_title="Retorno Acumulado (%)",
                template="plotly_white",
                height=500,
                hovermode="x unified"
            )
            st.plotly_chart(fig_cum, use_container_width=True)

            st.markdown("---")
            col_corr, col_stats = st.columns([1, 1])

            # 2. Matriz de Correlación
            with col_corr:
                st.subheader("2. 🧩 Matriz de Correlación")
                corr_matrix = df_returns.corr()
                fig_corr = px.imshow(
                    corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title="Correlación de Retornos Diarios"
                )
                fig_corr.update_layout(height=450)
                st.plotly_chart(fig_corr, use_container_width=True)

            # 3. Estadísticas Financieras
            with col_stats:
                st.subheader("3. 📊 Estadísticas Financieras")
                stats_df = pd.DataFrame({
                    'Retorno Promedio Diálogo (%)': df_returns.mean() * 100,
                    'Volatilidad Diaria (%)': df_returns.std() * 100,
                    'Retorno Máximo (%)': df_returns.max() * 100,
                    'Retorno Mínimo (%)': df_returns.min() * 100
                })
                st.dataframe(stats_df.style.format("{:.2f}%"), use_container_width=True)

# ==============================================================================
# 6. PÁGINA: ℹ️ INFORMACIÓN Y DOCUMENTACIÓN
# ==============================================================================
elif pagina_seleccionada == "ℹ️ Información":
    st.title("ℹ️ Información y Documentación")
    st.markdown("Guía completa de indicadores, conceptos financieros y arquitectura del sistema.")
    st.markdown("---")

    with st.expander("🔑 ¿Qué es Alpha Vantage API?", expanded=True):
        st.markdown("""
        **Alpha Vantage** ofrece APIs gratuitas y premium para datos de mercado en tiempo real e históricos sobre acciones, forex, materias primas e indicadores técnicos.
        - **Límite Gratuito:** 5 solicitudes por minuto.
        - **Optimización de Caché:** Esta aplicación implementa `@st.cache_data` con expiración TTL para reducir peticiones innecesarias.
        """)

    with st.expander("📊 Indicadores Técnicos Explicados"):
        st.markdown("""
        ### 1. RSI (Índice de Fuerza Relativa)
        El RSI mide la velocidad y el cambio de los movimientos de precios en una escala de 0 a 100.
        - **Sobrecompra (> 70):** Indica que el precio ha subido de forma muy acelerada y podría experimentar una corrección.
        - **Sobreventa (< 30):** Indica que el activo ha sufrido caídas severas y podría aproximarse a un rebote.
        - **Neutral (30 - 70):** Rango de oscilación normal del precio.

        ### 2. Bandas de Bollinger
        Consisten en tres líneas: una media móvil simple (SMA de 20 períodos) y dos bandas de desviación estándar (arriba y abajo).
        - **Volatilidad:** Las bandas se ensanchan cuando la volatilidad aumenta y se contraen cuando disminuye.
        - **Toque de Banda Superior:** Posible nivel de sobrecompra o resistencia.
        - **Toque de Banda Inferior:** Posible nivel de sobreventa o soporte.
        """)

    with st.expander("🔄 Conceptos Comparativos"):
        st.markdown("""
        ### 1. Rendimiento Acumulado
        Muestra la ganancia o pérdida porcentual acumulada desde el inicio del período analizado:
        $$ R_{acumulado} = \\prod (1 + R_t) - 1 $$

        ### 2. Matriz de Correlación
        Mide la relación lineal entre los retornos de dos activos:
        - **+1.0:** Mueven exactamente en la misma dirección.
        - **0.0:** Sin correlación lineal.
        - **-1.0:** Se mueven en direcciones opuestas (útil para cobertura de riesgo).
        """)

    st.markdown("---")
    st.warning("⚠️ **Descargo de Responsabilidad (Disclaimer):** Este proyecto tiene fines exclusivamente educativos. No constituye asesoramiento financiero ni recomendación de inversión.")
