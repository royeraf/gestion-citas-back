from flask import jsonify
from models.rol_model import Rol
from models.especialidad_model import Especialidad
from models.area_model import Area

class CatalogoController:
    @staticmethod
    def get_roles():
        roles = Rol.query.all()
        return jsonify([r.to_dict() for r in roles]), 200

    @staticmethod
    def get_especialidades():
        especialidades = Especialidad.query.all()
        return jsonify([e.to_dict() for e in especialidades]), 200

    @staticmethod
    def get_areas():
        areas = Area.query.all()
        return jsonify([a.to_dict() for a in areas]), 200

    @staticmethod
    def get_estados_cita():
        from models.estado_cita_model import EstadoCita
        estados = EstadoCita.query.filter_by(activo=True).all()
        return jsonify([e.to_dict() for e in estados]), 200
