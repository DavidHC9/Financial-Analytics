# 📊 Financial Analytics - Dashboard Web con Streamlit

Una plataforma web interactiva y profesional para el análisis financiero de acciones, indicadores técnicos, commodities y análisis comparativo utilizando la API de **Alpha Vantage**, **Streamlit** y **Plotly**.

---

## 🚀 Características Principales

- **🏠 Dashboard Inicial:** Métricas principales del mercado en tiempo real (Precio IBM, RSI, Oro, Plata, Petróleo WTI, Ratio Oro/Plata).
- **📈 Análisis de Acciones:** Consulta de cotizaciones diarias, semanales y mensuales (con Velas Japonesas OHLC y volumen) para tickers populares (IBM, AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA) o cualquier símbolo personalizado.
- **📊 Análisis Técnico:** 
  - **RSI (14 períodos):** Indicador de sobrecompra/sobreventa con alertas visuales e interpretación automatizada.
  - **Bandas de Bollinger (20 períodos, 2 std dev):** Rango de volatilidad con gráfico interactivo y bandas sombreadas.
- **🥇 Commodities:** Precios históricos de Oro, Plata y Petróleo WTI, con gráfico de comparación "Oro vs Plata" y cálculo de Ratio Oro/Plata.
- **🔄 Comparador de Activos:** Evaluación del rendimiento acumulado porcentual, matriz de correlación de retornos y tabla estadística de volatilidad y retorno.
- **ℹ️ Sección Informativa:** Documentación educativa sobre los indicadores financieros y la API.

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.10+**
- **Streamlit** (Framework de interfaz de usuario)
- **Plotly** (Visualizaciones interactivas de alta calidad)
- **Pandas & NumPy** (Procesamiento y análisis de series temporales)
- **Requests** (Consumo de la REST API de Alpha Vantage)

---

## 📋 Requisitos Previos e Instalación

### 1. Clonar el repositorio o descargar el código
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd proyectofinanzas
```

### 2. Crear y activar un entorno virtual (recomendado)
En Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

En macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 🔑 Configuración de Alpha Vantage API & Streamlit Secrets

### Obtener API Key Gratuita
Consigue una API Key gratuita en [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key).

### Configurar Secrets para Desarrollo Local
Para ejecutar la aplicación localmente sin exponer tu clave en el código, crea la carpeta `.streamlit` y el archivo `secrets.toml`:

1. Crea la carpeta `.streamlit` en la raíz del proyecto (si no existe).
2. Dentro de `.streamlit/`, crea un archivo llamado `secrets.toml`.
3. Agrega la siguiente línea con tu clave:

```toml
ALPHA_VANTAGE_API_KEY = "TU_API_KEY_AQUI"
```

> **Nota:** El archivo `.streamlit/secrets.toml` ya está incluido en `.gitignore` para prevenir subir credenciales por accidente a GitHub.

---

## 💻 Ejecución Local

Ejecuta el servidor de desarrollo de Streamlit:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado en `http://localhost:8501`.

---

## ☁️ Despliegue en Streamlit Cloud

1. Sube tu proyecto a un repositorio de **GitHub** (asegúrate de **NO** incluir `.streamlit/secrets.toml`).
2. Ve a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **"New app"** y selecciona tu repositorio, rama (`main`) y archivo principal (`app.py`).
4. Antes de desplegar (o en la sección de Configuración de la App), dirígete a **Advanced settings -> Secrets** y añade tu clave:

```toml
ALPHA_VANTAGE_API_KEY = "TU_API_KEY_AQUI"
```

5. Haz clic en **Deploy**. ¡Tu aplicación estará en línea y lista para usarse!

---

## ⚠️ Limitaciones de la API Gratuita

La API gratuita de Alpha Vantage impone las siguientes restricciones:
- **Límite de Frecuencia:** Máximo 5 solicitudes por minuto.
- **Caché:** La aplicación implementa `@st.cache_data(ttl=300)` para almacenar en caché las respuestas durante 5 minutos y reducir drásticamente las solicitudes innecesarias.

---

## ⚠️ Disclaimer Financiero

Esta aplicación tiene fines exclusivamente educativos e informativos y no constituye asesoramiento ni recomendación financiera o de inversión.
