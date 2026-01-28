from flask import jsonify, request, send_file, Response
from extensions.database import db
from models.cita_model import Cita
from models.paciente_model import Paciente
from models.horario_medico_model import HorarioMedico
from models.area_model import Area
from models.usuario_model import Usuario
from models.persona_model import Persona
from models.estado_cita_model import EstadoCita
from models.historial_estado_cita_model import HistorialEstadoCita

from services.pdf_service import PDFService
from datetime import datetime

class CitaController:

    @staticmethod
    def listar():
        """
        Listar citas con filtros y paginación.
        
        IMPORTANTE: Si el usuario autenticado es un profesional (rol_id = 2),
        solo verá las citas asignadas a él.
        
        Query params:
        - page: Página actual (default: 1)
        - per_page: Items por página (default: 10)
        - fecha: Filtrar por fecha de cita (YYYY-MM-DD)
        - fecha_registro: Filtrar por fecha de registro (YYYY-MM-DD)
        - doctor_id: Filtrar por ID del doctor
        - area: Filtrar por nombre de área (búsqueda parcial)
        - area_id: Filtrar por ID de área
        - estado: Filtrar por estado (pendiente, confirmada, atendida, cancelada, referido, no_asistio)
        - paciente_dni: Filtrar por DNI del paciente
        - turno: Filtrar por turno ('M' o 'T')
        """
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            fecha = request.args.get('fecha')  # Fecha de la cita YYYY-MM-DD
            fecha_registro = request.args.get('fecha_registro')  # Fecha de registro YYYY-MM-DD
            doctor_id = request.args.get('doctor_id')
            area = request.args.get('area')
            area_id = request.args.get('area_id')
            estado = request.args.get('estado')
            paciente_dni = request.args.get('paciente_dni')
            turno = request.args.get('turno')
            
            # Si el usuario autenticado es un profesional (rol_id = 2),
            # forzar el filtro de doctor_id para que solo vea sus propias citas
            # y restringir los estados visibles
            is_profesional = False
            if hasattr(request, 'user') and request.user:
                user_rol_id = request.user.get('rol_id')
                user_id = request.user.get('id')
                
                # Rol 2 = Profesional: solo puede ver sus propias citas
                if user_rol_id == 2 and user_id:
                    doctor_id = user_id
                    is_profesional = True

            query = Cita.query

            # Filtro por fecha de la cita
            if fecha:
                try:
                    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
                    query = query.filter(Cita.fecha == fecha_obj)
                except ValueError:
                    pass

            # Filtro por fecha de registro
            if fecha_registro:
                try:
                    fecha_obj = datetime.strptime(fecha_registro, "%Y-%m-%d").date()
                    query = query.filter(db.func.date(Cita.fecha_registro) == fecha_obj)
                except ValueError:
                    pass

            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)
            
            # Filtro por área (por ID o por nombre)
            if area_id:
                query = query.filter_by(area_id=area_id)
            elif area:
                # Buscar por nombre de área (case-insensitive, parcial)
                query = query.join(Area, Cita.area_id == Area.id).filter(
                    Area.nombre.ilike(f"%{area}%")
                )
            # Filtro de estado
            # Para profesionales: solo pueden ver estados específicos
            # (confirmada, atendida, no_asistio, referido) - NO ven pendientes ni canceladas
                estados_permitidos_nombres = ['confirmada', 'atendida', 'no_asistio', 'referido']
                if estado and estado in estados_permitidos_nombres:
                    # Filtrar por un estado específico
                     query = query.join(EstadoCita).filter(EstadoCita.nombre == estado)
                else:
                    # Mostrar todos los permitidos
                     query = query.join(EstadoCita).filter(EstadoCita.nombre.in_(estados_permitidos_nombres))
            elif estado:
                # Filtrar por nombre de estado normalizado
                query = query.join(EstadoCita).filter(EstadoCita.nombre == estado)

            if paciente_dni:
                query = query.join(Paciente).join(Persona, Paciente.persona_id == Persona.id).filter(Persona.dni.ilike(f"%{paciente_dni}%"))

            # Filtro por turno (si tiene horario asociado)
            if turno:
                query = query.join(HorarioMedico, Cita.horario_id == HorarioMedico.id).filter(
                    HorarioMedico.turno == turno
                )

            # Ordenar por fecha de cita descendente, luego por fecha_registro
            query = query.order_by(Cita.fecha.desc().nullslast(), Cita.fecha_registro.desc())

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            data = []
            for cita in pagination.items:
                cita_dict = cita.to_dict()
                
                # Incluir datos del paciente
                if cita.paciente:
                    cita_dict['paciente'] = {
                        "id": cita.paciente.id,
                        "nombres": cita.paciente.nombres,
                        "apellido_paterno": cita.paciente.apellido_paterno,
                        "apellido_materno": cita.paciente.apellido_materno,
                        "dni": cita.paciente.dni,
                        "telefono": cita.paciente.telefono,
                        "email": cita.paciente.email
                    }
                
                # Incluir información del horario si existe
                if cita.horario:
                    cita_dict['horario'] = {
                        "id": cita.horario.id,
                        "turno": cita.horario.turno,
                        "turno_nombre": cita.horario.turno_nombre,
                        "hora_inicio": str(cita.horario.hora_inicio),
                        "hora_fin": str(cita.horario.hora_fin)
                    }
                
                data.append(cita_dict)

            return jsonify({
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": pagination.per_page,
                "data": data
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def crear():
        """
        Crear una nueva cita médica.
        
        Payload esperado:
        {
            "paciente_id": int (requerido),
            "horario_id": int (requerido),
            "fecha": "YYYY-MM-DD" (requerido),
            "sintomas": string (requerido),
            "area_id": int (opcional, se obtiene del horario si no se envía),
            "dni_acompanante": string (opcional),
            "nombre_acompanante": string (opcional),
            "telefono_acompanante": string (opcional)
        }
        """
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ["paciente_id", "horario_id", "fecha", "sintomas"]
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({"error": f"El campo '{field}' es obligatorio"}), 400
            
            # Validar que el paciente exista
            paciente = Paciente.query.get(data["paciente_id"])
            if not paciente:
                return jsonify({"error": "Paciente no encontrado"}), 404
            
            # Obtener el horario para validar y extraer información
            horario = HorarioMedico.query.get(data["horario_id"])
            if not horario:
                return jsonify({"error": "Horario no encontrado"}), 404
            
            # Parsear la fecha
            try:
                fecha_cita = datetime.strptime(data["fecha"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
            
            # Validar que la fecha coincida con el horario
            if horario.fecha != fecha_cita:
                return jsonify({"error": "La fecha no coincide con el horario seleccionado"}), 400
            
            # Contar citas existentes para este horario en esta fecha
            # Contar citas existentes usando relación de estado
            citas_existentes = Cita.query.join(EstadoCita).filter(
                Cita.horario_id == horario.id,
                Cita.fecha == fecha_cita,
                EstadoCita.nombre != 'cancelada'
            ).count()
            
            # Validar cupos disponibles
            if citas_existentes >= horario.cupos:
                return jsonify({
                    "error": "No hay cupos disponibles para este horario",
                    "cupos_totales": horario.cupos,
                    "cupos_ocupados": citas_existentes
                }), 400
            
            # Determinar area_id (del payload o del horario)
            area_id = data.get("area_id") or horario.area_id
            
            # Obtener nombre del área
            area = Area.query.get(area_id)
            area_nombre = area.nombre if area else "Sin área"
            
            # Gestionar Acompañante
            acompanante_persona_id = None
            dni_ac = data.get("dni_acompanante")
            if dni_ac:
                acompanante = Persona.query.filter_by(dni=dni_ac).first()
                if not acompanante:
                    acompanante = Persona(
                        dni=dni_ac,
                        nombres=data.get("nombres_acompanante", "ACOMPAÑANTE"),
                        apellido_paterno=data.get("apellido_paterno_acompanante", "."),
                        apellido_materno=data.get("apellido_materno_acompanante", "."),
                        telefono=data.get("telefono_acompanante")
                    )
                    db.session.add(acompanante)
                    db.session.flush()
                else:
                    # Actualizar datos si existen nuevos valores
                    if data.get("nombres_acompanante"):
                        acompanante.nombres = data.get("nombres_acompanante")
                    if data.get("apellido_paterno_acompanante"):
                        acompanante.apellido_paterno = data.get("apellido_paterno_acompanante")
                    if data.get("apellido_materno_acompanante"):
                        acompanante.apellido_materno = data.get("apellido_materno_acompanante")
                    # Actualizar teléfono si cambió
                    if data.get("telefono_acompanante"):
                        acompanante.telefono = data.get("telefono_acompanante")
                
                acompanante_persona_id = acompanante.id

            # Crear la cita
            nueva_cita = Cita(
                paciente_id=data["paciente_id"],
                horario_id=horario.id,
                doctor_id=horario.medico_id,
                area_id=area_id,
                fecha=fecha_cita,
                sintomas=data["sintomas"],
                acompanante_persona_id=acompanante_persona_id,
                datos_adicionales=data.get("datos_adicionales")
            )
            
            # Buscar estado pendiente
            estado_pendiente = EstadoCita.query.filter_by(nombre="pendiente").first()
            if estado_pendiente:
                nueva_cita.estado_id = estado_pendiente.id
            
            db.session.add(nueva_cita)
            db.session.commit()
            
            # Calcular cupos restantes para la respuesta
            cupos_restantes = horario.cupos - (citas_existentes + 1)
            
            return jsonify({
                "message": "Cita creada exitosamente",
                "data": nueva_cita.to_dict(),
                "cupos_restantes": cupos_restantes
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def obtener(id):
        """
        Obtener detalle completo de una cita por ID.
        Incluye información del paciente, horario y doctor.
        """
        try:
            cita = Cita.query.get(id)
            if not cita:
                return jsonify({"error": "Cita no encontrada"}), 404
            
            cita_dict = cita.to_dict()
            
            # Incluir datos completos del paciente
            if cita.paciente:
                cita_dict['paciente'] = {
                    "id": cita.paciente.id,
                    "nombres": cita.paciente.nombres,
                    "apellido_paterno": cita.paciente.apellido_paterno,
                    "apellido_materno": cita.paciente.apellido_materno,
                    "dni": cita.paciente.dni,
                    "telefono": cita.paciente.telefono,
                    "email": cita.paciente.email,
                    "fecha_nacimiento": str(cita.paciente.fecha_nacimiento) if cita.paciente.fecha_nacimiento else None,
                    "sexo": cita.paciente.sexo,
                    "direccion": cita.paciente.direccion,
                    "seguro": cita.paciente.seguro
                }
            
            # Incluir información del horario si existe
            if cita.horario:
                cita_dict['horario'] = {
                    "id": cita.horario.id,
                    "turno": cita.horario.turno,
                    "turno_nombre": cita.horario.turno_nombre,
                    "hora_inicio": str(cita.horario.hora_inicio),
                    "hora_fin": str(cita.horario.hora_fin),
                    "cupos": cita.horario.cupos
                }
            
            return jsonify(cita_dict), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def actualizar(id):
        try:
            data = request.get_json()
            cita = Cita.query.get(id)
            if not cita:
                return jsonify({"error": "Cita no encontrada"}), 404

            # Guardar estado anterior para el historial
            estado_anterior_id = cita.estado_id
            estado_nuevo_id = None

            if "doctor_id" in data:
                cita.doctor_id = data["doctor_id"]
            if "area_id" in data:
                cita.area_id = data["area_id"]
            if "sintomas" in data:
                cita.sintomas = data["sintomas"]
            if "estado" in data:
                # Actualizar relación de estado
                nuevo_estado_obj = EstadoCita.query.filter_by(nombre=data["estado"]).first()
                if nuevo_estado_obj:
                    estado_nuevo_id = nuevo_estado_obj.id
                    cita.estado_id = estado_nuevo_id
            
            if "dni_acompanante" in data:
                dni_ac = data["dni_acompanante"]
                if dni_ac:
                    ac = Persona.query.filter_by(dni=dni_ac).first()
                    if not ac:
                        ac = Persona(
                            dni=dni_ac,
                            nombres=data.get("nombres_acompanante", "ACOMPAÑANTE"),
                            apellido_paterno=data.get("apellido_paterno_acompanante", "."),
                            apellido_materno=data.get("apellido_materno_acompanante", "."),
                            telefono=data.get("telefono_acompanante")
                        )
                        db.session.add(ac)
                        db.session.flush()
                    else:
                        if "nombres_acompanante" in data:
                            ac.nombres = data["nombres_acompanante"]
                        if "apellido_paterno_acompanante" in data:
                            ac.apellido_paterno = data["apellido_paterno_acompanante"]
                        if "apellido_materno_acompanante" in data:
                            ac.apellido_materno = data["apellido_materno_acompanante"]
                        if "telefono_acompanante" in data:
                            ac.telefono = data["telefono_acompanante"]
                    cita.acompanante_persona_id = ac.id
                else:
                    cita.acompanante_persona_id = None

            if "datos_adicionales" in data:
                if cita.datos_adicionales and isinstance(data["datos_adicionales"], dict):
                    cita.datos_adicionales.update(data["datos_adicionales"])
                else:
                    cita.datos_adicionales = data["datos_adicionales"]
            
            # Registrar cambio de estado en el historial si hubo cambio
            if estado_nuevo_id and estado_nuevo_id != estado_anterior_id:
                # Obtener el usuario actual del token (guardado por el middleware)
                usuario_id = None
                if hasattr(request, 'user') and request.user:
                    usuario_id = request.user.get('id')
                
                # Obtener IP del cliente
                ip_address = request.remote_addr
                
                # Obtener comentario si se envió
                comentario = data.get("comentario_cambio")
                
                HistorialEstadoCita.registrar_cambio(
                    cita_id=cita.id,
                    estado_anterior_id=estado_anterior_id,
                    estado_nuevo_id=estado_nuevo_id,
                    usuario_id=usuario_id,
                    comentario=comentario,
                    ip_address=ip_address
                )

            db.session.commit()
            return jsonify(cita.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def eliminar(id):
        try:
            cita = Cita.query.get(id)
            if not cita:
                return jsonify({"error": "Cita no encontrada"}), 404
            
            db.session.delete(cita)
            db.session.commit()
            return jsonify({"message": "Cita eliminada correctamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def obtener_historial(id):
        """
        Obtiene el historial de cambios de estado de una cita.
        
        Returns:
            Lista de cambios de estado ordenados por fecha descendente
        """
        try:
            cita = Cita.query.get(id)
            if not cita:
                return jsonify({"error": "Cita no encontrada"}), 404
            
            historial = HistorialEstadoCita.query.filter_by(cita_id=id)\
                .order_by(HistorialEstadoCita.fecha_cambio.desc())\
                .all()
            
            return jsonify({
                "cita_id": id,
                "total": len(historial),
                "historial": [h.to_dict() for h in historial]
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def obtener_citas_confirmadas_para_impresion():
        """
        Obtiene las citas confirmadas para una fecha y área específica.
        
        IMPORTANTE: Las citas se ordenan por fecha_registro (orden de llegada/registro)
        para que la numeración refleje el orden en que los pacientes registraron su cita.
        
        Query params:
        - fecha: Fecha de las citas en formato YYYY-MM-DD (requerido)
        - area_id: ID del área/servicio (requerido)
        
        Returns:
            JSON con la lista de citas confirmadas numeradas
        """
        try:
            fecha = request.args.get('fecha')
            area_id = request.args.get('area_id', type=int)
            
            # Validar parámetros requeridos
            if not fecha:
                return jsonify({
                    'success': False,
                    'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'
                }), 400
            
            if not area_id:
                return jsonify({
                    'success': False,
                    'error': 'El parámetro area_id es requerido'
                }), 400
            
            # Validar formato de fecha
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400
            
            # Verificar que el área existe
            area = Area.query.get(area_id)
            if not area:
                return jsonify({
                    'success': False,
                    'error': 'Área no encontrada'
                }), 404
            
            medico_id = request.args.get('medico_id', type=int)
            
            # Consultar citas confirmadas ordenadas por fecha de registro (orden de llegada)
            # Usamos JOIN con HorarioMedico para poder filtrar por médico si es necesario
            query = Cita.query.join(HorarioMedico).join(EstadoCita).filter(
                Cita.fecha == fecha_obj,
                Cita.area_id == area_id,
                EstadoCita.nombre == 'confirmada'
            )
            
            if medico_id:
                query = query.filter(HorarioMedico.medico_id == medico_id)
            
            citas = query.order_by(
                Cita.fecha_registro.asc()  # Ordenar por orden de registro (ascendente)
            ).all()
            
            # Construir respuesta con numeración
            citas_data = []
            for numero, cita in enumerate(citas, start=1):
                cita_info = {
                    'numero': numero,  # Numeración automática por orden de registro
                    'id': cita.id,
                    'paciente': {
                        'id': cita.paciente.id,
                        'nombres': cita.paciente.nombres,
                        'apellido_paterno': cita.paciente.apellido_paterno,
                        'apellido_materno': cita.paciente.apellido_materno,
                        'dni': cita.paciente.dni,
                        'telefono': cita.paciente.telefono
                    } if cita.paciente else None,
                    'horario': {
                        'id': cita.horario.id,
                        'hora_inicio': str(cita.horario.hora_inicio),
                        'hora_fin': str(cita.horario.hora_fin),
                        'turno': cita.horario.turno,
                        'turno_nombre': cita.horario.turno_nombre
                    } if cita.horario else None,
                    'medico': {
                        'id': cita.horario.medico.id,
                        'nombre': cita.horario.medico.nombres_completos
                    } if cita.horario and cita.horario.medico else None,
                    'fecha_registro': cita.fecha_registro.isoformat() if cita.fecha_registro else None
                }
                citas_data.append(cita_info)
            
            response = {
                'success': True,
                'fecha': fecha,
                'area': {
                    'id': area.id,
                    'nombre': area.nombre
                },
                'total': len(citas_data),
                'citas': citas_data
            }
            
            if medico_id:
                medico = Usuario.query.get(medico_id)
                if medico:
                    response['medico'] = {
                        'id': medico.id,
                        'nombre': medico.nombres_completos
                    }

            return jsonify(response), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al obtener citas: {str(e)}'
            }), 500

    @staticmethod
    def generar_pdf_citas_confirmadas():
        """
        Genera un PDF con las citas confirmadas para una fecha y área específica.
        Opcionalmente filtra por médico.
        
        Query params:
        - fecha: Fecha de las citas en formato YYYY-MM-DD (requerido)
        - area_id: ID del área/servicio (requerido)
        - medico_id: ID del médico (opcional)
        
        Returns:
            PDF file como respuesta directa para descarga
        """
        try:
            fecha = request.args.get('fecha')
            area_id = request.args.get('area_id', type=int)
            medico_id = request.args.get('medico_id', type=int)
            
            # Validar parámetros requeridos
            if not fecha:
                return jsonify({
                    'success': False,
                    'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'
                }), 400
            
            if not area_id:
                return jsonify({
                    'success': False,
                    'error': 'El parámetro area_id es requerido'
                }), 400
                
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400

            # Validar existencia del área
            area = Area.query.get(area_id)
            if not area:
                return jsonify({
                    'success': False,
                    'error': 'Área no encontrada'
                }), 404
            
            # Obtener info del médico si se solicita
            medico = None
            if medico_id:
                medico = Usuario.query.get(medico_id)
                # Validar que el médico exista es opcional aquí, pero útil
            
            # Construir consulta
            query = Cita.query.join(HorarioMedico).join(EstadoCita).filter(
                HorarioMedico.area_id == area_id,
                HorarioMedico.fecha == fecha_obj,
                EstadoCita.nombre == 'confirmada'
            )
            
            # Filtrar por médico si se proporciona
            if medico_id:
                query = query.filter(HorarioMedico.medico_id == medico_id)
            
            # Ordenar por fecha de registro (orden de llegada)
            citas = query.order_by(
                Cita.fecha_registro.asc()
            ).all()
            
            # Preparar datos para el servicio PDF
            citas_data = []
            for numero, cita in enumerate(citas, start=1):
                cita_info = {
                    'numero': numero, 
                    'id': cita.id,
                    'paciente': {
                        'nombres': cita.paciente.nombres,
                        'apellido_paterno': cita.paciente.apellido_paterno,
                        'apellido_materno': cita.paciente.apellido_materno,
                        'dni': cita.paciente.dni
                    } if cita.paciente else None,
                    'horario': {
                        'hora_inicio': str(cita.horario.hora_inicio),
                        'hora_fin': str(cita.horario.hora_fin),
                        'turno': cita.horario.turno,
                        'turno_nombre': cita.horario.turno_nombre
                    } if cita.horario else None,
                    # Agregar info del médico por cita si no filtramos por médico único
                    'medico': {
                        'nombre': cita.horario.medico.nombres_completos
                    } if cita.horario.medico else None
                }
                citas_data.append(cita_info)
            
            area_data = {'id': area.id, 'nombre': area.nombre}
            medico_data = {'nombre': medico.nombres_completos} if medico else None
            
            # Generar PDF
            pdf_buffer = PDFService.generar_pdf_citas_confirmadas(
                fecha=fecha,
                area=area_data,
                citas=citas_data,
                medico=medico_data
            )
            
            # Nombre del archivo
            filename = PDFService.generar_nombre_archivo(
                fecha, 
                area.nombre, 
                medico.nombres_completos if medico else None
            )
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{filename}.pdf"
            )
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al generar PDF: {str(e)}'
            }), 500
