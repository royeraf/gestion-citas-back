from flask import Blueprint, request
from controllers.especialidad_controller import EspecialidadController
from middleware.auth_middleware import token_required

especialidad_bp = Blueprint("especialidad_bp", __name__)

@especialidad_bp.get("/")
@token_required
def get_especialidades():
    return EspecialidadController.get_all()

@especialidad_bp.post("/")
@token_required
def create_especialidad():
    data = request.get_json()
    return EspecialidadController.create(data)

@especialidad_bp.put("/<int:id>")
@token_required
def update_especialidad(id):
    data = request.get_json()
    return EspecialidadController.update(id, data)

@especialidad_bp.delete("/<int:id>")
@token_required
def delete_especialidad(id):
    return EspecialidadController.delete(id)
