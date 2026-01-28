from extensions.database import db
from datetime import datetime

class Persona(db.Model):
    __tablename__ = "personas"

    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(8), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    sexo = db.Column(db.String(1), nullable=True) # M, F
    telefono = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "dni": self.dni,
            "nombres": self.nombres,
            "apellido_paterno": self.apellido_paterno,
            "apellido_materno": self.apellido_materno,
            "nombre_completo": f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}",
            "fecha_nacimiento": str(self.fecha_nacimiento) if self.fecha_nacimiento else None,
            "sexo": self.sexo,
            "telefono": self.telefono,
            "email": self.email,
            "direccion": self.direccion
        }
