from flask import Blueprint
from controllers.horario_controller import HorarioController
from middleware.auth_middleware import token_required

horario_bp = Blueprint('horario_bp', __name__)

# Crear horarios mensuales (nuevo endpoint principal)
horario_bp.route('/mensual', methods=['POST'])(token_required(HorarioController.create_horarios_mensuales))

# Obtener resumen de horarios por mes (para calendario)
horario_bp.route('/resumen', methods=['GET'])(token_required(HorarioController.get_horarios_resumen_mes))

# Eliminar horarios de un mes completo
horario_bp.route('/mensual', methods=['DELETE'])(token_required(HorarioController.delete_horarios_mes))

# Crear o actualizar horario individual (compatible con nuevo formato)
horario_bp.route('/', methods=['POST'])(token_required(HorarioController.create_or_update_horario))

# Obtener lista de horarios (con filtros opcionales: area_id, medico_id, mes, fecha, turno)
horario_bp.route('/', methods=['GET'])(token_required(HorarioController.get_horarios))

# Eliminar horario individual por ID
horario_bp.route('/<int:id>', methods=['DELETE'])(token_required(HorarioController.delete_horario))

# Actualizar horario individual por ID (cupos, area_id)
horario_bp.route('/<int:id>', methods=['PUT'])(token_required(HorarioController.update_horario))

# Obtener horarios de un médico (Legacy/Specific)
horario_bp.route('/medico/<int:medico_id>', methods=['GET'])(token_required(HorarioController.get_horarios_by_medico))

# Obtener horarios por área (Legacy/Specific)
horario_bp.route('/area/<int:area_id>', methods=['GET'])(token_required(HorarioController.get_horarios_by_area))
