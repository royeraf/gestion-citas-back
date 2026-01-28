from flask_jwt_extended import JWTManager
from models.usuario_model import Usuario

jwt = JWTManager()

@jwt.user_identity_loader
def user_identity_lookup(user):
    # If it's a dict (legacy support), return the id as string
    if isinstance(user, dict):
        return str(user.get("id"))
    # If it's the User model object
    if hasattr(user, 'id'):
        return str(user.id)
    # Default return as string
    return str(user)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Usuario.query.filter_by(id=identity).first()

