from flask import Blueprint, request
from controllers.usuario_controller import UsuarioController
from middleware.auth_middleware import token_required, roles_required

from flask import jsonify


usuario_bp = Blueprint("usuario_bp", __name__)

# CREATE
@usuario_bp.post("/create")
def crear_usuario():
    data = request.get_json()
    return UsuarioController.crear_usuario(data)


# LOGIN
@usuario_bp.post("/login")
def login():
    data = request.get_json()
    return UsuarioController.login(data)

# REFRESH
# REFRESH
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

@usuario_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    try:
        # get_jwt_identity() retrieves the identity stored in the refresh token
        identity = get_jwt_identity()
        
        # Create new access token
        new_access = create_access_token(identity=identity)
        
        return jsonify({"access_token": new_access}), 200
        
    except Exception as e:
         return jsonify({"error": "Error al renovar token", "details": str(e)}), 401



# EJEMPLO DE RUTA PROTEGIDA
@usuario_bp.get("/perfil")
@token_required
def perfil():
    return {"user": request.user}, 200


# EJEMPLO RUTA SOLO ADMIN
@usuario_bp.get("/admin-only")
@token_required
@roles_required(1)  # 1 = administrador
def admin_only():
    return {"message": "Bienvenido administrador"}, 200

@usuario_bp.post("/logout")
def logout():
    response = jsonify({"message": "Sesión cerrada"})
    response.set_cookie("refresh_token", "", expires=0)
    return response


@usuario_bp.get("/medicos")
@token_required
def get_medicos():
    return UsuarioController.get_medicos()


# ==========================================
# CRUD COMPLETO PARA GESTIÓN DE USUARIOS
# ==========================================

# GET - Listar todos los usuarios
@usuario_bp.get("/users")
@token_required
@roles_required(1)  # 1 = administrador
def listar_usuarios():
    """Lista todos los usuarios del sistema con filtros opcionales."""
    return UsuarioController.listar_usuarios()


# POST - Crear nuevo usuario
@usuario_bp.post("/users")
@token_required
@roles_required(1)  # 1 = administrador
def crear_usuario_nuevo():
    """Crea un nuevo usuario en el sistema."""
    data = request.get_json()
    return UsuarioController.crear_usuario_completo(data)


# GET - Obtener usuario por ID
@usuario_bp.get("/users/<int:usuario_id>")
@token_required
@roles_required(1)  # 1 = administrador
def obtener_usuario(usuario_id):
    """Obtiene un usuario específico por su ID."""
    return UsuarioController.obtener_usuario(usuario_id)


# PUT - Actualizar usuario
@usuario_bp.put("/users/<int:usuario_id>")
@token_required
@roles_required(1)  # 1 = administrador
def actualizar_usuario(usuario_id):
    """Actualiza un usuario existente."""
    data = request.get_json()
    return UsuarioController.actualizar_usuario(usuario_id, data)


# DELETE - Eliminar usuario
@usuario_bp.delete("/users/<int:usuario_id>")
@token_required
@roles_required(1)  # 1 = administrador
def eliminar_usuario(usuario_id):
    """Elimina un usuario del sistema."""
    return UsuarioController.eliminar_usuario(usuario_id)
