from dash import Input, Output, State, dash_table, dcc, html
import dash
import pandas as pd
import numpy as np
import random
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import asignar_industria, eliminar_acentos, import_dict, comunas_df, puertos_coords, cargar_diccionarios, enriquecer_dataframe, cargar_descripcion_estructura ,leer_txt_sin_encabezado
from io import StringIO
from validator import validar_df
from dash.exceptions import PreventUpdate

os.chdir(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER_ROOT = "uploads"
DICCIONARIO_PATH = os.path.join('data', 'DICCIONARIO.xlsx')


def esperar_liberacion(filepath, intentos=5, espera=1):
    import time
    for _ in range(intentos):
        try:
            with open(filepath, 'rb'):
                return True
        except PermissionError:
            time.sleep(espera)
    return False


def register_callbacks(app):
    @app.callback(
        # 🟢 Outputs
        Output('stored-data', 'data'),
        Output('date-picker-range', 'min_date_allowed'),
        Output('date-picker-range', 'max_date_allowed'),
        Output('date-picker-range', 'start_date'),
        Output('date-picker-range', 'end_date'),
        Output('date-picker-range', 'disabled'),
        Output('search-producto', 'disabled'),
        Output('search-importador', 'disabled'),
        Output('search-pa-orig', 'disabled'),
        Output('search-pa-adq', 'disabled'),
        Output('search-comuna', 'disabled'),
        Output('column-dropdown', 'disabled'),

        # 🟡 Inputs
        Input('dash-uploader', 'isCompleted'),

        # 🔵 States
        State('dash-uploader', 'fileNames')
    )
    def actualizar_datos(isCompleted, fileNames):
        try:
            return process_upload(isCompleted, fileNames)
        except Exception as e:
            print(f"❌ Error en process_upload: {e}")
            return None, None, None, None, None, True, True, True, True, True, True, True


    def process_upload(isCompleted, fileNames):
        print(f"📥 isCompleted: {isCompleted}")
        print(f"📂 fileNames: {fileNames} (type: {type(fileNames)})")

        if not isCompleted or not fileNames or len(fileNames) == 0:
            print("⚠️ Upload incompleto o sin archivos")
            raise PreventUpdate

        filename = fileNames[0]

        # Buscar el archivo en cualquier subcarpeta dentro de UPLOAD_FOLDER_ROOT
        pattern = os.path.join(UPLOAD_FOLDER_ROOT, '**', filename)
        matches = glob.glob(pattern, recursive=True)

        if not matches:
            print(f"⚠️ No se encontró archivo con patrón: {pattern}")
            return None, None, None, None, None, True, True, True, True, True, True, True

        filepath = matches[0]

        if not esperar_liberacion(filepath):
            print(f"⚠️ El archivo está bloqueado por el sistema: {filepath}")
            return None, None, None, None, None, True, True, True, True, True, True, True

        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.csv':
            df = pd.read_csv(filepath)
        elif ext == '.txt':
            try:
                df = leer_txt_sin_encabezado(filepath)
            except Exception as e:
                print(f"❌ Error al leer TXT: {e}")
                return None, None, None, None, None, True, True, True, True, True, True, True

            validar_df(df, columnas_esperadas=[
                'DD', 'NUM_UNICO_IMPORTADOR', 'ARANC_NAC', 'CIF_ITEM', 'PA_ORIG', 'PA_ADQ', 'TPO_CARGA', 'VIA_TRAN', 'TOT_BULTOS',
                'TPO_BUL1', 'CANT_BUL1', 'TPO_BUL2', 'CANT_BUL2', 'DNOMBRE', 'DMARCA', 'DVARIEDAD', 'DOTRO1', 'DOTRO2',
                'ATR_5', 'ATR_6', 'MEDIDA', 'CANT_MERC', 'CODCOMUN', 'ADU', 'PTO_DESEM', 'PTO_EMB', 'DESOBS1', 'TPO_DOCTO'
            ])

            if 'DD' in df.columns:
                df['DD'] = pd.to_datetime(df['DD'].astype(int).astype(str), format='%d%m%Y', errors='coerce')

            if df['DD'].isna().all():
                print("⚠️ Todas las fechas en 'DD' son inválidas o no se pudieron convertir.")
                return None, None, None, None, None, True, True, True, True, True, True, True
        else:
            return None, None, None, None, None, True, True, True, True, True, True, True

        df['NUM_UNICO_IMPORTADOR'] = df['NUM_UNICO_IMPORTADOR'].astype(str)

        dicts = cargar_diccionarios()
        df['NUM_UNICO_IMPORTADOR'] = df['NUM_UNICO_IMPORTADOR'].apply(lambda x: import_dict.get(str(x), x))

        select_df = df[[
            'DD', 'NUM_UNICO_IMPORTADOR', 'ARANC_NAC', 'CIF_ITEM', 'PA_ORIG', 'PA_ADQ', 'TPO_CARGA', 'VIA_TRAN', 'TOT_BULTOS',
            'TPO_BUL1', 'CANT_BUL1', 'TPO_BUL2', 'CANT_BUL2', 'DNOMBRE', 'DMARCA', 'DVARIEDAD', 'DOTRO1', 'DOTRO2',
            'ATR_5', 'ATR_6', 'MEDIDA', 'CANT_MERC', 'CODCOMUN', 'ADU', 'PTO_DESEM', 'PTO_EMB', 'DESOBS1', 'TPO_DOCTO'
        ]].copy()

        select_df['PRODUCTO'] = (
            select_df['DNOMBRE'].fillna('') + ' ' +
            select_df['DMARCA'].fillna('') + ' ' +
            select_df['DVARIEDAD'].fillna('') + ' ' +
            select_df['DOTRO1'].fillna('') + ' ' +
            select_df['DOTRO2'].fillna('') + ' ' +
            select_df['ATR_5'].fillna('') + ' ' +
            select_df['ATR_6'].fillna('')
        )

        select_df['Industria'] = select_df['ARANC_NAC'].apply(asignar_industria)
        select_df = enriquecer_dataframe(select_df, dicts)
        select_df = select_df.drop(columns=['DNOMBRE', 'DMARCA', 'DVARIEDAD'])

        select_df['DD'] = pd.to_datetime(select_df['DD'], format='%Y-%m-%d')
        min_date = select_df['DD'].min().date()
        max_date = select_df['DD'].max().date()

        return (
            select_df.to_json(date_format='iso', orient='split'),
            min_date, max_date, min_date, max_date,
            False, False, False, False, False, False, False
        )


        return None, None, None, None, None, True, True, True, True, True, True, True



    @app.callback(
        Output('output-visualizations', 'children'),
        Input('stored-data', 'data'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date'),
        Input('search-producto', 'value'),
        Input('search-importador', 'value'),
        Input('search-pa-orig', 'value'),
        Input('search-pa-adq', 'value'),
        Input('search-comuna', 'value'),
        Input('column-dropdown', 'value'),
        Input('section-dropdown', 'value'),  # Agrega Input para el dropdown de Section
        Input('hsdesc-dropdown', 'value'),  # <-- AGREGA ESTA LÍNEA
        prevent_initial_call=True
    )


    def update_visualizations(
        data, start_date, end_date, search_producto, search_importador, search_pa_orig,
        search_pa_adq, search_comuna, column_dropdown, section_value, hsdesc_value
    ):


        if data is None or start_date is None or end_date is None or column_dropdown is None:
            print("📦 Estado de inputs:")
            print("→ data:", "OK" if data else "None")
            print("→ start_date:", start_date)
            print("→ end_date:", end_date)
            print("→ column_dropdown:", column_dropdown)

            
            print("⚠️ Callback detenido: algún input es None")
            return dash.no_update

        print("📢 Callback ejecutado")
        json_buffer = StringIO(data)
        df = pd.read_json(json_buffer, orient='split')
        df = agregar_section(df)  # ¡Solo esta línea, elimina el bloque de merge manual!
        # --- Elimina este bloque duplicado ---
        # if 'ARANC_NAC' in df.columns:
        #     df_dict = pd.read_excel(...)
        #     ...
        #     df = pd.merge(...)
        # --- FIN bloque duplicado ---
        # Asegura que la columna DD sea datetime

        print("✔️ DataFrame shape:", df.shape)
        print("✔️ Columnas:", df.columns.tolist())

        df['DD'] = pd.to_datetime(df['DD'], errors='coerce')
        # Asegura que NUM_UNICO_IMPORTADOR sea string
        df['NUM_UNICO_IMPORTADOR'] = df['NUM_UNICO_IMPORTADOR'].astype(str)
        # Filtros
        if start_date and end_date:
            df = df[(df['DD'] >= pd.to_datetime(start_date)) & (df['DD'] <= pd.to_datetime(end_date))]
        if search_producto:
            terms = [t.strip() for t in search_producto.split(',')]
            df = df[df['PRODUCTO'].str.contains('|'.join(terms), case=False, na=False)]
        if search_importador:
            terms = [t.strip() for t in search_importador.split(',')]
            df = df[df['NUM_UNICO_IMPORTADOR'].str.contains('|'.join(terms), case=False, na=False)]
        if search_pa_orig:
            terms = [t.strip() for t in search_pa_orig.split(',')]
            df = df[df['PA_ORIG'].str.contains('|'.join(terms), case=False, na=False)]
        if search_pa_adq:
            terms = [t.strip() for t in search_pa_adq.split(',')]
            df = df[df['PA_ADQ'].str.contains('|'.join(terms), case=False, na=False)]
        if search_comuna:
            terms = [t.strip() for t in search_comuna.split(',')]
            df = df[df['CODCOMUN'].str.contains('|'.join(terms), case=False, na=False)]
        if section_value:
            if isinstance(section_value, list):
                df = df[df['Section'].isin(section_value)]
            else:
                df = df[df['Section'] == section_value]
        if hsdesc_value:
            if isinstance(hsdesc_value, list):
                df = df[df['HS Description'].isin(hsdesc_value)]
            else:
                df = df[df['HS Description'] == hsdesc_value]

        # ¡AQUÍ! Antes de cualquier agrupación o gráfico:
        if df.empty:
            return html.Div([
                html.H3("No hay datos para la combinación de filtros seleccionada.", style={'color': 'red'})
            ])

        # Agrupaciones y gráficos principales
        df['MES'] = df['DD'].dt.to_period('M')
        monthly_group = df.groupby('MES')['CIF_ITEM'].sum().reset_index()
        df['CANT_MERC'] = pd.to_numeric(df['CANT_MERC'], errors='coerce')
        monthly_group['CANT_MERC'] = df.groupby('MES')['CANT_MERC'].sum().reset_index(drop=True)
        monthly_group['MES'] = monthly_group['MES'].dt.to_timestamp() + pd.offsets.MonthEnd(0)
        monthly_group['CIF_ITEM/KILOS'] = monthly_group['CIF_ITEM'] / monthly_group['CANT_MERC']
        monthly_group_country_ADQ = (
            df.groupby(['MES', 'PA_ADQ'])['CIF_ITEM']  # Agrupa por mes y país
            .sum()
            .reset_index()
        )

        monthly_group_country_ADQ['MES'] = monthly_group_country_ADQ['MES'].dt.to_timestamp() + pd.offsets.MonthEnd(0)

        monthly_group_country_ORG = (
            df.groupby(['MES', 'PA_ORIG'])['CIF_ITEM']  # Agrupa por mes y país
            .sum()
            .reset_index()
        )

        monthly_group_country_ORG['MES'] = monthly_group_country_ORG['MES'].dt.to_timestamp() + pd.offsets.MonthEnd(0)

        fig_monthly = px.area(
            monthly_group, x='MES', y='CIF_ITEM',
            title='CIF_ITEM Mensual vs Tiempo',
            labels={'MES': 'Mes', 'CIF_ITEM': 'CIF_ITEM'},
            template='plotly_dark'
        )
        fig_monthly_kilos = px.area(
            monthly_group, x='MES', y='CANT_MERC',
            title='CANT_MERC Mensual vs Tiempo',
            labels={'MES': 'Mes', 'CANT_MERC': 'Kilos'},
            template='plotly_dark'
        )
        fig_monthly_kilos_cif = px.line(
            monthly_group, x='MES', y='CIF_ITEM/KILOS',
            title='CIF_ITEM/KILOS Mensual vs Tiempo',
            labels={'MES': 'Mes', 'CIF_ITEM/KILOS': 'CIF_ITEM/Kilos'},
            template='plotly_dark'
        )

        fig_monthly_group_country_ADQ = px.line(
            monthly_group_country_ADQ,
            x='MES',
            y='CIF_ITEM',
            color='PA_ADQ',  # o 'PA_ORIG' si prefieres
            title='Suma mensual de CIF_ITEM por país de adquisición',
            labels={'MES': 'Mes', 'CIF_ITEM': 'Suma CIF_ITEM', 'PA_ADQ': 'País'},
            template='plotly_dark'
        )

        fig_monthly_group_country_ORG = px.line(
            monthly_group_country_ORG,
            x='MES',
            y='CIF_ITEM',
            color='PA_ORIG',  # o 'PA_ORIG' si prefieres
            title='Suma mensual de CIF_ITEM por país de origen',
            labels={'MES': 'Mes', 'CIF_ITEM': 'Suma CIF_ITEM', 'PA_ORIG': 'País'},
            template='plotly_dark'
        )



        # Gráfico de porcentaje por columna seleccionada
        group = df.groupby(column_dropdown)['CIF_ITEM'].sum()
        percentage = (group / group.sum()) * 100
        percentage = percentage.sort_values(ascending=False)
        fig = px.bar(
            percentage,
            x=percentage.index,
            y=percentage.values,
            title=f'Porcentaje de CIF_ITEM por {column_dropdown}',
            labels={'x': column_dropdown, 'y': 'Porcentaje de CIF_ITEM'},
            template='plotly_dark'
        )
        fig.update_layout(xaxis_tickangle=-45)

        # Gráfico de porcentaje por tipo de producto (Section)
        fig_section = None
        if 'Section' in df.columns:
            group_section = df.groupby('Section')['CIF_ITEM'].sum()
            percentage_section = (group_section / group_section.sum()) * 100
            percentage_section = percentage_section.sort_values(ascending=False)
            fig_section = px.pie(
                percentage_section,
                values=percentage_section.values,
                names=percentage_section.index,
                title='Porcentaje del Tipo de Producto (Section)',
                labels={'value': 'Porcentaje', 'index': 'Tipo de Producto'},
                template='plotly_dark'
            )

        # Top 20 productos
        top20 = df.groupby('PRODUCTO').size().sort_values(ascending=False).head(20)
        top20_df = top20.reset_index()
        top20_df.columns = ['Producto', 'Conteo']

        # Top 20 transacciones por producto
        top20_trans = df.groupby('PRODUCTO').agg({'CIF_ITEM': 'sum', 'DD': 'max'}).sort_values(by='CIF_ITEM', ascending=False).head(20)
        top20_trans_df = top20_trans.reset_index()
        top20_trans_df.columns = ['Producto', 'Total CIF_ITEM', 'Fecha']
        top20_trans_df['Fecha'] = top20_trans_df['Fecha'].dt.strftime('%Y-%m-%d')

        # Top 20 transacciones individuales
        top20_trans_ind = df[['PRODUCTO','TPO_DOCTO','ARANC_NAC' ,'NUM_UNICO_IMPORTADOR', 'CIF_ITEM', 'CANT_MERC', 'DESOBS1', 'DD', 'CODCOMUN', 'ADU', 'PTO_DESEM', 'PTO_EMB', 'VIA_TRAN']].copy()
        top20_trans_ind = top20_trans_ind.sort_values(by='CIF_ITEM', ascending=False).head(20)
        top20_trans_ind['DD'] = top20_trans_ind['DD'].dt.strftime('%Y-%m-%d')

        #Precio promedio por países
        # Tabla para País de Origen
        precio_promedio_origen_df = df.groupby('PA_ORIG').agg({
                    'CIF_ITEM': 'sum',
                    'CANT_MERC': 'sum'
                }).reset_index()
        precio_promedio_origen_df['CANT_MERC'] = precio_promedio_origen_df['CANT_MERC'].replace(0, np.nan)
        precio_promedio_origen_df['Precio Promedio (CIF/Kg)'] = precio_promedio_origen_df['CIF_ITEM'] / precio_promedio_origen_df['CANT_MERC']
        precio_promedio_origen_df['Precio Promedio (CIF/Kg)'] = precio_promedio_origen_df['Precio Promedio (CIF/Kg)'].round(2)
        precio_promedio_origen_df = precio_promedio_origen_df[['PA_ORIG', 'Precio Promedio (CIF/Kg)']]
        # Tabla para País de Adquisición
        precio_promedio_adq_df = df.groupby('PA_ADQ').agg({
                    'CIF_ITEM': 'sum',
                    'CANT_MERC': 'sum'
                }).reset_index()
        precio_promedio_adq_df['CANT_MERC'] = precio_promedio_adq_df['CANT_MERC'].replace(0, np.nan)
        precio_promedio_adq_df['Precio Promedio (CIF/Kg)'] = precio_promedio_adq_df['CIF_ITEM'] / precio_promedio_adq_df['CANT_MERC']
        precio_promedio_adq_df['Precio Promedio (CIF/Kg)'] = precio_promedio_adq_df['Precio Promedio (CIF/Kg)'].round(2)
        precio_promedio_adq_df = precio_promedio_adq_df[['PA_ADQ', 'Precio Promedio (CIF/Kg)']]

        # Heatmap país de origen vs tiempo
        df['MES'] = df['MES'].dt.to_timestamp()
        heatmap_data_origen = df.pivot_table(index='PA_ORIG', columns='MES', values='CIF_ITEM', aggfunc='sum', fill_value=0)
        fig_heatmap_origen = px.imshow(
            heatmap_data_origen,
            title='Heatmap de País de Origen vs Tiempo',
            labels={'color': 'CIF_ITEM'},
            template='plotly_dark'
        )

        # Heatmap país de adquisición vs tiempo
        heatmap_data_adq = df.pivot_table(index='PA_ADQ', columns='MES', values='CIF_ITEM', aggfunc='sum', fill_value=0)
        fig_heatmap_adq = px.imshow(
            heatmap_data_adq,
            title='Heatmap de País de Adquisición vs Tiempo',
            labels={'color': 'CIF_ITEM'},
            template='plotly_dark'
        )

        # Indicadores principales
        unidades = df['MEDIDA'].unique()
        indicadores = []

        if len(unidades) == 1 and unidades[0] == 6:
            total_kg = df['CANT_MERC'].sum()
            total_cif = df['CIF_ITEM'].sum()
            precio_por_kg = total_cif / total_kg if total_kg else 0
            df['MES'] = df['DD'].dt.to_period('M')
            promedio_cif_mensual = df.groupby(df['MES'])['CIF_ITEM'].sum().mean()
            promedio_kg_mensual = df.groupby(df['MES'])['CANT_MERC'].sum().mean()

            indicadores = [
                html.Div([
                    html.Div([
                        html.H4("Total Kg"),
                        html.H5(f"{total_kg:,.0f} Kg 🏋️")
                    ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),
                    html.Div([
                        html.H4("Total CIF"),
                        html.H5(f"{total_cif:,.0f} 💰")
                    ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),
                    html.Div([
                        html.H4("Precio por Kg"),
                        html.H5(f"{precio_por_kg:,.2f} 💸")
                    ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),
                ], style={'display': 'flex', 'justifyContent': 'space-around'}),
                html.H4("Indicadores adicionales"),
                html.P(f"CIF Total Promedio Mensual: {promedio_cif_mensual:,.2f} 📈"),
                html.P(f"Total de Kg Promedio Mensual: {promedio_kg_mensual:,.2f} Kg 📅")
            ]
        else:
            total_cif = df['CIF_ITEM'].sum()
            promedio_cif = df['CIF_ITEM'].mean()
            df['MES'] = df['DD'].dt.to_period('M')
            promedio_kg_mensual = df.groupby(df['MES'])['CANT_MERC'].sum().mean()

            indicadores = [
                html.Div([
                    html.H4("Total CIF"),
                    html.H5(f"{total_cif:,.0f} 💰")
                ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),
                html.H4("Indicadores adicionales"),
                html.P(f"CIF Total Promedio: {promedio_cif:,.2f} 📈"),
                html.P(f"Total de Kg Promedio Mensual: {promedio_kg_mensual:,.2f} Kg 📅")
            ]

        # Normalización y merge igual que en tu código
        df['CODCOMUN'] = df['CODCOMUN'].str.strip().str.lower().apply(eliminar_acentos)
        comunas_df_local = comunas_df.copy()
        df['CODCOMUN'] = df['CODCOMUN'].str.strip().str.lower().apply(eliminar_acentos)
        comunas_df_local['nombre'] = comunas_df_local['nombre'].str.strip().str.lower().apply(eliminar_acentos)
        comunas_df_local = comunas_df_local[['nombre', 'latitud', 'longitud']]
        comunas_df_local.rename(columns={'nombre': 'Comuna', 'latitud': 'Latitud', 'longitud': 'Longitud'}, inplace=True)
        select_df_comunas = df.merge(comunas_df_local, left_on='CODCOMUN', right_on='Comuna', how='left')
        select_df_comunas = select_df_comunas.dropna(subset=['Latitud', 'Longitud'])

        # Estadísticas por comuna
        comunas_stats = df.groupby('CODCOMUN').agg({
            'CIF_ITEM': 'sum',
            'CANT_MERC': 'sum',
            'NUM_UNICO_IMPORTADOR': 'count'
        }).reset_index()
        comunas_stats.columns = ['Comuna', 'Total CIF_ITEM', 'Total Mercancías', 'Número de Transacciones']

        select_df_comunas = select_df_comunas.merge(comunas_stats, on='Comuna', how='left')

        # Mapa interactivo
        fig_comunas = px.scatter_mapbox(
            select_df_comunas,
            lat='Latitud',
            lon='Longitud',
            hover_name='Comuna',
            hover_data={
                'Total CIF_ITEM': True,
                'Total Mercancías': True,
                'Número de Transacciones': True
            },
            color='Comuna',
            size='Total CIF_ITEM',
            title="Mapa de Comuna del Importador con Estadísticas",
            zoom=4,
            height=800,
            template='plotly_dark'
        )
        fig_comunas.update_layout(mapbox_style="carto-positron")

        # Estadísticas y merge igual que en tu código
        puertos_stats = df.groupby(['PTO_EMB', 'PTO_DESEM']).agg({
            'CIF_ITEM': 'sum',
            'CANT_MERC': 'sum',
            'NUM_UNICO_IMPORTADOR': 'count'
        }).reset_index()
        puertos_stats.columns = ['Puerto de Embarque', 'Puerto de Desembarque', 'Total CIF_ITEM', 'Total Mercancías', 'Número de Transacciones']
        puertos_stats = puertos_stats.merge(puertos_coords, left_on='Puerto de Embarque', right_on='Puerto', how='left')
        puertos_stats = puertos_stats.merge(puertos_coords, left_on='Puerto de Desembarque', right_on='Puerto', how='left', suffixes=('_emb', '_desem'))
        puertos_stats['Latitud_emb'] = pd.to_numeric(puertos_stats['Latitud_emb'], errors='coerce')
        puertos_stats['Longitud_emb'] = pd.to_numeric(puertos_stats['Longitud_emb'], errors='coerce')
        puertos_stats['Latitud_desem'] = pd.to_numeric(puertos_stats['Latitud_desem'], errors='coerce')
        puertos_stats['Longitud_desem'] = pd.to_numeric(puertos_stats['Longitud_desem'], errors='coerce')
        puertos_stats = puertos_stats.dropna(subset=['Latitud_emb', 'Longitud_emb', 'Latitud_desem', 'Longitud_desem'])

        def calcular_puntos_curva(lat1, lon1, lat2, lon2, num_puntos=50):
            latitudes = np.linspace(lat1, lat2, num_puntos)
            longitudes = np.linspace(lon1, lon2, num_puntos)
            curvatura = np.sin(np.linspace(0, np.pi, num_puntos)) * 0.5
            longitudes += curvatura * (lon2 - lon1)
            return latitudes, longitudes

        def generar_color():
            return f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})"

        # Mapa base
        fig_puertos = go.Figure()

        # Puntos de embarque
        fig_puertos.add_trace(go.Scattermapbox(
            lat=puertos_stats['Latitud_emb'],
            lon=puertos_stats['Longitud_emb'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=12, color='blue'),
            text=puertos_stats['Puerto de Embarque'],
            name='Embarque'
        ))

        # Líneas entre puertos
        for _, row in puertos_stats.iterrows():
            latitudes, longitudes = calcular_puntos_curva(
                row['Latitud_emb'], row['Longitud_emb'],
                row['Latitud_desem'], row['Longitud_desem']
            )
            fig_puertos.add_trace(
                go.Scattermapbox(
                    lat=latitudes,
                    lon=longitudes,
                    mode='lines',
                    line=dict(width=2, color=generar_color()),
                    hoverinfo='none'
                )
            )

        fig_puertos.update_layout(
            mapbox_style="open-street-map",
            mapbox_center={"lat": -33.45, "lon": -70.65},
            mapbox_zoom=1.5,
            height=800,
            title="Mapa de Movimiento entre Puertos",
            template='plotly_dark'
        )

        return html.Div([
            html.Div(indicadores),
            html.H3("Gráficos principales"),
            dcc.Graph(figure=fig),
            dcc.Graph(figure=fig_section) if fig_section else None,
            dcc.Graph(figure=fig_monthly),
            dcc.Graph(figure=fig_monthly_kilos),
            dcc.Graph(figure=fig_monthly_kilos_cif),
            dcc.Graph(figure=fig_monthly_group_country_ADQ),
            dcc.Graph(figure=fig_monthly_group_country_ORG),
            html.H3("TOP 20 Productos con mayor frecuencia de compra"),
            dash_table.DataTable(
                data=top20_df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in top20_df.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),
            html.H3("TOP 20 Productos frecuentes with mayor valor de transacción por producto (última fecha)"),
            dash_table.DataTable(
                data=top20_trans_df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in top20_trans_df.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),
            html.H3("TOP 20 Transacciones individuales con mayor valor"),
            dash_table.DataTable(
                data=top20_trans_ind.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in top20_trans_ind.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),
            html.H3(" Precio Promedio por País de Adquisición"),
            dash_table.DataTable(
                data=precio_promedio_adq_df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in precio_promedio_adq_df.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),
            html.H3("Precio Promedio por País de Origen"),
            dash_table.DataTable(
                data=precio_promedio_origen_df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in precio_promedio_origen_df.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),
            html.H3("Heatmap de País de Origen en el Tiempo"),
            dcc.Graph(figure=fig_heatmap_origen),
            html.H3("Heatmap de País de Adquisición en el Tiempo"),
            dcc.Graph(figure=fig_heatmap_adq),
            html.H3("Mapa de Comunas con Estadísticas"),
            dcc.Graph(figure=fig_comunas),

            # NUEVO: Tabla de estadísticas por comuna
            html.H3("Estadísticas por Comuna"),
            dash_table.DataTable(
                data=comunas_stats.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in comunas_stats.columns],
                style_header={
                    'backgroundColor': '#23272b',
                    'color': '#00cec9',
                    'fontWeight': 'bold',
                    'border': '1px solid #444'
                },
                style_table={
                    'overflowX': 'auto',  # Scroll horizontal si es necesario
                    'maxWidth': '100vw',  # No se sale de la ventana
                    'minWidth': '100%',       # Ocupa todo el ancho disponible
                },
                style_cell={
                    'minWidth': '120px', 'width': '120px', 'maxWidth': '300px',
                    'whiteSpace': 'normal',  # Permite salto de línea en celdas
                    'backgroundColor': '#18191a',
                    'color': '#f5f6fa',
                    'border': '1px solid #444',
                    'fontFamily': 'Segoe UI, Arial, sans-serif',
                    'fontSize': '16px'
                },
                style_data={
                    'backgroundColor': '#23272b',
                    'color': '#f5f6fa'
                }
            ),

            html.H3("Mapa de Movimiento entre Puertos"),
            dcc.Graph(figure=fig_puertos)
        ])

    @app.callback(
        Output('section-dropdown', 'options'),
        Input('stored-data', 'data')
    )
    def update_section_options(data):
        if data is None:
            return []
        json_buffer = StringIO(data)
        df = pd.read_json(json_buffer, orient='split')
        df = agregar_section(df)  # <-- ¡Agrega esta línea!
        if 'Section' not in df.columns:
            return []
        sections = df['Section'].dropna().unique()
        return [{'label': s, 'value': s} for s in sorted(sections)]

    @app.callback(
        [Output('hsdesc-dropdown', 'options'),
         Output('hsdesc-dropdown', 'value')],
        [Input('stored-data', 'data'),
         Input('section-dropdown', 'value')],
        [State('hsdesc-dropdown', 'value')]
    )
    def update_hsdesc_options(data, section_value, hsdesc_value):
        if data is None:
            return [], None
        json_buffer = StringIO(data)
        df = pd.read_json(json_buffer, orient='split')
        df = agregar_section(df)
        if section_value:
            if isinstance(section_value, list):
                df = df[df['Section'].isin(section_value)]
            else:
                df = df[df['Section'] == section_value]
        if 'HS Description' not in df.columns:
            return [], None
        hsdescs = df['HS Description'].dropna().unique()
        options = [{'label': s, 'value': s} for s in sorted(hsdescs)]
        # Si el valor actual no está en las opciones, lo resetea
        if not hsdesc_value:
            return options, None
        if isinstance(hsdesc_value, list):
            hsdesc_value = [v for v in hsdesc_value if v in hsdescs]
            return options, hsdesc_value if hsdesc_value else None
        else:
            return options, hsdesc_value if hsdesc_value in hsdescs else None

def agregar_section(df):
    if 'ARANC_NAC' in df.columns:
        df_dict = pd.read_excel(
            DICCIONARIO_PATH,
            sheet_name='CATEGORIA_HS'
        )
        df_dict.columns = df_dict.columns.str.strip()
        df['Chapter'] = df['ARANC_NAC'].astype(str).str[:2]
        df_dict['Chapter'] = df_dict['Chapter'].astype(str).str[:2]
        df = pd.merge(df, df_dict[['Chapter', 'HS Description', 'Section']], on='Chapter', how='left')
    return df

