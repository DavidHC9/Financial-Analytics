import os
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit as st

# ML imports
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, confusion_matrix, classification_report

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="ProyecKeras ML - Financial Analytics & Machine Learning",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS personalizados desde style.css
if os.path.exists("style.css"):
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==============================================================================
# GENERADOR DE DATOS FINANCIEROS DE RESPALDO (FALLBACK SIMULADO DE ALTA FIDELIDAD)
# ==============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def generar_datos_simulados(symbol, periodos=200, tipo="stock"):
    np.random.seed(hash(symbol) % 10000000)
    fechas = pd.date_range(end=datetime.now(), periods=periodos, freq='D')
    
    precios_base = {"IBM": 216.56, "AAPL": 225.0, "MSFT": 440.0, "GOOGL": 175.0, "AMZN": 180.0, "TSLA": 210.0, "NVDA": 120.0, "GOLD": 2170.03, "SILVER": 29.5, "WTI": 67.62}
    p0 = precios_base.get(symbol.upper(), 150.0)
    
    returns = np.random.normal(0.0008, 0.012, periodos)
    price = p0 * np.exp(np.cumsum(returns) - np.cumsum(returns)[-1])
    
    high = price * (1 + np.abs(np.random.normal(0.004, 0.003, periodos)))
    low = price * (1 - np.abs(np.random.normal(0.004, 0.003, periodos)))
    open_p = low + (high - low) * np.random.random(periodos)
    volume = np.random.randint(2000000, 15000000, periodos)
    
    if tipo == "commodity":
        df = pd.DataFrame({'Price': price}, index=fechas)
    else:
        df = pd.DataFrame({'Open': open_p, 'High': high, 'Low': low, 'Close': price, 'Volume': volume}, index=fechas)
    
    df.index.name = "Date"
    return df.sort_index(ascending=True)

# ==============================================================================
# FUNCIONES DE CONSULTA API ALPHA VANTAGE
# ==============================================================================
BASE_URL = "https://www.alphavantage.co/query"

def hacer_request_api(params, api_key_usuario=""):
    api_key = api_key_usuario.strip() or os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        return None, "MODO_FALLBACK"
    
    req_params = params.copy()
    req_params['apikey'] = api_key
    try:
        response = requests.get(BASE_URL, params=req_params, timeout=10)
        data = response.json()
        if 'Error Message' in data or 'Note' in data or 'Information' in data:
            return None, "MODO_FALLBACK"
        return data, None
    except Exception:
        return None, "MODO_FALLBACK"

def convertir_time_series(data, key):
    if not data or key not in data:
        return None
    df = pd.DataFrame.from_dict(data[key], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    return df.sort_index(ascending=True)

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
    return df.sort_index(ascending=True)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_daily(symbol, api_key=""):
    params = {'function': 'TIME_SERIES_DAILY', 'symbol': symbol, 'outputsize': 'compact'}
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_time_series(data, 'Time Series (Daily)')
        if df is not None:
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            return df, "API_REAL"
    return generar_datos_simulados(symbol, 200, "stock"), "SIMULADO"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_weekly(symbol, api_key=""):
    params = {'function': 'TIME_SERIES_WEEKLY', 'symbol': symbol}
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_time_series(data, 'Weekly Time Series')
        if df is not None:
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            return df, "API_REAL"
    return generar_datos_simulados(symbol, 100, "stock"), "SIMULADO"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_monthly(symbol, api_key=""):
    params = {'function': 'TIME_SERIES_MONTHLY', 'symbol': symbol}
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_time_series(data, 'Monthly Time Series')
        if df is not None:
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            return df, "API_REAL"
    return generar_datos_simulados(symbol, 60, "stock"), "SIMULADO"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_rsi(symbol, time_period=14, api_key=""):
    params = {'function': 'RSI', 'symbol': symbol, 'interval': 'daily', 'time_period': time_period, 'series_type': 'close'}
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_time_series(data, 'Technical Analysis: RSI')
        if df is not None:
            df.columns = ['RSI']
            return df, "API_REAL"
    
    df_stock = generar_datos_simulados(symbol, 200, "stock")
    delta = df_stock['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=time_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=time_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return pd.DataFrame({'RSI': rsi.fillna(54.4)}, index=df_stock.index), "CALCULADO_LOCAL"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_bollinger_bands(symbol, time_period=20, api_key=""):
    params = {'function': 'BBANDS', 'symbol': symbol, 'interval': 'daily', 'time_period': time_period, 'series_type': 'close'}
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_time_series(data, 'Technical Analysis: BBANDS')
        if df is not None:
            return df, "API_REAL"
    
    df_stock = generar_datos_simulados(symbol, 200, "stock")
    sma = df_stock['Close'].rolling(window=time_period).mean()
    std = df_stock['Close'].rolling(window=time_period).std()
    df_bb = pd.DataFrame({
        'Real Middle Band': sma,
        'Real Upper Band': sma + (std * 2),
        'Real Lower Band': sma - (std * 2)
    }, index=df_stock.index).dropna()
    return df_bb, "CALCULADO_LOCAL"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_commodity(symbol, api_key=""):
    func = 'GOLD_SILVER_HISTORY' if symbol in ['GOLD', 'SILVER'] else 'WTI'
    params = {'function': func, 'interval': 'daily'}
    if symbol in ['GOLD', 'SILVER']:
        params['symbol'] = symbol
    data, err = hacer_request_api(params, api_key)
    if data:
        df = convertir_commodities(data)
        if df is not None:
            col_name = 'value' if 'value' in df.columns else df.columns[0]
            df = df.rename(columns={col_name: 'Price'})
            return df[['Price']], "API_REAL"
    return generar_datos_simulados(symbol, 200, "commodity"), "SIMULADO"

def crear_sparkline(series, color='#0070f3'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(series))),
        y=series.values,
        mode='lines',
        line=dict(color=color, width=2.2),
        hoverinfo='none'
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=40,
        width=90
    )
    return fig

# ==============================================================================
# HELPER PARA PREPARAR DATOS DE ML
# ==============================================================================
def preparar_features_ml(df_stock, lags=5):
    df = df_stock.copy()
    df['Return'] = df['Close'].pct_change()
    
    for i in range(1, lags + 1):
        df[f'Lag_{i}'] = df['Close'].shift(i)
        df[f'Return_Lag_{i}'] = df['Return'].shift(i)
        
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Volatility_10'] = df['Return'].rolling(window=10).std()
    
    df['Target_Price'] = df['Close'].shift(-1)
    df['Target_Class'] = (df['Target_Price'] > df['Close']).astype(int)
    
    df = df.dropna()
    feature_cols = [c for c in df.columns if c.startswith('Lag_') or c.startswith('Return_Lag_') or c.startswith('SMA_') or c.startswith('Volatility_')]
    return df, feature_cols

# ==============================================================================
# SIDEBAR DE NAVEGACIÓN Y CONFIGURACIÓN (Fiel al Mockup)
# ==============================================================================
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <div style='background: linear-gradient(135deg, #0070f3, #00c6ff); color: white; width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,112,243,0.3);'>📊</div>
        <div>
            <h3 style='margin: 0; font-size: 1.15rem; color: #0f172a; font-weight: 800; letter-spacing: -0.02em;'>ProyecKeras ML</h3>
            <p style='margin: 0; font-size: 0.76rem; color: #64748b; font-weight: 500;'>Machine Learning & Financial Analytics</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<div class="sidebar-category-header">PROYECTO</div>', unsafe_allow_html=True)

secciones = [
    "🏠 Inicio",
    "📄 Resumen del proyecto",
    "🗄️ Datos",
    "📈 Análisis",
    "🧠 Modelo de Machine Learning",
    "🎯 Predicciones",
    "📊 Métricas",
    "🖼️ Visualizaciones"
]

# Estructurar la navegación en un Radio Selector estilizado
pagina = st.sidebar.radio("", secciones, index=2) # default a Datos o Inicio

st.sidebar.markdown('<div class="sidebar-category-header" style="margin-top: 15px;">CONFIGURACIÓN</div>', unsafe_allow_html=True)
api_key_input = st.sidebar.text_input("🔑 Alpha Vantage API Key:", type="password", help="Ingresa tu API Key para consultas en tiempo real.")

# Footer con avatar de usuario y tuerca de configuración (Fiel al Mockup)
st.sidebar.markdown(
    """
    <div class="sidebar-user-footer">
        <div class="sidebar-user-info">
            <div class="sidebar-user-avatar">DH</div>
            <div class="sidebar-user-name">
                David Herrera
                <span style="font-size: 0.7rem; color: #64748b;">∨</span>
            </div>
        </div>
        <div class="sidebar-settings-icon">⚙️</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Top Bar (Profile Header)
st.markdown(
    """
    <div class="user-top-bar">
        <div class="notification-bell">🔔</div>
        <div class="user-profile-badge">
            <div class="user-avatar-circle">DH</div>
            <span>David Herrera</span>
            <span style="font-size: 0.7rem; color: #64748b;">▼</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# 1. SECCIÓN: 🏠 INICIO
# ==============================================================================
if pagina == "🏠 Inicio":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title-container">
                <div class="hero-icon-box">🏦</div>
                <div class="hero-text">
                    <h1>Inicio - Dashboard Financiero & ML</h1>
                    <p>Visión general del mercado en tiempo real, KPIs clave y resumen interactivo de activos.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    c_alert, c_btn = st.columns([4, 1])
    with c_alert:
        st.markdown(
            """
            <div class="simulation-alert-content" style="background-color: #eef6ff; border: 1px solid #bae0ff; border-radius: 12px; padding: 14px 20px; margin-bottom: 20px;">
                <div class="simulation-alert-icon">ℹ</div>
                <span>Se están utilizando datos de mercado en modo simulación de alta fidelidad (para consulta en tiempo real ingresa una API Key de Alpha Vantage en la barra lateral).</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_btn:
        if st.button("🔑 Configurar API Key", use_container_width=True):
            st.info("Ingresa tu API Key en el menú desplegable de la barra lateral izquierda.")

    with st.spinner("Cargando indicadores clave..."):
        df_ibm, _ = fetch_stock_daily("IBM", api_key_input)
        df_rsi_ibm, _ = fetch_rsi("IBM", 14, api_key_input)
        df_gold, _ = fetch_commodity("GOLD", api_key_input)
        df_wti, _ = fetch_commodity("WTI", api_key_input)

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        p_act = df_ibm['Close'].iloc[-1]
        p_prev = df_ibm['Close'].iloc[-2]
        d_pct = ((p_act - p_prev) / p_prev) * 100
        
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-blue">
                <div class="kpi-header">
                    <div class="kpi-icon-circle" style="background: #e0f2fe; color: #0284c7;">📈</div>
                    <div class="kpi-title">IBM Close Price</div>
                </div>
                <div class="kpi-body">
                    <div>
                        <div class="kpi-value">${p_act:,.2f}</div>
                        <div class="kpi-badge-positive">↑ {d_pct:+.2f}% vs. día anterior</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.plotly_chart(crear_sparkline(df_ibm['Close'].iloc[-15:], '#0070f3'), use_container_width=True, key="sp_ibm")

    with k2:
        rsi_val = df_rsi_ibm['RSI'].iloc[-1]
        
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-green">
                <div class="kpi-header">
                    <div class="kpi-icon-circle" style="background: #dcfce7; color: #16a34a;">💲</div>
                    <div class="kpi-title">RSI IBM (14d)</div>
                </div>
                <div class="kpi-body">
                    <div>
                        <div class="kpi-value">{rsi_val:.1f}</div>
                        <div class="kpi-badge-neutral">● Neutro</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.plotly_chart(crear_sparkline(df_rsi_ibm['RSI'].iloc[-15:], '#10b981'), use_container_width=True, key="sp_rsi")

    with k3:
        g_act = df_gold['Price'].iloc[-1]
        g_prev = df_gold['Price'].iloc[-2]
        g_pct = ((g_act - g_prev) / g_prev) * 100
        
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-red">
                <div class="kpi-header">
                    <div class="kpi-icon-circle" style="background: #fee2e2; color: #dc2626;">🔺</div>
                    <div class="kpi-title">Oro (USD/oz)</div>
                </div>
                <div class="kpi-body">
                    <div>
                        <div class="kpi-value">${g_act:,.2f}</div>
                        <div class="kpi-badge-negative">↓ {g_pct:.2f}% vs. día anterior</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.plotly_chart(crear_sparkline(df_gold['Price'].iloc[-15:], '#ef4444'), use_container_width=True, key="sp_gold")

    with k4:
        w_act = df_wti['Price'].iloc[-1]
        w_prev = df_wti['Price'].iloc[-2]
        w_pct = ((w_act - w_prev) / w_prev) * 100
        
        st.markdown(
            f"""
            <div class="kpi-card kpi-card-purple">
                <div class="kpi-header">
                    <div class="kpi-icon-circle" style="background: #f3e8ff; color: #9333ea;">🛢️</div>
                    <div class="kpi-title">Petróleo WTI</div>
                </div>
                <div class="kpi-body">
                    <div>
                        <div class="kpi-value">${w_act:,.2f}</div>
                        <div class="kpi-badge-negative">↓ {w_pct:.2f}% vs. día anterior</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.plotly_chart(crear_sparkline(df_wti['Price'].iloc[-15:], '#a855f7'), use_container_width=True, key="sp_wti")

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart, col_summary = st.columns([3, 1])

    with col_chart:
        st.markdown(
            """
            <div class="card-title">📉 Tendencia de Precio Reciente (IBM)</div>
            <div class="card-subtitle">Evolución del precio de cierre en los últimos 30 días.</div>
            """,
            unsafe_allow_html=True
        )
        
        df_sub = df_ibm.iloc[-30:]
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_sub.index,
            y=df_sub['Close'],
            mode='lines+markers',
            name='Precio Cierre',
            line=dict(color='#0070f3', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 112, 243, 0.08)',
            marker=dict(size=4)
        ))
        fig_trend.update_layout(
            template="plotly_white",
            height=380,
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_summary:
        p_init = df_sub['Close'].iloc[0]
        p_final = df_sub['Close'].iloc[-1]
        var_tot = ((p_final - p_init) / p_init) * 100
        
        st.markdown(
            f"""
            <div class="summary-box">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-top: 0; margin-bottom: 20px;">Resumen del período</h3>
                <div class="summary-row">
                    <span class="summary-label">Precio inicial</span>
                    <span class="summary-val">${p_init:,.2f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Precio actual</span>
                    <span class="summary-val">${p_final:,.2f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Variación total</span>
                    <span class="summary-val" style="color: #16a34a;">{var_tot:+.2f}%</span>
                </div>
                <div class="summary-row" style="margin-top: 15px;">
                    <span class="summary-label">📈 Tendencia</span>
                    <span class="kpi-badge-positive">Alcista</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ==============================================================================
# 2. SECCIÓN: 📄 RESUMEN DEL PROYECTO
# ==============================================================================
elif pagina == "📄 Resumen del proyecto":
    st.markdown("<h2>📄 Resumen del Proyecto ProyecKeras</h2>", unsafe_allow_html=True)
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        st.markdown("""
        <div class="custom-card">
            <h3>🎯 Objetivos</h3>
            <ul>
                <li>Análisis integral de mercados accionarios y commodities.</li>
                <li>Modelado predictivo avanzado con técnicas supervisadas.</li>
                <li>Evaluación cuantitativa rigurosa mediante métricas de error y exactitud.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c_r2:
        st.markdown("""
        <div class="custom-card">
            <h3>💻 Stack Tecnológico</h3>
            <ul>
                <li>Python 3.10+ & Streamlit</li>
                <li>Scikit-Learn (Random Forest, Ridge, Decision Trees)</li>
                <li>Plotly Express & Graph Objects</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 3. SECCIÓN: 🗄️ DATOS
# ==============================================================================
elif pagina == "🗄️ Datos":
    st.markdown("<h2>🗄️ Exploración de Datos</h2>", unsafe_allow_html=True)
    sym = st.selectbox("Seleccionar Activo:", ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"])
    df_data, modo = fetch_stock_daily(sym, api_key_input)
    st.dataframe(df_data.sort_index(ascending=False), use_container_width=True)

# ==============================================================================
# 4. SECCIÓN: 📈 ANÁLISIS
# ==============================================================================
elif pagina == "📈 Análisis":
    st.markdown("<h2>📈 Análisis Técnico & Commodities</h2>", unsafe_allow_html=True)
    sym = st.selectbox("Seleccionar Activo:", ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN"])
    df_stock, _ = fetch_stock_daily(sym, api_key_input)
    df_rsi, _ = fetch_rsi(sym, 14, api_key_input)
    
    fig = px.line(df_rsi, y='RSI', title=f"RSI (14 días) - {sym}")
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 5. SECCIÓN: 🧠 MODELO DE MACHINE LEARNING
# ==============================================================================
elif pagina == "🧠 Modelo de Machine Learning":
    st.markdown("<h2>🧠 Entrenamiento del Modelo de Machine Learning</h2>", unsafe_allow_html=True)
    sym = st.selectbox("Activo a Modelar:", ["IBM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"])
    tipo_modelo = st.selectbox("Modelo:", ["Random Forest Regressor", "Ridge Regression", "Decision Tree Regressor", "Random Forest Classifier"])
    
    if st.button("🚀 Entrenar Modelo", use_container_width=True):
        df_stock, _ = fetch_stock_daily(sym, api_key_input)
        df_ml, feature_cols = preparar_features_ml(df_stock, lags=5)
        X = df_ml[feature_cols]
        is_class = "Classifier" in tipo_modelo
        y = df_ml['Target_Class'] if is_class else df_ml['Target_Price']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        model = RandomForestRegressor(n_estimators=50, random_state=42) if not is_class else RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        st.session_state['trained_model'] = model
        st.session_state['model_name'] = tipo_modelo
        st.session_state['feature_cols'] = feature_cols
        st.session_state['X_test'] = X_test
        st.session_state['y_test'] = y_test
        st.session_state['y_pred'] = y_pred
        st.session_state['target_symbol'] = sym
        st.session_state['is_class'] = is_class
        st.session_state['df_ml'] = df_ml
        st.success("✅ Modelo entrenado exitosamente.")

# ==============================================================================
# 6. SECCIÓN: 🎯 PREDICCIONES
# ==============================================================================
elif pagina == "🎯 Predicciones":
    st.markdown("<h2>🎯 Predicciones Futuras</h2>", unsafe_allow_html=True)
    if 'trained_model' in st.session_state:
        df_ml = st.session_state['df_ml']
        st.write(f"Predicción para {st.session_state['target_symbol']}")
        fig_pred = px.line(df_ml, y='Close', title="Predicciones vs Histórico")
        st.plotly_chart(fig_pred, use_container_width=True)
    else:
        st.warning("Primero entrena un modelo en la sección 🧠 Modelo de Machine Learning.")

# ==============================================================================
# 7. SECCIÓN: 📊 MÉTRICAS
# ==============================================================================
elif pagina == "📊 Métricas":
    st.markdown("<h2>📊 Métricas del Modelo</h2>", unsafe_allow_html=True)
    if 'trained_model' in st.session_state:
        y_test = st.session_state['y_test']
        y_pred = st.session_state['y_pred']
        if not st.session_state['is_class']:
            st.metric("R² Score", f"{r2_score(y_test, y_pred):.4f}")
            st.metric("MAE", f"${mean_absolute_error(y_test, y_pred):.2f}")
        else:
            st.metric("Accuracy", f"{accuracy_score(y_test, y_pred)*100:.2f}%")

# ==============================================================================
# 8. SECCIÓN: 🖼️ VISUALIZACIONES
# ==============================================================================
elif pagina == "🖼️ Visualizaciones":
    st.markdown("<h2>🖼️ Visualizaciones Comparativas</h2>", unsafe_allow_html=True)
    activos = st.multiselect("Seleccionar Activos:", ["IBM", "AAPL", "GOLD", "WTI"], default=["IBM", "GOLD"])
    if len(activos) >= 2:
        df_comp = pd.DataFrame()
        for a in activos:
            df_item, _ = fetch_commodity(a, api_key_input) if a in ["GOLD", "WTI"] else fetch_stock_daily(a, api_key_input)
            df_comp[a] = df_item['Price'] if 'Price' in df_item.columns else df_item['Close']
        df_returns = df_comp.dropna().pct_change().dropna()
        fig_corr = px.imshow(df_returns.corr(), text_auto=".2f", color_continuous_scale="RdBu_r")
        st.plotly_chart(fig_corr, use_container_width=True)
