import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard Analítico MiniPlanta", layout="wide")
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.figsize': (10, 6), 'font.size': 10})

st.title("Dashboard Analítico Integral: Mini Planta Láctea")
st.markdown("---")

@st.cache_data
def cargar_datos():
    # USANDO RUTA ABSOLUTA PARA EVITAR EL ERROR DE ARCHIVO NO ENCONTRADO
    archivo = "/Users/macbook/Documents/PRUEBA 1/analisis.xlsx"
    try:
        df = pd.read_excel(archivo, sheet_name='Base_Datos_Integrada')
        # Convertimos a fecha, ignorando errores si hay celdas vacías
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'], errors='coerce')
        return df
    except Exception as e:
        return e


df = cargar_datos()

if isinstance(df, Exception):
    st.error(f"Error al cargar el archivo: {df}")
    st.info("Asegúrate de que el archivo se llame 'analisis.xlsx' y esté en: /Users/macbook/Documents/PRUEBA 1/")
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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([

        "Estadística Descriptiva",

        "Tablas de Frecuencia",

        "Gráficos Básicos",

        "Análisis Avanzado",

        "Alertas Predictivas",
        
        "Resumen Final"

    ])


   
    #3. ESTADÍSTICA DESCRIPTIVA
    with tab1:
        st.header("Resumen de la Base de Datos y Distribución de Fallas")
        
        # Tabla general
        st.write("### Resumen de la Base de Datos")
        st.dataframe(df_filtrado)

        st.markdown("---")
        
        # Estadísticas agrupadas solo por sensor
        st.write("### Estadísticas por Sensor")
        resumen = df_filtrado.groupby('sensor')['valor_detectado'].agg(['mean', 'std', 'min', 'max']).rename(columns={
            'mean': 'Media', 'std': 'Desv. Est.', 'min': 'Mínimo', 'max': 'Máximo'
        })
        st.table(resumen)

        st.markdown("---")
        
        # Estadísticas avanzadas agrupadas por proceso y sensor
        st.subheader("Análisis de Medias, Máximos, Mínimos y Desviaciones")
        stats = df_filtrado.groupby(['proceso', 'sensor'])['valor_detectado'].agg(['mean', 'max', 'min', 'std', 'count']).reset_index()
        stats.columns = ['Proceso', 'Sensor', 'Media', 'Máximo', 'Mínimo', 'Desv. Estándar', 'Nº Muestras']
        st.dataframe(stats.style.format({
            'Media': '{:.2f}',
            'Máximo': '{:.2f}',
            'Mínimo': '{:.2f}',
            'Desv. Estándar': '{:.2f}'
        }), use_container_width=True)

        st.markdown("---")

        # Gráficas de Dispersión
        st.subheader("Gráficas de Dispersión (Separadas por Magnitud/Sensor)")
        sensores_unicos = df_filtrado['sensor'].unique()
        
        if len(sensores_unicos) > 0:
            fig_box, axes = plt.subplots(1, len(sensores_unicos), figsize=(15, 5))
            
            # Ajuste en caso de que solo haya 1 sensor seleccionado
            if len(sensores_unicos) == 1:
                axes = [axes]
                
            for i, sensor in enumerate(sensores_unicos):
                df_sensor = df_filtrado[df_filtrado['sensor'] == sensor]
                sns.boxplot(data=df_sensor, x='proceso', y='valor_detectado', palette='Set2', ax=axes[i], hue='proceso', legend=False)
                axes[i].set_title(f"Dispersión: {sensor}", fontweight='bold')
                axes[i].tick_params(axis='x', rotation=45)
                
            plt.tight_layout()
            st.pyplot(fig_box)
# 4. TABLAS DE FRECUENCIA Y DISPERSIÓN
    with tab2:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver las tablas de frecuencia.")
        else:
            st.header(" Análisis de Frecuencia y Dispersión de Fallos")
            st.info("Estas tablas muestran dónde se concentran los problemas. El objetivo es reducir estas frecuencias a cero mediante mantenimiento preventivo.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("Fallas por Proceso")
                f_proc = df_filtrado['proceso'].value_counts().reset_index()
                f_proc.columns = ['Proceso', 'Cant. Fallas']
                st.table(f_proc)
                
                fig_p, ax_p = plt.subplots(figsize=(5, 4))
                sns.barplot(data=f_proc, x='Proceso', y='Cant. Fallas', palette='viridis', ax=ax_p)
                ax_p.axhline(5, color='red', linestyle='--', label='Meta Máxima')
                ax_p.legend()
                st.pyplot(fig_p)
                st.write("**Uso:** Identifica qué área de la planta requiere inversión inmediata.")

            with c2:
                st.subheader("Fallas por Sensor")
                f_sens = df_filtrado['sensor'].value_counts().reset_index()
                f_sens.columns = ['Sensor', 'Cant. Fallas']
                st.table(f_sens)
                
                fig_s, ax_s = plt.subplots(figsize=(5, 4))
                sns.barplot(data=f_sens, x='Sensor', y='Cant. Fallas', palette='magma', ax=ax_s)
                plt.xticks(rotation=45)
                st.pyplot(fig_s)
                st.write("**Uso:** Indica qué repuestos debemos tener siempre en almacén.")

            with c3:
                st.subheader("Fallas más Comunes")
                f_tipo = df_filtrado['tipo_falla'].value_counts().reset_index()
                f_tipo.columns = ['Tipo Falla', 'Frecuencia']
                st.table(f_tipo.head(5))
                
                fig_t, ax_t = plt.subplots(figsize=(5, 4))
                sns.barplot(data=f_tipo.head(3), x='Tipo Falla', y='Frecuencia', color='teal', ax=ax_t)
                st.pyplot(fig_t)
                st.write("**Uso:** Ayuda a capacitar al personal en los errores más frecuentes.")
            
            st.markdown("---")
            
            # --- NUEVA SECCIÓN: GRÁFICA DE DISPERSIÓN CON LÍMITES POR PROCESO ---
            st.subheader("Relación de Desgaste: Tiempo de Uso vs. Valor del Sensor")
            
            st.write("""
            **Muestra la relación directa entre el **tiempo de operación (horas)** y la **temperatura registrada** al momento de la falla. 
            La **línea roja** es el límite máximo permitido (calculado según la variación de cada proceso). Si los puntos superan esta línea a medida que avanzan las horas, significa que el cansancio térmico del equipo está descontrolando la producción. ¡Es la alerta visual para programar un mantenimiento!
            """)

            procesos_presentes = df_filtrado['proceso'].unique()
            
            # Creamos columnas dinámicas según los procesos seleccionados para ponerlas lado a lado
            cols_disp = st.columns(len(procesos_presentes))
            
            for i, proceso in enumerate(procesos_presentes):
                with cols_disp[i]:
                    # Usamos el sensor de temperatura (RTD_PT100) como indicador principal para no mezclar escalas
                    df_proc_temp = df_filtrado[(df_filtrado['proceso'] == proceso) & (df_filtrado['sensor'] == 'RTD_PT100')]
                    
                    if not df_proc_temp.empty:
                        fig_disp, ax_disp = plt.subplots(figsize=(5, 4))
                        
                        # Dibujar los puntos (Tiempo vs Valor)
                        sns.scatterplot(data=df_proc_temp, x='tiempo_hasta_falla_h', y='valor_detectado', color='#8A2BE2', s=60, alpha=0.8, ax=ax_disp)
                        
                        # Calcular el límite de tolerancia específico de este proceso
                        media_val = df_proc_temp['valor_detectado'].mean()
                        std_val = df_proc_temp['valor_detectado'].std()
                        limite_max = media_val + (1.5 * std_val) # Límite basado en la media + desviación
                        
                        # Trazar TODA la línea roja continua en el eje horizontal (límite de Y)
                        ax_disp.axhline(limite_max, color='red', linestyle='-', linewidth=2.5, label=f'Límite Crítico: {limite_max:.1f}°C')
                        
                        ax_disp.set_title(f"PROCESO: {proceso.upper()}", fontweight='bold')
                        ax_disp.set_xlabel("Tiempo de Trabajo (Horas)")
                        ax_disp.set_ylabel("Valor del Sensor (°C)")
                        ax_disp.legend(loc='lower right', fontsize='small')
                        ax_disp.grid(True, linestyle=':', alpha=0.5)
                        
                        st.pyplot(fig_disp)
                        
                        st.write(f"**Análisis Práctico:** En la producción de {proceso}, el sistema colapsa si supera los **{limite_max:.1f}°C**. Los puntos por encima de la franja roja exigen revisión inmediata de la sonda.")
                    else:st.warning(f"Sin datos suficientes para graficar la dispersión en {proceso}.")
# 5. ANÁLISIS DINÁMICO CON ZOOM Y ARRASTRE LIBRE (MODO MAPA)
    with tab3:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver los gráficos.")
        else:
            st.header("Análisis de Precisión: Curvas de Comportamiento")
            
            # --- INFO COMPACTA Y TIP DE NAVEGACIÓN ---
            st.info("""⚠️ **Zonas:** 🟢 Óptimo | 🟠 Advertencia | 🔴 Crítico | ⬛ PELIGRO FATAL
            """)

            # Límites técnicos del manual
            limites_tecnicos = {
                'Queso': {'temp': (32.0, 38.0, 42.0, 250.0), 'presion': (1.0, 1.3, 1.5, 5.0)},
                'Yogurt': {'temp': (42.0, 45.0, 48.0, 250.0), 'presion': (1.0, 1.3, 1.5, 5.0)},
                'Pasteurizacion': {'temp': (72.0, 75.0, 80.0, 250.0), 'presion': (2.5, 3.0, 3.5, 5.0)},
                'Dulce de Leche': {'temp': (85.0, 88.0, 89.0, 250.0), 'presion': (3.0, 3.5, 4.0, 5.0)},
                'Biodiesel': {'temp': (55.0, 60.0, 64.0, 70.0), 'presion': (1.0, 1.2, 1.3, 1.5)} 
            }

            for proceso in df_filtrado['proceso'].unique():
                st.markdown(f"---")
                st.subheader(f"Monitoreo Crítico: {proceso.upper()}")
                
                df_p = df_filtrado[df_filtrado['proceso'] == proceso]
                lim = limites_tecnicos.get(proceso, {'temp': (0,0,0,0), 'presion': (0,0,0,0)})
                
                # --- GRÁFICA DE TEMPERATURA (PLOTLY) ---
                df_t = df_p[df_p['sensor'] == 'RTD_PT100']
                if not df_t.empty:
                    st.write("**Historial Detallado de Temperatura (°C)**")
                    fig_t = px.line(df_t, x='fecha_hora', y='valor_detectado', 
                                    title=f"Evolución Térmica - {proceso}",
                                    markers=True, 
                                    hover_data={'tipo_falla': True, 'valor_detectado': ':.2f'})
                    
                    t_min, t_max, t_crit, t_ext = lim['temp']
                    fig_t.add_hline(y=t_min, line_dash="dash", line_color="green", annotation_text="Mínimo")
                    fig_t.add_hline(y=t_max, line_dash="dash", line_color="orange", annotation_text="Aviso")
                    fig_t.add_hline(y=t_crit, line_dash="dot", line_color="red", line_width=2, annotation_text="CRÍTICO")
                    fig_t.add_hline(y=t_ext, line_color="black", line_width=4, annotation_text="💀 DAÑO")

                    # ACTIVAMOS dragmode='pan' PARA ARRASTRE LIBRE
                    fig_t.update_layout(height=450, hovermode="x unified", dragmode='pan', margin=dict(l=10, r=10, t=40, b=10))
                    
                    # config={'scrollZoom': True} mantiene el zoom con la rueda
                    st.plotly_chart(fig_t, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                    
                    pico_t = df_t['valor_detectado'].max()
                    if pico_t >= t_ext: st.error(f"💀 **FALLA CATASTRÓFICA:** Pico de {pico_t:.1f}°C detectado. Sensor Pt100 quemado.")
                    elif pico_t >= t_crit: st.error(f"🚨 **ALERTA ROJA:** Sobrecalentamiento crítico de {pico_t:.1f}°C. Producto dañado.")
                    else: st.success(f"✅ **NORMAL:** Temperatura máxima de {pico_t:.1f}°C bajo control.")

                # --- GRÁFICA DE PRESIÓN (PLOTLY) ---
                df_pre = df_p[df_p['sensor'] == 'Manometro_Bourdon']
                if not df_pre.empty:
                    st.write("**Historial Detallado de Presión (Bar)**")
                    fig_p = px.area(df_pre, x='fecha_hora', y='valor_detectado', 
                                    title=f"Estrés de Presión - {proceso}",
                                    color_discrete_sequence=['#17a2b8'])
                    
                    p_min, p_max, p_crit, p_ext = lim['presion']
                    fig_p.add_hline(y=p_min, line_dash="dash", line_color="green")
                    fig_p.add_hline(y=p_max, line_dash="dash", line_color="orange")
                    fig_p.add_hline(y=p_crit, line_dash="dot", line_color="red", line_width=2)
                    fig_p.add_hline(y=p_ext, line_color="black", line_width=4, annotation_text="💀 EXPLOSIÓN")

                    # ACTIVAMOS dragmode='pan' PARA ARRASTRE LIBRE
                    fig_p.update_layout(height=450, hovermode="x unified", dragmode='pan', margin=dict(l=10, r=10, t=40, b=10))
                    
                    # config={'scrollZoom': True} mantiene el zoom con la rueda
                    st.plotly_chart(fig_p, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                    
                    pico_p = df_pre['valor_detectado'].max()
                    if pico_p >= p_ext: st.error(f"💀 **PELIGRO MORTAL:** Presión de {pico_p:.1f} Bar. Riesgo inminente de estallido.")
                    elif pico_p >= p_crit: st.warning(f"🚨 **PRESIÓN ALTA:** Superado el límite de seguridad con {pico_p:.1f} Bar.")
                    else: st.success(f"✅ **SEGURO:** Operación estable y controlada a {pico_p:.1f} Bar.")

# 6. ANÁLISIS AVANZADO
    with tab4:
        if df_filtrado.empty:
            st.warning("Selecciona al menos un proceso para ver el análisis avanzado.")
        else:
            st.header("Análisis Probabilístico y de Confiabilidad")
            
            st.subheader("Modelos de Confiabilidad y Pendiente (K)")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.info("**A. Sensor Temperatura**\n*(Modelo Parabólico)*")
                st.success("**K₁ = 1.7778 × 10⁻⁹**")
            with col_m2:
                st.info("**B. Manómetro Presión**\n*(Modelo Lineal)*")
                st.success("**K₂ = 8.8889 × 10⁻⁷**")
            with col_m3:
                st.info("**C. Nivel Conductivo**\n*(Modelo Decreciente)*")
                st.success("**K₃ = 8.8889 × 10⁻⁷**")

            st.subheader("📈 Gráfico Comparativo de Riesgo")
            fig_k = plt.figure(figsize=(10, 4))
            t = np.linspace(0, 1500, 500) 
            plt.plot(t, (1.7778e-9)*(1500*t - t**2), label='Temperatura (Curva)', color='orange', lw=3)
            plt.plot(t, (8.8889e-7)*t, label='Presión (Sube)', color='red', lw=3)
            plt.plot(t, (8.8889e-7)*(1500-t), label='Nivel (Baja)', color='blue', lw=3)
            plt.fill_between(t, (1.7778e-9)*(1500*t - t**2), alpha=0.1, color='orange')
            plt.title("Evolución del Riesgo de Falla")
            plt.xlabel("Horas")
            plt.legend()
            st.pyplot(fig_k)
            st.markdown("---")

            col_graf1, _ = st.columns(2)
            with col_graf1:
                st.subheader("Relación Valor vs Tiempo de Vida")
                fig_rel = plt.figure(figsize=(8, 4))
                sns.scatterplot(data=df_filtrado, x='valor_detectado', y='tiempo_hasta_falla_h', hue='criticidad', palette='Set1')
                st.pyplot(fig_rel)
           # --- SECCIÓN 7.5 (CAPÍTULO 8) ---
            st.header("Curvas de Experiencia por Proceso")
            
          
            st.subheader("Parámetros Estándar (Altitud Mallasilla)")
            # Tabla de parámetros técnicos (Resultados directos)
            data_cap8 = {
                "Proceso": ["Queso", "Yogurt", "Pasteurización", "Dulce de Leche", "Biodiesel"],
                "Temp. Normal": ["32°C - 38°C", "42°C - 45°C", "72°C - 75°C", "85°C - 88°C", "55°C - 60°C"],
                "Presión (Bar)": ["1.0 - 1.5", "1.0 - 1.5", "2.5 - 3.5", "3.0 - 4.0", "Max 1.5"],
                "Límite Crítico": ["Agitación Crítica", "Estabilidad", "88°C (Seguridad)", "88°C (Ebullición)", "64°C (Evap. Metanol)"]
            }
            st.table(pd.DataFrame(data_cap8))

            st.markdown("---")
            
            # --- SECCIÓN 8.5: ANÁLISIS POR SENSOR ---
            st.subheader("Análisis de Aprendizaje por Instrumento")
            st.caption("Evolución de fallas y diagnóstico técnico individual")
            
            sensores_presentes = df_filtrado['sensor'].unique()
            cols_graficos = st.columns(len(sensores_presentes)) 
            
            # Diccionario de análisis técnico para 8.5
            analisis_tecnico = {
                'RTD_PT100': "**Análisis (Temp):** La curva muestra estabilización. La pendiente disminuye conforme el operador calibra mejor el PID del caldero.",
                'Manometro_Bourdon': "**Análisis (Presión):** Fallas lineales por fatiga mecánica. Se recomienda amortiguación por glicerina para aplanar la curva.",
                'Nivel_Conductivo': "**Análisis (Nivel):** Alta tasa de error inicial por residuos lácteos. Mejora drásticamente al aplicar protocolos de limpieza CIP."
            }

            for i, sensor_name in enumerate(sensores_presentes):
                with cols_graficos[i]:
                    # Gráfica individual
                    fig_exp = plt.figure(figsize=(5, 4))
                    df_sensor = df_filtrado[df_filtrado['sensor'] == sensor_name].sort_values('fecha_hora')
                    df_sensor['acumulado'] = range(1, len(df_sensor) + 1)
                    
                    plt.plot(df_sensor['fecha_hora'], df_sensor['acumulado'], marker='o', color='#2ca02c', linewidth=2)
                    plt.title(f"{sensor_name}", fontsize=11, fontweight='bold')
                    plt.xticks(rotation=45, fontsize=7)
                    plt.grid(True, alpha=0.3)
                    st.pyplot(fig_exp)
                    
                    # 8.5 Análisis debajo de cada gráfica
                    st.write(analisis_tecnico.get(sensor_name, "**Análisis:** Datos en proceso de estabilización histórica."))

            st.markdown("---")

            # --- SECCIÓN 8.3 y 8.4 (AHORA CON LOS 3 SENSORES Y METODOLOGÍA) ---
            col_dev1, col_dev2 = st.columns(2)
            
            with col_dev1:
                st.subheader("Tolerancias Operativas")
                st.caption("🔧 **Metodología:** Establecidas calculando la **Desviación Estándar (σ)** sobre el histórico de datos limpios.")
                st.write("""
                * **🌡️ Temperatura (Pt100):** Límite de ruido de **± 1.5 °C**. Definido por la varianza del régimen estacionario.
                * **⏱️ Presión (Manómetro):** Tolerancia de **± 0.2 Bar**. Aceptable considerando la vibración normal de las bombas.
                * **💧 Nivel (Conductivo):** Tolerancia de oleaje de **± 2.0 cm**. Filtrado estadísticamente para ignorar la espuma durante la agitación.
                """)
                
            with col_dev2:
                st.subheader("Lógica de Detección (PLC)")
                st.caption("💻 **Metodología:** El algoritmo evalúa la **Tasa de Cambio en el tiempo (Derivada)** de las señales.")
                st.warning("""
                **Criterios de Disparo de Emergencia (Paro Automático):**
                * **🌡️ Temperatura:** Si sube **> 2°C por minuto** $\\rightarrow$ Pre-alarma de sobrecalentamiento rápido.
                * **⏱️ Presión:** Si detecta un pico **> 0.5 Bar por segundo** $\\rightarrow$ Alarma por obstrucción o golpe de ariete.
                * **💧 Nivel:** Si la señal cae a cero en **< 1 segundo** $\\rightarrow$ Bloqueo inmediato de resistencias para evitar que se quemen en seco.
                """)
    # 7. ALERTAS PREDICTIVAS
    with tab5:
        st.header("Alertas")
        ultimos_registros = df_filtrado.sort_values('fecha_hora', ascending=False).head(10)
        for _, row in ultimos_registros.iterrows():
            historico_aislado = df[(df['proceso'] == row['proceso']) & (df['sensor'] == row['sensor'])]
            umbral_critico = historico_aislado['valor_detectado'].mean() + (1.5 * historico_aislado['valor_detectado'].std())
            color = '#ff4b4b' if row['valor_detectado'] > umbral_critico else '#28a745'
            estado = 'CRÍTICO' if row['valor_detectado'] > umbral_critico else 'ESTABLE'
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background-color: #f8f9fa;">
                <strong>Proceso:</strong> {row['proceso']} | <strong>Sensor:</strong> {row['sensor']}<br>
                <strong>Lectura:</strong> {row['valor_detectado']:.2f} | <strong>Estado:</strong> <span style="color:{color}">{estado}</span>
            </div>
            """, unsafe_allow_html=True)


   # ---------------------------------------------------------
    # NUEVA PESTAÑA 6: RESUMEN EJECUTIVO Y CONCLUSIONES AUTOMATIZADAS
    # ---------------------------------------------------------
    with tab6:
        st.header("Resumen Final")
        
        # Referencia técnica directa
        st.markdown("""
        **Referencia :**
        * **Eje X:** Temperatura detectada (°C).
        * **Eje Y:** Frecuencia (cantidad de registros).
        * **Picos:** Puntos de mayor incidencia en el proceso.
        """)

        st.info("Diagnóstico automático basado en la distribución de datos históricos.")

        if df_filtrado.empty:
            st.warning("Selecciona procesos en la barra lateral para generar el resumen.")
        else:
            for proceso in df_filtrado['proceso'].unique():
                st.markdown(f"### Análisis de Proceso: {proceso}")
                col_graf, col_txt = st.columns([2, 1])
                
                df_proc_res = df_filtrado[(df_filtrado['proceso'] == proceso) & (df_filtrado['sensor'] == 'RTD_PT100')]
                
                if not df_proc_res.empty:
                    with col_graf:
                        fig_hist = px.histogram(
                            df_proc_res, x="valor_detectado", 
                            nbins=20, 
                            title=f"Distribución de Carga Térmica: {proceso}",
                            labels={'valor_detectado': 'Temperatura (°C)', 'count': 'Frecuencia'},
                            color_discrete_sequence=['#4B8BBE'],
                            marginal="rug"
                        )
                        fig_hist.update_layout(height=350, showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
                        st.plotly_chart(fig_hist, use_container_width=True)

                    with col_txt:
                        st.write("**Estado del Proceso:**")
                        
                        media = df_proc_res['valor_detectado'].mean()
                        std_dev = df_proc_res['valor_detectado'].std()
                        conteo = len(df_proc_res)
                        
                        if std_dev < 2:
                            estabilidad = "🟢 **Alta Estabilidad:** Poca variación detectada."
                        else:
                            estabilidad = "🟡 **Variabilidad:** Inestabilidad en las lecturas térmicas."
                        
                        if media > df_proc_res['valor_detectado'].median():
                            tendencia = "⚠️ **Sesgo Positivo:** Tendencia a registros sobre la media."
                        else:
                            tendencia = "✅ **Normalidad:** Registros concentrados en rangos seguros."

                        st.success(estabilidad)
                        st.info(tendencia)
                        st.markdown(f"**Muestras analizadas:** {conteo}")
                
                st.markdown("---")
