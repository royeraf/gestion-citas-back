from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from routes.paciente_route import paciente_bp
from routes.dni_routes import dni_bp
from routes.usuario_routes import usuario_bp
from routes.area_routes import area_bp
from routes.cita_routes import cita_bp
from routes.horario_routes import horario_bp
from routes.dashboard_routes import dashboard_bp
from routes.medico_routes import medico_bp  # Nuevo import para medicos
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from extensions.database import db
from flask_cors import CORS

app = Flask(__name__)

# SECRET KEY para JWT
app.config["SECRET_KEY"] = "super_clave_secreta"  # cambia esto

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

# Configuración optimizada para Supabase (evita errores de conexión perdida y límite de clientes)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,                # Mantener máximo 5 conexiones abiertas
    'max_overflow': 2,             # Permitir solo 2 conexiones extra temporales
    'pool_recycle': 300,           # Reciclar conexiones cada 5 minutos
    'pool_pre_ping': True,         # Verificar conexión antes de usarla
    'pool_timeout': 30             # Tiempo máximo de espera por una conexión
}

# CORS CORRECTO para Vue.js + Cookies + JWT
CORS(app,
     origins=["http://localhost:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Inicializar DB
db.init_app(app)



# Rutas API (ahora con prefijo /api)
app.register_blueprint(paciente_bp, url_prefix="/api/pacientes")
app.register_blueprint(dni_bp, url_prefix="/api/dni")
app.register_blueprint(usuario_bp, url_prefix="/api/auth")
app.register_blueprint(area_bp, url_prefix="/api/areas")
app.register_blueprint(cita_bp, url_prefix="/api/citas")
app.register_blueprint(horario_bp, url_prefix="/api/horarios")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(medico_bp, url_prefix="/api/medicos")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
