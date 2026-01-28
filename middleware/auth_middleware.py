from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, current_user

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            # current_user is populated by user_lookup_loader in extensions/jwt_manager.py
            if not current_user:
                return jsonify({"error": "Usuario no encontrado"}), 401
            
            request.user = current_user.to_dict()
        except Exception as e:
            return jsonify({"error": "Token inválido o expirado", "details": str(e)}), 401


        return f(*args, **kwargs)
    return decorated


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def middleware(*args, **kwargs):
            if not hasattr(request, "user") or not request.user:
                return jsonify({"error": "No autenticado"}), 403

            # rol_id: 1=administrador, 2=profesional, 3=asistente
            user_role = request.user.get("rol_id")

            if user_role not in roles:
                return jsonify({"error": "No autorizado"}), 403

            return f(*args, **kwargs)
        return middleware
    return decorator
