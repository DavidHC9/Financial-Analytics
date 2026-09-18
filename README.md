# 📊 Financial Analytics & Machine Learning: ProyecKeras

url de streamlit : https://parcial-1-introduccion-a-machine-learning-yppy9qxqtofvnokbkwds.streamlit.app

![Python](https://img.shields.io/badge/python-3.10%2B-106EBE?style=flat-square&logo=python&logoColor=white) ![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?style=flat-square&logo=scikit-learn&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=flat-square&logo=pandas&logoColor=white) ![Methodology](https://img.shields.io/badge/Methodology-CRISP--ML-purple?style=flat-square)

Una plataforma profesional e interactiva de análisis financiero y Machine Learning diseñada para monitorear activos de mercado, evaluar indicadores técnicos y entrenar modelos predictivos bursátiles bajo la metodología industrial estándar **CRISP-ML(Q)**.

---

## 📁 Estructura del Proyecto

El repositorio está estructurado de la siguiente forma:

```text
ProyecKeras/
│
├── .github/
│   └── workflows/
│       └── ci.yml             # Workflow de Integración Continua (CI)
├── .gitignore                 # Configuración de archivos ignorados
├── LICENSE                    # Licencia del proyecto (MIT)
├── README.md                  # Documentación oficial del proyecto
├── app.py                     # Aplicación principal de Streamlit
├── index.html                 # Portal web de presentación y documentación
├── requirements.txt           # Lista de dependencias en Python
└── style.css                  # Hoja de estilos visuales personalizada
```

---

## 🎯 Descripción y Objetivos

El objetivo principal de **ProyecKeras** es integrar en un único entorno interactivo herramientas de análisis técnico cuantitativo, visualizaciones dinámicas de mercado e ingeniería de características para el entrenamiento y evaluación de modelos predictivos.

La aplicación permite:
- **Consultar cotizaciones** y datos históricos de acciones (*IBM, AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA*) y materias primas (*Oro, Plata, Petróleo WTI*).
- **Analizar indicadores técnicos** como el **RSI (Índice de Fuerza Relativa)**, **Bandas de Bollinger** y ratios de materias primas.
- **Entrenar modelos de Machine Learning** supervisados (*Random Forest Regressor/Classifier*, *Ridge Regression*, *Decision Trees*).
- **Proyectar precios futuros** y tendencias a $N$ días con escenarios simulados (Optimista, Base, Pesimista).
- **Evaluar métricas cuantitativas** ($R^2$, RMSE, MAE, Exactitud, Matriz de Confusión e Importancia de Características).

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje Principal:** Python 3.10+
- **Dashboard Interactivo:** [Streamlit](https://streamlit.io/) (v1.30.0+)
- **Machine Learning:** [Scikit-Learn](https://scikit-learn.org/)
- **Procesamiento de Datos:** Pandas, NumPy
- **Visualización:** Plotly Express, Plotly Graph Objects
- **APIs & Ingestión de Datos:** Alpha Vantage API (con generador sintético de respaldo automático)
- **CI / CD:** GitHub Actions

---

## ⚙️ Instalación y Ejecución Local

### 1. Requisitos Previos
Tener instalado Python 3.10+ y Git.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/ProyecKeras.git
cd ProyecKeras
```

### 3. Crear y Activar Entorno Virtual
- **Windows:**
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Ejecutar la Aplicación Localmente
Para iniciar la plataforma interactiva de Streamlit:

```bash
streamlit run app.py
```

> 💡 **Nota en Windows:** Si la consola indica que `streamlit` no se reconoce como un comando, puedes ejecutar alternativamente:
```bash
python -m streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`.

---

## 🤖 Información sobre el Modelo de Machine Learning

El módulo de Machine Learning en `app.py` permite construir y personalizar modelos predictivos:

1. **Ingeniería de Características:** Retardos ($Lag_1 \dots Lag_n$), retornos porcentuales, medias móviles ($SMA_5$, $SMA_{20}$) y volatilidad rodante.
2. **Modelos Disponibles:** Random Forest (Regresión y Clasificación), Ridge Regression y Árboles de Decisión.
3. **Métricas de Evaluación:** MAE, RMSE, $R^2$, Exactitud, Matriz de Confusión y Gráficos de Importancia de Variables.

---

## 🔮 Predicciones y Proyecciones

El módulo de predicción permite generar proyecciones iterativas hacia el futuro:
- **Precios Proyectados:** Estimación puntual basada en el modelo entrenado.
- **Escenarios de Riesgo:** Banda superior (+2% u optimista) y banda inferior (-2% o pesimista).
- **Visualización:** Gráficos comparativos entre la serie histórica reciente y la proyección futura.

---

## 🚀 Instrucciones de Despliegue

> [!IMPORTANT]
> **GitHub Pages vs Streamlit:**
> GitHub Pages solo aloja sitios web estáticos como `index.html`. Para ejecutar aplicaciones interactivas de Streamlit se requiere un entorno de ejecución servidor en Python.

Para desplegar la aplicación en la nube:
1. **Streamlit Community Cloud (Recomendado):** Sube el repositorio a GitHub, conecta en [share.streamlit.io](https://share.streamlit.io/) y selecciona `app.py`.
2. **Docker / Railway / Render:** Compatible con el ejecutable `streamlit run app.py --server.port $PORT`.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
