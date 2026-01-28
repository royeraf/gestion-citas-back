from extensions.database import db
from datetime import datetime

class EstadoCita(db.Model):
    __tablename__ = "estados_cita"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(20), nullable=True) # Para uso en frontend (badges)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "color": self.color,
            "activo": self.activo
        }
