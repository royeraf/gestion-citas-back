import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from extensions.database import db
from extensions.jwt_manager import jwt
from config import config

# Import Routes
from routes.paciente_route import paciente_bp
from routes.dni_routes import dni_bp
from routes.usuario_routes import usuario_bp
from routes.area_routes import area_bp
from routes.cita_routes import cita_bp
from routes.horario_routes import horario_bp
from routes.dashboard_routes import dashboard_bp
from routes.medico_routes import medico_bp
from routes.indicador_routes import indicador_bp

def create_app(config_name=None):
    load_dotenv()
    
    if config_name is None:
        config_name = 'production' if os.getenv('FLASK_ENV') == 'production' else 'development'
        
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # CORS Configuration
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    allowed_origins = [frontend_url]
    if "," in frontend_url:
        allowed_origins = [url.strip() for url in frontend_url.split(",")]
        
    if app.debug:
        allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
        allowed_origins = list(set(allowed_origins))
        
    CORS(app,
         origins=allowed_origins,
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    
    # Register Blueprints
    app.register_blueprint(paciente_bp, url_prefix="/api/pacientes")
    app.register_blueprint(dni_bp, url_prefix="/api/dni")
    app.register_blueprint(usuario_bp, url_prefix="/api/auth")
    app.register_blueprint(area_bp, url_prefix="/api/areas")
    app.register_blueprint(cita_bp, url_prefix="/api/citas")
    app.register_blueprint(horario_bp, url_prefix="/api/horarios")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(medico_bp, url_prefix="/api/medicos")
    app.register_blueprint(indicador_bp, url_prefix="/api/indicadores")
    
    # Global Health Check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "message": "API Citas Médicas funcionando correctamente (App Factory)"
        }), 200

    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            "message": "API Citas Médicas - Centro de Salud La Unión",
            "version": "1.0.0",
            "docs": "/api/health"
        }), 200

    return app
