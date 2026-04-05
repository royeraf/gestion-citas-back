from flask import Blueprint
from controllers.reporte_controller import ReporteController
from middleware.auth_middleware import token_required

reporte_bp = Blueprint('reportes', __name__)

@reporte_bp.route('/estadisticas', methods=['GET'])
@token_required
def obtener_estadisticas():
    return ReporteController.obtener_estadisticas()

@reporte_bp.route('/exportar-pdf', methods=['GET'])
@token_required
def exportar_pdf():
    return ReporteController.exportar_pdf()
