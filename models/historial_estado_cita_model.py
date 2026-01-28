from extensions.database import db
from datetime import datetime

class HistorialEstadoCita(db.Model):
    """
    Modelo para registrar el historial de cambios de estado de las citas.
    Cada vez que una cita cambia de estado, se registra aquí con:
    - El estado anterior y el nuevo estado (referencia a estados_cita)
    - El usuario que realizó el cambio
    - La fecha y hora del cambio
    - Opcionalmente, un comentario o motivo
    """
    __tablename__ = "historial_estado_citas"

    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    
    # Normalización: Referencias a la tabla estados_cita
    estado_anterior_id = db.Column(db.Integer, db.ForeignKey('estados_cita.id'), nullable=True)
    estado_nuevo_id = db.Column(db.Integer, db.ForeignKey('estados_cita.id'), nullable=False)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)
    comentario = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    # Relaciones
    cita = db.relationship('Cita', backref=db.backref('historial_estados', lazy='dynamic', order_by='HistorialEstadoCita.fecha_cambio.desc()'))
    usuario = db.relationship('Usuario', backref=db.backref('cambios_estado_citas', lazy=True))
    
    estado_anterior = db.relationship('EstadoCita', foreign_keys=[estado_anterior_id])
    estado_nuevo = db.relationship('EstadoCita', foreign_keys=[estado_nuevo_id])

    def to_dict(self):
        return {
            "id": self.id,
            "cita_id": self.cita_id,
            "estado_anterior": self.estado_anterior.nombre if self.estado_anterior else None,
            "estado_anterior_id": self.estado_anterior_id,
            "estado_nuevo": self.estado_nuevo.nombre if self.estado_nuevo else None,
            "estado_nuevo_id": self.estado_nuevo_id,
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario.nombres_completos if self.usuario else "Sistema",
            "fecha_cambio": self.fecha_cambio.isoformat() if self.fecha_cambio else None,
            "comentario": self.comentario,
            "ip_address": self.ip_address
        }

    @staticmethod
    def registrar_cambio(cita_id, estado_anterior_id, estado_nuevo_id, usuario_id=None, comentario=None, ip_address=None):
        """
        Método estático para registrar un cambio de estado de manera normalizada.
        """
        historial = HistorialEstadoCita(
            cita_id=cita_id,
            estado_anterior_id=estado_anterior_id,
            estado_nuevo_id=estado_nuevo_id,
            usuario_id=usuario_id,
            comentario=comentario,
            ip_address=ip_address
        )
        db.session.add(historial)
        return historial
