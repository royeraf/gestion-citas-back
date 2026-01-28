from extensions.database import db
from models.paciente_model import Paciente
from models.cita_model import Cita
from models.usuario_model import Usuario
from models.area_model import Area
from models.estado_cita_model import EstadoCita
from models.horario_medico_model import HorarioMedico
from datetime import date
from sqlalchemy import func

def get_dashboard_stats():
    today = date.today()
    
    total_pacientes = Paciente.query.count()
    citas_hoy = Cita.query.filter(Cita.fecha == today).count()
    
    # Citas pendientes hoy usando relacion
    citas_pendientes_hoy = Cita.query.join(EstadoCita).filter(Cita.fecha == today, EstadoCita.nombre == 'pendiente').count()
    # Corregido: rol_id es 2 para medicos segun insert_medicos.py y usuario_controller.py
    medicos_activos = Usuario.query.filter(Usuario.rol_id == 2, Usuario.activo == True).count()
    # Citas pendientes total usando relacion
    citas_pendientes_total = Cita.query.join(EstadoCita).filter(EstadoCita.nombre == 'pendiente').count()

    return {
        "totalPacientes": total_pacientes,
        "citasHoy": citas_hoy,
        "citasPendientesHoy": citas_pendientes_hoy,
        "medicosActivos": medicos_activos,
        "citasPendientesTotal": citas_pendientes_total
    }

def get_upcoming_appointments(user_rol_id=None, user_id=None):
    today = date.today()
    
    # Get upcoming appointments (today and future)
    query = Cita.query.filter(Cita.fecha >= today)

    # Lógica de filtrado por rol (usando EstadoCita para normalizacion)
    # 2 = Profesional: debe de verse solo las citas confirmadas para el
    if user_rol_id == 2:
        query = query.join(EstadoCita).filter(Cita.doctor_id == user_id, EstadoCita.nombre == 'confirmada')
    # 3 = Tecnico/Asistente: debe de verse las citas pendientes por confirmar (todas)
    elif user_rol_id == 3:
        query = query.join(EstadoCita).filter(EstadoCita.nombre == 'pendiente')
    
    # Ordenar por fecha y luego obtener las próximas 10 citas
    citas = query.order_by(Cita.fecha.asc())\
        .limit(10).all()
        
    proximas_citas = []
    for cita in citas:
        # Formatear la hora/turno. 
        hora = "Por definir"
        if cita.horario:
             hora = f"{cita.horario.hora_inicio.strftime('%I:%M %p')}" if hasattr(cita.horario, 'hora_inicio') and cita.horario.hora_inicio else "Turno " + str(cita.horario.turno)

        proximas_citas.append({
            "id": cita.id,
            "fecha": str(cita.fecha),
            "hora": hora,
            "paciente": f"{cita.paciente.nombres} {cita.paciente.apellido_paterno} {cita.paciente.apellido_materno}" if cita.paciente else "Desconocido",
            "doctor": f"{cita.doctor.nombres_completos}" if cita.doctor else "Sin asignar",
            "especialidad": cita.area_rel.nombre if cita.area_rel else "General",
            "estado": cita.estado_rel.nombre.capitalize() if cita.estado_rel else "Pendiente"
        })
        
    return proximas_citas

def get_appointments_by_specialty_today():
    today = date.today()
    
    # Agrupar por Area
    # Join Cita -> Area
    stats = db.session.query(Area.nombre, func.count(Cita.id))\
        .join(Cita, Area.id == Cita.area_id)\
        .filter(Cita.fecha == today)\
        .group_by(Area.nombre).all()
        
    total_citas_hoy = sum([count for _, count in stats])
    
    citas_por_especialidad = []
    for nombre, cantidad in stats:
        porcentaje = (cantidad / total_citas_hoy * 100) if total_citas_hoy > 0 else 0
        citas_por_especialidad.append({
            "nombre": nombre,
            "cantidad": cantidad,
            "porcentaje": round(porcentaje, 1)
        })
        
    # Si no hay citas hoy, devolver lista vacia o manejada en frontend
    return citas_por_especialidad
