from extensions.database import db
from datetime import datetime
from models.estado_cita_model import EstadoCita

class Cita(db.Model):
    __tablename__ = "citas"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horarios_medicos.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    fecha = db.Column(db.Date, nullable=True)  # Fecha de la cita
    sintomas = db.Column(db.Text, nullable=False)
    
    datos_adicionales = db.Column(db.JSON)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Normalización: Estado de la cita
    estado_id = db.Column(db.Integer, db.ForeignKey('estados_cita.id'), nullable=True)
    estado_rel = db.relationship('EstadoCita', backref=db.backref('citas', lazy=True))

    # Normalización: Acompañante
    acompanante_persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=True)
    acompanante = db.relationship('Persona', foreign_keys=[acompanante_persona_id], backref=db.backref('acompanando', lazy=True))

    # Relaciones
    paciente = db.relationship('Paciente', backref=db.backref('citas', lazy=True))
    horario = db.relationship('HorarioMedico', backref=db.backref('citas', lazy=True))
    doctor = db.relationship('Usuario', backref=db.backref('citas_asignadas', lazy=True))
    area_rel = db.relationship('Area', backref=db.backref('citas', lazy=True))

    @property
    def estado_nombre(self):
        return self.estado_rel.nombre if self.estado_rel else "pendiente"

    @property
    def area(self):
        return self.area_rel.nombre if self.area_rel else None

    @property
    def estado(self):
        return self.estado_nombre

    @property
    def dni_acompanante(self):
        return self.acompanante.dni if self.acompanante else None
    
    @property
    def nombre_acompanante(self):
        if self.acompanante:
            return f"{self.acompanante.nombres} {self.acompanante.apellido_paterno} {self.acompanante.apellido_materno}".strip()
        return None

    @property
    def nombres_acompanante_only(self):
         return self.acompanante.nombres if self.acompanante else None

    @property
    def telefono_acompanante(self):
        return self.acompanante.telefono if self.acompanante else None

    @property
    def apellido_paterno_acompanante(self):
        return self.acompanante.apellido_paterno if self.acompanante else None

    @property
    def apellido_materno_acompanante(self):
        return self.acompanante.apellido_materno if self.acompanante else None

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "horario_id": self.horario_id,
            "doctor_id": self.doctor_id,
            "area_id": self.area_id,
            "area": self.area,
            "fecha": str(self.fecha) if self.fecha else None,
            "sintomas": self.sintomas,
            "dni_acompanante": self.dni_acompanante,
            "nombre_acompanante": self.nombre_acompanante, # Nombre completo para backward compatibility
            "nombres_acompanante": self.nombres_acompanante_only,
            "apellido_paterno_acompanante": self.apellido_paterno_acompanante,
            "apellido_materno_acompanante": self.apellido_materno_acompanante,
            "telefono_acompanante": self.telefono_acompanante,
            "datos_adicionales": self.datos_adicionales,
            "fecha_registro": str(self.fecha_registro),
            
            # Estado normalizado
            "estado": self.estado_nombre,
            "estado_info": self.estado_rel.to_dict() if self.estado_rel else None,
            "color_estado": self.estado_rel.color if self.estado_rel else "blue",
            
            # Datos adicionales de relaciones
            "doctor_nombre": self.doctor.nombres_completos if self.doctor else None,
            "area_nombre": self.area_rel.nombre if self.area_rel else self.area,
            "horario_turno": self.horario.turno if self.horario else None,
            "horario_turno_nombre": self.horario.turno_nombre if self.horario else None,
        }
