from dash import html, dcc
import dash_uploader as du
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def create_layout(app):
    #du.configure_upload(app, "uploads")
    return html.Div([
        html.Img(src='/assets/logo.png', style={'height': '200px', 'margin-bottom': '20px'}),
        html.H2("Dashboard de Importaciones", className="my-header"),
        du.Upload(
            id='dash-uploader',
            text='Arrastra o selecciona tu archivo CSV o TXT de importaciones',
            max_files=1,
            filetypes=['csv', 'txt'],
            upload_id='auto',
        ),
        dcc.Store(id='stored-data'),
        html.Div([
            html.Label("Filtrar por rango de fechas:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                display_format='YYYY-MM-DD'
            ),
            html.Br(),
            html.Label("Buscar por nombre en PRODUCTO:"),
            dcc.Input(id='search-producto', type='text', placeholder='Términos separados por coma'),
            html.Br(),
            html.Label("Buscar por importador:"),
            dcc.Input(id='search-importador', type='text', placeholder='Términos separados por coma'),
            html.Br(),
            html.Label("Buscar por país de origen:"),
            dcc.Input(id='search-pa-orig', type='text', placeholder='Términos separados por coma'),
            html.Br(),
            html.Label("Buscar por país de adquisición:"),
            dcc.Input(id='search-pa-adq', type='text', placeholder='Términos separados por coma'),
            html.Br(),
            html.Label("Buscar por comuna:"),
            dcc.Input(id='search-comuna', type='text', placeholder='Términos separados por coma'),
            html.Br(),
            html.Label("Selecciona columna para graficar:"),
            dcc.Dropdown(
                id='column-dropdown',
                options=[{'label': col, 'value': col} for col in ['NUM_UNICO_IMPORTADOR','PA_ORIG', 'PA_ADQ', 'TPO_CARGA', 'VIA_TRAN', 'TPO_BUL1', 'TPO_BUL2']],
                value='NUM_UNICO_IMPORTADOR'
            )
        ], id='filters-container', style={'backgroundColor': '#23272b', 'padding': '20px', 'borderRadius': '10px', 'margin-bottom': '30px'}),
        html.Div([
            html.Label("Filtrar por Section"),
            dcc.Dropdown(
                id='section-dropdown',
                options=[],  # Se llena dinámicamente
                multi=True,  # <--- Esto permite seleccionar varias opciones
                placeholder="Selecciona una o varias secciones"
            )
        ], style={'backgroundColor': '#23272b', 'padding': '20px', 'borderRadius': '10px', 'margin-bottom': '30px'}),
        html.Div([
            html.Label("Filtrar por HS Description"),
            dcc.Dropdown(
                id='hsdesc-dropdown',
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Selecciona una o varias descripciones HS"
            )
        ], style={'backgroundColor': '#23272b', 'padding': '20px', 'borderRadius': '10px', 'margin-bottom': '30px'}),
        html.Div(id='output-visualizations')
    ], style={'padding': '40px', 'backgroundColor': '#18191a', 'minHeight': '100vh'})