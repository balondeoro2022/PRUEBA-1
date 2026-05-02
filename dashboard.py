import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página
st.set_page_config(page_title="Dashboard MiniPlanta", layout="wide")

st.title("📊 Dashboard de Mantenimiento Local: Mini Planta")

@st.cache_data
def cargar_datos():
    # Nombre exacto del archivo que tienes en tu carpeta
    archivo = "Analisis_Estadistico_MiniPlanta (1).xlsx"
    # Se carga la hoja 'Base_Datos_Integrada'
    df = pd.read_excel(archivo, sheet_name='Base_Datos_Integrada')
    return df

try:
    df = cargar_datos()

    # Filtro lateral interactivo
    st.sidebar.header("Controles de Usuario")
    proceso_sel = st.sidebar.multiselect(
        "Selecciona los Procesos a visualizar:", 
        df['proceso'].unique(), 
        default=df['proceso'].unique()
    )

    # Filtrar el dataframe según la selección
    df_filtrado = df[df['proceso'].isin(proceso_sel)]

    # Crear columnas para organizar el dashboard
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### Resumen de la Base de Datos")
        st.dataframe(df_filtrado)

    with col2:
        st.write("### Distribución de Fallas por Sensor")
        if not df_filtrado.empty:
            fig, ax = plt.subplots()
            sns.countplot(data=df_filtrado, x='sensor', ax=ax, palette='magma')
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("Selecciona al menos un proceso para ver la gráfica.")

    # Sección adicional: Estadísticas rápidas
    st.write("--- ")
    st.write("### Estadísticas por Sensor")
    resumen = df_filtrado.groupby('sensor')['valor_detectado'].agg(['mean', 'std', 'min', 'max']).rename(columns={'mean': 'Media', 'std': 'Desv. Est.', 'min': 'Mínimo', 'max': 'Máximo'})
    st.table(resumen)

except Exception as e:
    st.error(f"No se pudo cargar el archivo: {e}")
    st.info("Recuerda que el archivo Excel debe llamarse 'Analisis_Estadistico_MiniPlanta (1).xlsx' y estar en la misma carpeta que este script.")
