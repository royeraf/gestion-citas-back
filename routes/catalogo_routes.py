from flask import Blueprint
from controllers.catalogo_controller import CatalogoController

catalogo_bp = Blueprint("catalogo_bp", __name__)

@catalogo_bp.get("/roles")
def get_roles():
    return CatalogoController.get_roles()

@catalogo_bp.get("/especialidades")
def get_especialidades():
    return CatalogoController.get_especialidades()

@catalogo_bp.get("/areas")
def get_areas():
    return CatalogoController.get_areas()

@catalogo_bp.get("/estados-cita")
def get_estados_cita():
    return CatalogoController.get_estados_cita()
