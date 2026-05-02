import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard Analítico MiniPlanta", layout="wide")
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.figsize': (10, 6), 'font.size': 10})

st.title(" Dashboard Analítico Integral: Mini Planta Láctea")
st.markdown("--- ")

@st.cache_data
def cargar_datos():
    # 1. CARGAR ARCHIVO EXCEL
    archivo = "Analisis_Estadistico_MiniPlanta (1).xlsx"
    try:
        df = pd.read_excel(archivo, sheet_name='Base_Datos_Integrada')
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        return df
    except Exception as e:
        return e


df = cargar_datos()

if isinstance(df, Exception):
    st.error(f"❌ Error al cargar el archivo: {df}")
else:
    # 2. CALIDAD DE DATOS (Limpieza)
    st.sidebar.header("⚙️ Calidad de Datos")
    nulos = df['valor_detectado'].isnull().sum()
    if nulos > 0:
        # Limpieza por media de sensor para no sesgar magnitudes
        df['valor_detectado'] = df.groupby('sensor')['valor_detectado'].transform(lambda x: x.fillna(x.mean()))
        st.sidebar.warning(f"⚠️ {nulos} nulos corregidos por media de sensor.")
    else:
        st.sidebar.success("✅ Datos 100% limpios.")

    st.sidebar.header("Controles de Usuario")
    proceso_sel = st.sidebar.multiselect(
        "Selecciona los Procesos a visualizar:",
        df['proceso'].unique(),
        default=df['proceso'].unique()
    )

    # Filtrar el dataframe según la selección
    df_filtrado = df[df['proceso'].isin(proceso_sel)]

    # Pestañas para los puntos solicitados
    tab1, tab2, tab3 = st.tabs(["Estadística Descriptiva", "Tablas de Frecuencia", "Gráficos por Proceso"])

    # 3. ESTADÍSTICA DESCRIPTIVA
    with tab1:
        st.header("1. Resumen de la Base de Datos y Distribución de Fallas")
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

        st.markdown("---")
        st.write("### Estadísticas por Sensor")
        resumen = df_filtrado.groupby('sensor')['valor_detectado'].agg(['mean', 'std', 'min', 'max']).rename(columns={'mean': 'Media', 'std': 'Desv. Est.', 'min': 'Mínimo', 'max': 'Máximo'})
        st.table(resumen)

        st.markdown("---")
        st.subheader("Análisis de Medias, Máximos, Mínimos y Desviaciones")
        # 9 Desviaciones y medias diferentes (3 procesos x 3 sensores)
        stats = df_filtrado.groupby(['proceso', 'sensor'])['valor_detectado'].agg(['mean', 'max', 'min', 'std', 'count']).reset_index()
        stats.columns = ['Proceso', 'Sensor', 'Media', 'Máximo', 'Mínimo', 'Desv. Estándar', 'Nº Muestras']
        st.dataframe(stats.style.format({"Media": "{:.2f}", "Máximo": "{:.2f}", "Mínimo": "{:.2f}", "Desv. Estándar": "{:.2f}"}), use_container_width=True)

        st.subheader("Gráfica de Dispersión (Resumen Estadístico)")
        fig_box = plt.figure(figsize=(12, 5))
        sns.boxplot(data=df_filtrado, x='proceso', y='valor_detectado', hue='sensor', palette='Set2')
        plt.title("Dispersión de Lecturas por Proceso y Sensor")
        st.pyplot(fig_box)

    # 4. TABLAS DE FRECUENCIA
    with tab2:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver las tablas de frecuencia.")
        else:
            st.header("Tablas de Frecuencia y Distribución")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.subheader("4.1 Fallas por Proceso")
                f_proc = df_filtrado['proceso'].value_counts().reset_index()
                f_proc.columns = ['Proceso', 'Cant. Fallas']
                st.table(f_proc)
                
                fig_p = plt.figure(figsize=(5, 4))
                sns.barplot(data=f_proc, x='Proceso', y='Cant. Fallas', palette='viridis')
                st.pyplot(fig_p)

            with c2:
                st.subheader("4.2 Fallas por Sensor")
                f_sens = df_filtrado['sensor'].value_counts().reset_index()
                f_sens.columns = ['Sensor', 'Cant. Fallas']
                st.table(f_sens)
                
                fig_s = plt.figure(figsize=(5, 4))
                sns.countplot(data=df_filtrado, x='sensor', palette='magma')
                plt.xticks(rotation=45)
                st.pyplot(fig_s)

            with c3:
                st.subheader("4.3 Falla más Común")
                f_tipo = df_filtrado['tipo_falla'].value_counts().reset_index()
                f_tipo.columns = ['Tipo Falla', 'Frecuencia']
                st.table(f_tipo.head(5))
                
                fig_t = plt.figure(figsize=(5, 4))
                f_tipo.head(3).plot(kind='bar', x='Tipo Falla', y='Frecuencia', ax=plt.gca(), color='teal')
                st.pyplot(fig_t)

    # 5. GRÁFICOS DETALLADOS POR PROCESO
    with tab3:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver los gráficos por proceso.")
        else:
            st.header("Distribución Estadística por Proceso (Histogramas)")
            procesos = ["Dulce de Leche", "Pasteurizacion", "Queso"]
            sensores_config = [
                ("RTD_PT100", "Temperatura (°C)", "orange", 88.0, "Ebullición (~88°C)"),
                ("Manometro_Bourdon", "Presión (bar)", "red", 3.0, "Límite Seguro (3 bar)"),
                ("Nivel_Conductivo", "Nivel (%)", "blue", None, None)
            ]

            for proc in procesos:
                st.subheader(f"Proceso: {proc.upper()}")
                fig, axes = plt.subplots(1, 3, figsize=(18, 5))
                fig.suptitle(f'Histogramas de Frecuencia - {proc}', fontsize=16)
                
                for i, (sens, unit, col, limit, lab) in enumerate(sensores_config):
                    datos_f = df_filtrado[(df_filtrado['proceso'] == proc) & (df_filtrado['sensor'] == sens)]['valor_detectado']
                    sns.histplot(datos_f, bins='sturges', kde=True, color=col, ax=axes[i], edgecolor="black")
                    axes[i].set_title(f'{sens}')
                    axes[i].set_xlabel(unit)
                    
                    if limit and (sens == "Manometro_Bourdon" or (sens == "RTD_PT100" and proc == "Dulce de Leche")):
                        axes[i].axvline(limit, color='darkred', linestyle='--', linewidth=2, label=lab)
                        axes[i].legend()
                
                plt.tight_layout()
                plt.subplots_adjust(top=0.85)
                st.pyplot(fig)
                st.markdown("---")

