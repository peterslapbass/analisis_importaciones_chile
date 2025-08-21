from dash import Dash
import layout
import callbacks
import os
import dash_uploader as du

# Establecer ruta base
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Crear la app
app = Dash(__name__, suppress_callback_exceptions=True)

# Configurar carpeta de uploads
UPLOAD_FOLDER_ROOT = os.path.join(os.getcwd(), 'uploads')
du.configure_upload(app, UPLOAD_FOLDER_ROOT)

# Layout y callbacks
app.layout = layout.create_layout(app)
callbacks.register_callbacks(app)

# Ejecutar
if __name__ == '__main__':
    app.run(debug=False)
