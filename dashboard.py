import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard Analítico MiniPlanta", layout="wide")
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.figsize': (10, 6), 'font.size': 10})

st.title("Dashboard Analítico Integral: Mini Planta Láctea")
st.markdown("---")

@st.cache_data
def cargar_datos():
    # 1. cargar el archivo de excel
    archivo = "Analisis_Estadistico_MiniPlanta (1).xlsx"
    try:
        df = pd.read_excel(archivo, sheet_name='Base_Datos_Integrada')
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        return df
    except Exception as e:
        return e


df = cargar_datos()

if isinstance(df, Exception):
    st.error(f"Error al cargar el archivo: {df}")
else:
    # 2. revisa la calidad de datos
    st.sidebar.header("Calidad de Datos")
    nulos = df['valor_detectado'].isnull().sum()
    if nulos > 0:
        df['valor_detectado'] = df.groupby('sensor')['valor_detectado'].transform(lambda x: x.fillna(x.mean()))
        st.sidebar.warning(f"{nulos} nulos corregidos por la media de cada sensor.")
    else:
        st.sidebar.success("Datos limpios.")

    st.sidebar.header("Controles de Usuario")
    proceso_sel = st.sidebar.multiselect("Selecciona los procesos a visualizar:", df['proceso'].unique(), default=df['proceso'].unique())

    # Filtrar el dataframe según la selección
    df_filtrado = df[df['proceso'].isin(proceso_sel)]

    # Pestañas para los puntos solicitados
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Estadística Descriptiva",
        "Tablas de Frecuencia",
        "Gráficos Básicos",
        "Análisis Avanzado",
        "Alertas Predictivas"
    ])

    # 3. ESTADÍSTICA DESCRIPTIVA
    with tab1:
        st.header("Resumen de la Base de Datos y Distribución de Fallas")
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
        resumen = df_filtrado.groupby('sensor')['valor_detectado'].agg(['mean', 'std', 'min', 'max']).rename(columns={
            'mean': 'Media', 'std': 'Desv. Est.', 'min': 'Mínimo', 'max': 'Máximo'
        })
        st.table(resumen)

        st.markdown("---")
        st.subheader("Análisis de Medias, Máximos, Mínimos y Desviaciones")
        stats = df_filtrado.groupby(['proceso', 'sensor'])['valor_detectado'].agg(['mean', 'max', 'min', 'std', 'count']).reset_index()
        stats.columns = ['Proceso', 'Sensor', 'Media', 'Máximo', 'Mínimo', 'Desv. Estándar', 'Nº Muestras']
        st.dataframe(stats.style.format({
            'Media': '{:.2f}',
            'Máximo': '{:.2f}',
            'Mínimo': '{:.2f}',
            'Desv. Estándar': '{:.2f}'
        }), use_container_width=True)

        st.subheader("Gráficas de Dispersión (Separadas por Magnitud/Sensor)")
        st.write("Nota: Se separan por sensor para no mezclar diferentes unidades de medida (°C, Bar, cm).")
        
        # Identificamos los sensores que están en la base de datos
        sensores_unicos = df_filtrado['sensor'].unique()
        
        # Creamos una figura con tantas columnas como sensores haya (normalmente 3)
        fig_box, axes = plt.subplots(1, len(sensores_unicos), figsize=(15, 5))
        
        # Ajuste de seguridad por si en el filtro lateral solo dejan 1 sensor
        if len(sensores_unicos) == 1:
            axes = [axes]
            
        # Dibujamos un boxplot para cada sensor en su propio cuadro
        for i, sensor in enumerate(sensores_unicos):
            df_sensor = df_filtrado[df_filtrado['sensor'] == sensor]
            sns.boxplot(data=df_sensor, x='proceso', y='valor_detectado', palette='Set2', ax=axes[i])
            
            axes[i].set_title(f"Dispersión: {sensor}", fontweight='bold')
            axes[i].set_ylabel("Valor Detectado")
            axes[i].set_xlabel("Proceso")
            axes[i].tick_params(axis='x', rotation=45) # Rotamos los nombres para que se lean bien
            
        plt.tight_layout()
        st.pyplot(fig_box)

    # 4. TABLAS DE FRECUENCIA
    with tab2:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver las tablas de frecuencia.")
        else:
            st.header("Tablas de Frecuencia")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.subheader("Fallas por Proceso")
                f_proc = df_filtrado['proceso'].value_counts().reset_index()
                f_proc.columns = ['Proceso', 'Cant. Fallas']
                st.table(f_proc)

                fig_p = plt.figure(figsize=(5, 4))
                sns.barplot(data=f_proc, x='Proceso', y='Cant. Fallas', palette='viridis')
                st.pyplot(fig_p)

            with c2:
                st.subheader("Fallas por Sensor")
                f_sens = df_filtrado['sensor'].value_counts().reset_index()
                f_sens.columns = ['Sensor', 'Cant. Fallas']
                st.table(f_sens)

                fig_s = plt.figure(figsize=(5, 4))
                sns.countplot(data=df_filtrado, x='sensor', palette='magma')
                plt.xticks(rotation=45)
                st.pyplot(fig_s)

            with c3:
                st.subheader("Tipo de Falla más Común")
                f_tipo = df_filtrado['tipo_falla'].value_counts().reset_index()
                f_tipo.columns = ['Tipo Falla', 'Frecuencia']
                st.table(f_tipo.head(5))

                fig_t = plt.figure(figsize=(5, 4))
                f_tipo.head(3).plot(kind='bar', x='Tipo Falla', y='Frecuencia', ax=plt.gca(), color='teal')
                st.pyplot(fig_t)

    # 5. GRÁFICOS BÁSICOS
    with tab3:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver los gráficos por proceso.")
        else:
            st.header("Visualización Base")
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.subheader("Barras: Fallas por Proceso")
                fig_bar = plt.figure()
                sns.countplot(data=df_filtrado, x='proceso', palette='viridis')
                st.pyplot(fig_bar)

                st.subheader("Boxplot: Dispersión de Presión")
                fig_box = plt.figure()
                df_pres = df_filtrado[df_filtrado['sensor'] == 'Manometro_Bourdon']
                sns.boxplot(data=df_pres, x='proceso', y='valor_detectado', palette='Reds')
                st.pyplot(fig_box)

            with col_g2:
                st.subheader("Histograma: Temperatura")
                fig_hist = plt.figure()
                df_temp = df_filtrado[df_filtrado['sensor'] == 'RTD_PT100']
                sns.histplot(df_temp['valor_detectado'], kde=True, color='orange')
                st.pyplot(fig_hist)

                st.subheader("Línea Temporal: Fallas por Fecha")
                fig_line = plt.figure()
                df_timeline = df_filtrado.set_index('fecha_hora').resample('D').size()
                df_timeline.plot(color='blue', marker='o')
                plt.ylabel('Cant. Fallas')
                st.pyplot(fig_line)

    # 6. ANÁLISIS AVANZADO
    with tab4:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver el análisis avanzado.")
        else:
            st.header("Análisis Probabilístico y de Variables")

            st.subheader("Probabilidad de Falla por Proceso")
            totales = len(df_filtrado)
            prob_proceso = (df_filtrado['proceso'].value_counts() / totales * 100).reset_index()
            prob_proceso.columns = ['Proceso', 'Probabilidad de Falla (%)']
            st.table(prob_proceso)

            st.markdown("---")
            st.subheader("Relación entre Valor Detectado y Tiempo hasta Falla")
            fig_rel = plt.figure(figsize=(10, 5))
            sns.scatterplot(data=df_filtrado, x='valor_detectado', y='tiempo_hasta_falla_h', hue='criticidad', style='sensor', palette='Set1')
            plt.title('¿Valores altos reducen el tiempo de vida?')
            st.pyplot(fig_rel)

            st.markdown("---")
            st.subheader("Curva de Experiencia")
            fig_exp = plt.figure(figsize=(10, 5))
            for p in df_filtrado['proceso'].unique():
                df_p = df_filtrado[df_filtrado['proceso'] == p].sort_values('fecha_hora')
                df_p['acumulado'] = range(1, len(df_p) + 1)
                plt.plot(df_p['fecha_hora'], df_p['acumulado'], label=p)
            plt.legend()
            plt.title('Fallas acumuladas por proceso')
            st.pyplot(fig_exp)

    # 7. ALERTAS PREDICTIVAS
    with tab5:
        st.header("Alertas Predictivas")
        st.write("Se evalúan los últimos 10 registros y se alerta si el valor supera la media más 1.5 desviaciones estándar para el proceso y sensor.")

        ultimos_registros = df_filtrado.sort_values('fecha_hora', ascending=False).head(10)
        for _, row in ultimos_registros.iterrows():
            historico_aislado = df[(df['proceso'] == row['proceso']) & (df['sensor'] == row['sensor'])]
            media_aislada = historico_aislado['valor_detectado'].mean()
            std_aislada = historico_aislado['valor_detectado'].std()
            umbral_critico = media_aislada + (1.5 * std_aislada)

            if row['valor_detectado'] > umbral_critico:
                color = '#ff4b4b'
                estado = 'CRÍTICO (Valor Atípico / Posible Falla)'
            else:
                color = '#28a745'
                estado = 'ESTABLE (Dentro del margen estadístico)'

            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background-color: #f8f9fa;">
                <strong>Proceso:</strong> {row['proceso']} | <strong>Sensor:</strong> {row['sensor']}<br>
                <strong>Lectura Detectada:</strong> {row['valor_detectado']:.2f} <i>(Umbral: {umbral_critico:.2f})</i><br>
                <span style="color: {color}; font-weight: bold;">ESTADO: {estado}</span>
            </div>
            """, unsafe_allow_html=True)

