from extensions.database import db
from datetime import datetime
from models.rol_model import Rol
from models.persona_model import Persona

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    # El username ahora es redundante, usamos el DNI de la persona vinculada
    # username = db.Column(db.String(50), unique=True, nullable=True) # SE ELIMINA DE BD
    password = db.Column(db.Text, nullable=False)
    
    # Normalización: Relación con tabla personas
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    persona = db.relationship('Persona', backref=db.backref('usuario', uselist=False))

    @property
    def username(self):
        return self.dni
    
    @username.setter
    def username(self, value):
        self.dni = value

    @property
    def dni(self):
        return self.persona.dni if self.persona else None
    
    @dni.setter
    def dni(self, value):
        if self.persona:
            self.persona.dni = value
        # Si se usa durante la creación antes de que persona esté cargada por la relación
        # pero persona ya fue asignada al objeto persona_id, SQLAlchemy lo manejará
        # al persistir si asignamos directamente al objeto persona si está disponible.

    @property
    def nombres_completos(self):
        if self.persona:
            return f"{self.persona.nombres} {self.persona.apellido_paterno} {self.persona.apellido_materno}".strip()
        return ""
    
    @nombres_completos.setter
    def nombres_completos(self, value):
        if self.persona and value:
            # Lógica básica para dividir nombre completo si se asigna directamente
            parts = value.split()
            if len(parts) >= 3:
                self.persona.nombres = " ".join(parts[:-2])
                self.persona.apellido_paterno = parts[-2]
                self.persona.apellido_materno = parts[-1]
            elif len(parts) == 2:
                self.persona.nombres = parts[0]
                self.persona.apellido_paterno = parts[1]
            else:
                self.persona.nombres = value

    # Normalización: Relación con tabla roles
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    rol = db.relationship('Rol', backref=db.backref('usuarios', lazy=True))

    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "dni": self.dni,
            "username": self.username,
            "nombres_completos": self.nombres_completos,
            "rol_id": self.rol_id,
            "rol_nombre": self.rol.nombre if self.rol else None,
            "activo": self.activo,
            "especialidades": [esp.to_dict() for esp in self.especialidades.all()] if self.rol_id == 2 else []
        }
