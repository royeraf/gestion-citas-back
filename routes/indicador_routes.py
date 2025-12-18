"""
Rutas de Indicadores de Gestión de Citas Médicas.
Endpoints para la tesis - 3 dimensiones de análisis.
"""

from flask import Blueprint
from controllers.indicador_controller import IndicadorController
from middleware.auth_middleware import token_required

indicador_bp = Blueprint('indicadores', __name__)


@indicador_bp.route('/', methods=['GET'])
@token_required
def obtener_indicadores():
    """
    GET /api/indicadores/
    Obtiene los 3 indicadores principales para un período.
    
    Query params:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    - area_id: (opcional)
    """
    return IndicadorController.obtener_indicadores()


@indicador_bp.route('/tendencia', methods=['GET'])
@token_required
def obtener_indicadores_tendencia():
    """
    GET /api/indicadores/tendencia
    Obtiene indicadores agrupados por período (día, semana, mes).
    
    Query params:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    - agrupacion: 'dia' | 'semana' | 'mes'
    - area_id: (opcional)
    """
    return IndicadorController.obtener_indicadores_por_periodo()


@indicador_bp.route('/por-area', methods=['GET'])
@token_required
def obtener_indicadores_por_area():
    """
    GET /api/indicadores/por-area
    Obtiene indicadores comparativos por área/especialidad.
    
    Query params:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    """
    return IndicadorController.obtener_indicadores_por_area()
