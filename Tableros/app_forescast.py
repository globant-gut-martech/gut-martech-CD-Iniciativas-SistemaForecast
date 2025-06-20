import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from google.cloud import bigquery
from google.oauth2 import service_account
import json

# ---------- AUTENTICACIÓN CON GOOGLE CLOUD ----------
# Leer credenciales desde st.secrets
clave_json_str = st.secrets["GCP_SERVICE_ACCOUNT"]
repo_str = st.secrets["REPOSITORIOS"]
clave_dict = json.loads(clave_json_str)
repo_json = json.loads(repo_str)
credenciales = service_account.Credentials.from_service_account_info(clave_dict)

# Crear cliente BigQuery
client = bigquery.Client(credentials=credenciales, project=credenciales.project_id)

st.set_page_config(page_title="Visualización de Impresiones", layout="wide")


# ---------- FUNCIONES DE CARGA Y VISUALIZACIÓN ----------

def cargar_datos(query):
    """Cargar datos desde BigQuery con credenciales autenticadas."""
    datos = client.query(query).to_dataframe()
    return datos


def cargar_datos_y_visualizar(modelo_seleccionado):
    if modelo_seleccionado == "Prophet":
        query_df = repo_json["entrenamiento_prophet"]
        df = cargar_datos(query_df)
        query_dp = repo_json["prediccion_prophet"]
        dp = cargar_datos(query_dp)
    else:
        query_df = repo_json["entrenamiento_xgboost"]
        df = cargar_datos(query_df)
        query_dp = repo_json["prediccion_xgboost"]
        dp = cargar_datos(query_dp)

    if df.empty:
        st.write("El archivo está vacío. Por favor, verifica el contenido.")
        return

    df['Date'] = pd.to_datetime(df['Date'])

    st.sidebar.header('Filtros')

    campanas = df['Campaign'].unique()
    campana_seleccionada = st.sidebar.selectbox('Selecciona una Campaña', campanas)

    df_filtrado = df[df['Campaign'] == campana_seleccionada]

    

    sets = df['Set'].unique().tolist()
    sets.append("Ninguno")
    if "Future" not in sets:
        sets.append("Future")
    set_seleccionado = st.sidebar.selectbox('Selecciona un Set', sets, index=sets.index("Ninguno"))
    
    if set_seleccionado != "Future":
        fecha_inicio_default = df_filtrado['Date'].min() if not df_filtrado.empty else df['Date'].min()
        fecha_fin_default = df_filtrado['Date'].max() if not df_filtrado.empty else df['Date'].max()
    else:
        fecha_inicio_default = dp['Date'].min()
        fecha_fin_default = dp['Date'].max()
    
    fecha_inicio = st.sidebar.date_input('Fecha de Inicio', value=fecha_inicio_default)
    fecha_fin = st.sidebar.date_input('Fecha de Fin', value=fecha_fin_default)
    
    
    df_filtrado = df_filtrado[
        (df_filtrado['Date'] >= pd.to_datetime(fecha_inicio)) &
        (df_filtrado['Date'] <= pd.to_datetime(fecha_fin))
    ]
    if set_seleccionado != "Ninguno":
        df_filtrado = df_filtrado[(df_filtrado['Set'] == set_seleccionado)]

    frecuencia = st.sidebar.selectbox('Selecciona la Frecuencia', ['Diario', 'Mensual'])

    if frecuencia == 'Mensual':
        df_filtrado.set_index('Date', inplace=True)
        df_agrupado = df_filtrado.resample('ME').agg({
            'Real Impressions': 'sum',
            'Predicted Impressions': 'sum'
        }).reset_index()
        dp.set_index('Date', inplace=True)
        dp = dp.resample('ME').agg({
            'Lower Bound':'sum',
            'Predicción': 'sum',
            'Upper Bound': 'sum'
        }).reset_index()
    else:
        df_agrupado = df_filtrado
        
    print(df_agrupado.shape)
    #if not df_agrupado.empty or modelo_seleccionado == "Prophet":
    fig = go.Figure()
    if set_seleccionado != "Future":
        fig.add_trace(go.Scatter(x=df_agrupado['Date'], y=df_agrupado['Real Impressions'],
                                    mode='lines+markers', name='Impresiones Históricas', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df_agrupado['Date'], y=df_agrupado['Predicted Impressions'],
                                    mode='lines+markers', name='Predicción de Impresiones', line=dict(color='orange', dash='dash')))
    else:
        print(modelo_seleccionado)
        fig.add_trace(go.Scatter(x=dp['Date'], y=dp['Lower Bound'],
                                    mode='lines+markers', name='Limite inferior', line=dict(color='yellowgreen', dash='dash')))
        fig.add_trace(go.Scatter(x=dp['Date'], y=dp['Predicción'],
                                    mode='lines+markers', name='Predicción de Impresiones', line=dict(color='orange', dash='dash')))
        fig.add_trace(go.Scatter(x=dp['Date'], y=dp['Upper Bound'],
                                    mode='lines+markers', name='Limite superior', line=dict(color='mediumpurple', dash='dash')))

    fig.update_layout(
        title=f'Predicción de Impresiones para la Campaña: {campana_seleccionada}',
        xaxis_title='Fecha',
        yaxis_title='Impresiones',
        legend_title='Leyenda',
        height=600,
        width=4000,
        xaxis=dict(
            tickmode='array',
            tickvals=pd.date_range(start=fecha_inicio, end=fecha_fin,
                                    freq='2MS' if set_seleccionado != 'Future' else 'D'),
            ticktext=pd.date_range(start=fecha_inicio, end=fecha_fin,
                                    freq='2MS' if set_seleccionado != 'Future' else 'D').strftime(
                '%b %Y' if set_seleccionado != 'Future' else '%d %b')
        )
    )

    with st.container():
        st.plotly_chart(fig, use_container_width=True)
    #else:
        #st.write("No hay datos para mostrar con los filtros seleccionados.")


# ---------- UI PRINCIPAL ----------

st.sidebar.header('Seleccione un Modelo')
modelos = ["Prophet", "XGBoost"]
modelo_seleccionado = st.sidebar.selectbox('Seleccione un Modelo', modelos)

if modelo_seleccionado:
    cargar_datos_y_visualizar(modelo_seleccionado)
else:
    st.write("Por favor, seleccione un modelo para continuar.")
