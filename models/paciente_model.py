from extensions.database import db
from datetime import datetime
from models.persona_model import Persona

class Paciente(db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    
    # Normalización: Relación con tabla personas
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=True)
    persona = db.relationship('Persona', backref=db.backref('paciente', uselist=False))
    
    @property
    def dni(self):
        return self.persona.dni if self.persona else None
    
    @dni.setter
    def dni(self, value):
        if self.persona: self.persona.dni = value

    @property
    def nombres(self):
        return self.persona.nombres if self.persona else ""
    
    @nombres.setter
    def nombres(self, value):
        if self.persona: self.persona.nombres = value

    @property
    def apellido_paterno(self):
        return self.persona.apellido_paterno if self.persona else ""
    
    @apellido_paterno.setter
    def apellido_paterno(self, value):
        if self.persona: self.persona.apellido_paterno = value

    @property
    def apellido_materno(self):
        return self.persona.apellido_materno if self.persona else ""
    
    @apellido_materno.setter
    def apellido_materno(self, value):
        if self.persona: self.persona.apellido_materno = value

    @property
    def fecha_nacimiento(self):
        return self.persona.fecha_nacimiento if self.persona else None
    
    @fecha_nacimiento.setter
    def fecha_nacimiento(self, value):
        if self.persona: self.persona.fecha_nacimiento = value

    @property
    def sexo(self):
        return self.persona.sexo if self.persona else None
    
    @sexo.setter
    def sexo(self, value):
        if self.persona: self.persona.sexo = value

    @property
    def telefono(self):
        return self.persona.telefono if self.persona else None
    
    @telefono.setter
    def telefono(self, value):
        if self.persona: self.persona.telefono = value

    @property
    def email(self):
        return self.persona.email if self.persona else None
    
    @email.setter
    def email(self, value):
        if self.persona: self.persona.email = value

    @property
    def direccion(self):
        return self.persona.direccion if self.persona else None
    
    @direccion.setter
    def direccion(self, value):
        if self.persona: self.persona.direccion = value

    estado_civil = db.Column(db.String(1), nullable=False)
    grado_instruccion = db.Column(db.Enum(
        'inicial_incompleta', 'inicial_completa', 
        'primaria_incompleta', 'primaria_completa', 
        'secundaria_incompleta', 'secundaria_completa', 
        'tecnico_superior_incompleta', 'tecnico_superior_completa', 
        'universitario_incompleto', 'universitario_completo',
        name='grado_instruccion_enum'
    ))

    religion = db.Column(db.String(50))
    procedencia = db.Column(db.String(50))
    ocupacion = db.Column(db.String(100))  # Ocupación del paciente
    
    seguro = db.Column(db.String(50))
    numero_seguro = db.Column(db.String(50))  # Número de afiliación al seguro

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # Calcular edad
        today = datetime.now().date()
        age = 0
        f_nac = self.fecha_nacimiento
        if f_nac:
            age = today.year - f_nac.year - ((today.month, today.day) < (f_nac.month, f_nac.day))

        return {
            "id": self.id,
            "persona_id": self.persona_id,
            "dni": self.dni,
            "nombres": self.nombres,
            "apellido_paterno": self.apellido_paterno,
            "apellidoPaterno": self.apellido_paterno,
            "apellido_materno": self.apellido_materno,
            "apellidoMaterno": self.apellido_materno,
            "fecha_nacimiento": str(f_nac) if f_nac else None,
            "fechaNacimiento": str(f_nac) if f_nac else None,
            "edad": age,
            "sexo": self.sexo,
            "estado_civil": self.estado_civil,
            "grado_instruccion": self.grado_instruccion,
            "religion": self.religion,
            "procedencia": self.procedencia,
            "ocupacion": self.ocupacion,
            "telefono": self.telefono,
            "email": self.email,
            "direccion": self.direccion,
            "seguro": self.seguro,
            "numero_seguro": self.numero_seguro,
            "fecha_registro": str(self.fecha_registro)
        }
