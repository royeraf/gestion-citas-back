from extensions.database import db
from datetime import datetime

# Tabla pivote para relación médico - especialidad
medico_especialidad = db.Table('medico_especialidad',
    db.Column('medico_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('especialidad_id', db.Integer, db.ForeignKey('especialidades.id'), primary_key=True)
)

class Especialidad(db.Model):
    __tablename__ = "especialidades"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación muchos a muchos
    medicos = db.relationship('Usuario', secondary=medico_especialidad, backref=db.backref('especialidades', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "activo": self.activo
        }
