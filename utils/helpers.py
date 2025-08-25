import pandas as pd
import unicodedata
import os


# Ruta centralizada del diccionario de estructura
DESCRIPCION_PATH = os.path.join('data', 'descripcion-y-estructura-de-datos.xlsx')
DESCRIPCION_SHEET = 'DIN'  # Ajustable si usás otra hoja

def cargar_descripcion_estructura():
    """
    Carga los nombres de columnas desde el diccionario estructural.
    Usa la columna 'CAMPO - DIN -  ENCABEZADO' como base y limpia los espacios.
    Retorna una lista de nombres de columnas limpios.
    """
    df_descrip = pd.read_excel(DESCRIPCION_PATH, sheet_name=DESCRIPCION_SHEET, header=1)
    
    if 'CAMPO - DIN -  ENCABEZADO' not in df_descrip.columns:
        raise ValueError("No se encontró la columna 'CAMPO - DIN -  ENCABEZADO' en el diccionario.")

    columnas = (
        df_descrip['CAMPO - DIN -  ENCABEZADO']
        .dropna()
        .astype(str)
        .str.strip()
        .str.replace(' ', '')
        .tolist()
    )
    return columnas



def leer_txt_sin_encabezado(filepath, delimiter=';', decimal=','):
    columnas = cargar_descripcion_estructura()
    return pd.read_csv(
        filepath,
        header=None,
        names=columnas,
        delimiter=delimiter,
        encoding='latin1',
        decimal=decimal,
        on_bad_lines='skip',
        low_memory=False
    )



DICCIONARIO_PATH = os.path.join('data', 'DICCIONARIO.xlsx')

def cargar_diccionarios():
    return {
        'PAIS': pd.read_excel(DICCIONARIO_PATH, sheet_name='PAIS').set_index('Código')['Glosa'].to_dict(),
        'BULTO': pd.read_excel(DICCIONARIO_PATH, sheet_name='BULTO').set_index('Código')['Glosa'].to_dict(),
        'CARGA': pd.read_excel(DICCIONARIO_PATH, sheet_name='CARGA').set_index('Código')['Glosa'].to_dict(),
        'TRANSPORTE': pd.read_excel(DICCIONARIO_PATH, sheet_name='TRANSPORTE').set_index('Código')['Glosa'].to_dict(),
        'COMUNA': pd.read_excel(DICCIONARIO_PATH, sheet_name='COMUNA').set_index('Código')['Glosa'].to_dict(),
        'ADUANA': pd.read_excel(DICCIONARIO_PATH, sheet_name='ADUANA').set_index('Código')['Glosa'].to_dict(),
        'PUERTOS': pd.read_excel(DICCIONARIO_PATH, sheet_name='PUERTOS').set_index('Código')['Glosa'].to_dict(),
        'OPERACION': pd.read_excel(DICCIONARIO_PATH, sheet_name='OPERACION').set_index('Código')['Glosa'].to_dict()
    }


# Diccionario de códigos HS y sus industrias
hs_industries = {
    '3004': 'Farmacéutica',
    '2710': 'Petroquímica',
    '3901': 'Plásticos',
    '3902': 'Plásticos',
    '3903': 'Plásticos',
    '3904': 'Plásticos',
    '3907': 'Resinas',
    '3908': 'Resinas',
    '3910': 'Resinas',
    '3911': 'Resinas',
    '3824': 'Aditivos para Plásticos',
    '3407': 'Aditivos para Plásticos',
    '3808': 'Químicos - Agroquímicos/Desinfectantes',
    '3304': 'Químicos - Industria Cosmética',
    '2830': 'Minería',
    '2815': 'Minería',
    '2707': 'Minería',
    '7201': 'Fundición',
    '7202': 'Fundición',
    '8111': 'Fundición',
    '2827': 'Tratamiento de Aguas',
    '2833': 'Tratamiento de Aguas',
    '2828': 'Tratamiento de Aguas',
    '4801': 'Industria del Papel',
    '4802': 'Industria del Papel',
    '4810': 'Industria del Papel',
    '4707': 'Industria del Papel',
    '3809': 'Industria del Papel - Aditivos'
}

def asignar_industria(codigo_hs):
    codigo_hs = str(codigo_hs)[:4]
    return hs_industries.get(codigo_hs, 'Industria Desconocida')

def eliminar_acentos(texto):
    if isinstance(texto, str):
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto

# Cargar import.csv y crear diccionario
import_df = pd.read_csv(os.path.join('data', 'import.txt'), sep='\t', encoding='utf-8')
import_df['RUT'] = import_df['RUT'].astype(str).str.strip()
import_dict = dict(zip(import_df['RUT'], import_df['RAZON_SOCIAL']))

# Cargar comunas y puertos
comunas_df = pd.read_csv(os.path.join('data', 'comunas.csv'))
puertos_coords = pd.read_csv(os.path.join('data', 'puertos_coordenadas.csv'))

#Enriquecer datos
def enriquecer_dataframe(df, dicts):
    mapeos = {
        'PA_ORIG': dicts['PAIS'],
        'PA_ADQ': dicts['PAIS'],
        'VIA_TRAN': dicts['TRANSPORTE'],
        'TPO_CARGA': dicts['CARGA'],
        'ID_BULTOS': dicts['BULTO'],
        'CODCOMUN': dicts['COMUNA'],
        'ADU': dicts['ADUANA'],
        'PTO_DESEM': dicts['PUERTOS'],
        'PTO_EMB': dicts['PUERTOS'],
        'TPO_DOCTO': dicts['OPERACION']
    }

    for col, mapping in mapeos.items():
        if col in df.columns:
            df[col] = df[col].map(mapping)

    for i in range(1, 9):
        col = f'TPO_BUL{i}'
        if col in df.columns:
            df[col] = df[col].map(dicts['BULTO'])

    return df
