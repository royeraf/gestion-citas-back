from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from extensions.database import db
from models.usuario_model import Usuario
from models.persona_model import Persona
from models.horario_medico_model import HorarioMedico
from models.especialidad_model import Especialidad
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from flask import make_response


class UsuarioController:

    @staticmethod
    def crear_usuario(data):
        try:
            required = ["dni", "password", "rol_id"]
            for field in required:
                if field not in data or not data[field]:
                    return jsonify({"error": f"El campo '{field}' es obligatorio"}), 400

            # Verificar usuario existente por DNI a través de Persona
            if Usuario.query.join(Persona).filter(Persona.dni == data["dni"]).first():
                return jsonify({"error": "El DNI ya está registrado como usuario"}), 409

            # 1. Gestionar Persona
            persona = Persona.query.filter_by(dni=data["dni"]).first()
            if not persona:
                nombres = data.get("nombres_completos", "Usuario")
                persona = Persona(
                    dni=data["dni"],
                    nombres=nombres,
                    apellido_paterno="",
                    apellido_materno=""
                )
                db.session.add(persona)
                db.session.flush()

            # 2. Gestionar Usuario
            usuario = Usuario(
                persona_id=persona.id,
                dni=data["dni"],
                password=generate_password_hash(data["password"]),
                rol_id=data["rol_id"],
                nombres_completos=data.get("nombres_completos")
            )

            db.session.add(usuario)
            db.session.commit()

            return jsonify({
                "message": "Usuario creado correctamente",
                "usuario": usuario.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def login(data):
        dni = data.get("dni")
        password = data.get("password")

        if not dni or not password:
            return jsonify({"error": "dni y password son requeridos"}), 400

        # Buscar por DNI uniendo con Persona
        usuario = Usuario.query.join(Persona).filter(Persona.dni == dni).first()

        if not usuario:
            return jsonify({"error": "Credenciales incorrectas"}), 401

        if not check_password_hash(usuario.password, password):
            return jsonify({"error": "Credenciales incorrectas"}), 401

        # Use dictionary as identity to maintain compatibility with frontend/middleware
        identity_data = {
            "id": usuario.id,
            "dni": usuario.dni,
            "rol_id": usuario.rol_id
        }

        access = create_access_token(identity=identity_data)
        refresh = create_refresh_token(identity=identity_data)

        response = make_response({
            "message": "Login exitoso",
            "access_token": access,
            "usuario": usuario.to_dict()
        })

        # Guardar refresh token como cookie HTTP-Only
        response.set_cookie(
            "refresh_token",
            refresh,
            httponly=True,
            secure=False,  # Cambiar a True en producción con HTTPS
            samesite="Lax",
            max_age=60*60*24*7  # 7 días
        )

        return response

    @staticmethod
    def refresh_token(data):
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "refresh_token requerido"}), 400

        decoded = JWTManager.decode_token(refresh_token)

        if "error" in decoded:
            return jsonify(decoded), 401

        if decoded.get("type") != "refresh":
            return jsonify({"error": "Token no es de tipo refresh"}), 401

        user_data = decoded["data"]

        new_access = JWTManager.create_access_token(user_data)

        return jsonify({"access_token": new_access})

    @staticmethod
    def get_medicos():
        """
        Obtiene lista de médicos con su área de servicio y disponibilidad futura.
        OPTIMIZADO: Una sola consulta para todos los médicos, sus áreas y disponibilidad.
        
        Query params:
        - area_id: Filtrar por área específica
        
        Retorna para cada médico:
        - Datos básicos del usuario
        - area_id: ID del área principal
        - area_nombre: Nombre del área principal
        - especialidad: Alias de area_nombre
        - disponibilidad: { turnos: int, cupos: int }
        """
        try:
            from models.area_model import Area
            from models.cita_model import Cita
            from models.estado_cita_model import EstadoCita
            from sqlalchemy import func, desc
            from datetime import date
            
            area_id_filter = request.args.get('area_id')
            
            # 1. Subconsulta para obtener el área más frecuente por médico
            area_counts = db.session.query(
                HorarioMedico.medico_id,
                HorarioMedico.area_id,
                Area.nombre.label('area_nombre'),
                func.count(HorarioMedico.id).label('horarios_count')
            ).join(Area, HorarioMedico.area_id == Area.id)\
             .group_by(HorarioMedico.medico_id, HorarioMedico.area_id, Area.nombre)\
             .subquery()
            
            # 2. Subconsulta para obtener el máximo count por médico
            max_counts = db.session.query(
                area_counts.c.medico_id,
                func.max(area_counts.c.horarios_count).label('max_count')
            ).group_by(area_counts.c.medico_id).subquery()
            
            # 3. Obtener el área principal
            areas_principales = db.session.query(
                area_counts.c.medico_id,
                area_counts.c.area_id,
                area_counts.c.area_nombre
            ).join(
                max_counts,
                (area_counts.c.medico_id == max_counts.c.medico_id) & 
                (area_counts.c.horarios_count == max_counts.c.max_count)
            ).subquery()

            # 4. Subconsultas para DISPONIBILIDAD futura
            today = date.today()

            # A. Capacidad total (Horarios futuros)
            capacity_query = db.session.query(
                HorarioMedico.medico_id,
                func.count(HorarioMedico.id).label('total_turnos'),
                func.sum(HorarioMedico.cupos).label('total_cupos')
            ).filter(
                HorarioMedico.fecha >= today
            )
            
            if area_id_filter:
                capacity_query = capacity_query.filter(HorarioMedico.area_id == area_id_filter)
            
            capacity_subquery = capacity_query.group_by(HorarioMedico.medico_id).subquery()

            # B. Citas ocupadas (Citas en horarios futuros activos)
            occupied_query = db.session.query(
                HorarioMedico.medico_id,
                func.count(Cita.id).label('occupied_count')
            ).join(
                Cita, Cita.horario_id == HorarioMedico.id
            ).join(
                EstadoCita, Cita.estado_id == EstadoCita.id
            ).filter(
                HorarioMedico.fecha >= today,
                EstadoCita.nombre != 'cancelada'
            )

            if area_id_filter:
                occupied_query = occupied_query.filter(HorarioMedico.area_id == area_id_filter)

            occupied_subquery = occupied_query.group_by(HorarioMedico.medico_id).subquery()
            
            # 5. Query principal
            query = db.session.query(
                Usuario,
                areas_principales.c.area_id,
                areas_principales.c.area_nombre,
                func.coalesce(capacity_subquery.c.total_turnos, 0).label('turnos'),
                func.coalesce(capacity_subquery.c.total_cupos, 0).label('total_cupos'),
                func.coalesce(occupied_subquery.c.occupied_count, 0).label('occupied')
            ).outerjoin(
                areas_principales,
                Usuario.id == areas_principales.c.medico_id
            ).outerjoin(
                capacity_subquery,
                Usuario.id == capacity_subquery.c.medico_id
            ).outerjoin(
                occupied_subquery,
                Usuario.id == occupied_subquery.c.medico_id
            ).filter(Usuario.rol_id == 2)

            # Filtros adicionales
            activo_param = request.args.get('activo')
            if activo_param is not None:
                if activo_param.lower() == 'true':
                    query = query.filter(Usuario.activo == True)
                elif activo_param.lower() == 'false':
                    query = query.filter(Usuario.activo == False)
            else:
                query = query.filter(Usuario.activo == True)
            
            if area_id_filter:
                # Filtrar médicos que tienen horarios en esa área
                medicos_con_horario = db.session.query(
                    HorarioMedico.medico_id
                ).filter_by(area_id=area_id_filter).distinct()
                query = query.filter(Usuario.id.in_(medicos_con_horario))
            
            # Ejecutar consulta
            resultados = query.all()
            
            # Construir respuesta
            lista_medicos = []
            for usuario, area_id, area_nombre, turnos, total_cupos, occupied in resultados:
                medico_dict = usuario.to_dict()
                medico_dict['name'] = usuario.nombres_completos
                medico_dict['area_id'] = area_id
                medico_dict['area_nombre'] = area_nombre
                medico_dict['especialidad'] = area_nombre  # Alias para compatibilidad
                
                # Calcular cupos disponibles reales
                cupos_disponibles = int(total_cupos) - int(occupied)
                
                medico_dict['disponibilidad'] = {
                    'turnos': int(turnos),
                    'cupos': max(0, cupos_disponibles),
                    'ocupados': int(occupied)
                }
                lista_medicos.append(medico_dict)
            
            return jsonify(lista_medicos), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # CRUD COMPLETO PARA GESTIÓN DE USUARIOS
    # ==========================================

    @staticmethod
    def listar_usuarios():
        """
        Lista todos los usuarios del sistema con filtros opcionales.
        
        Query params:
        - role: Filtrar por rol (admin, medico, asistente)
        - search: Búsqueda por nombre o username
        
        Retorna lista de usuarios con campos compatibles con frontend:
        - id, name, username, role, createdAt
        """
        try:
            query = Usuario.query

            # Filtro por rol
            role_filter = request.args.get('role')
            if role_filter:
                # Mapear roles del frontend a los del backend (enteros)
                role_mapping = {
                    'admin': 1,
                    'profesional': 2,
                    'asistente': 3
                }
                backend_role = role_mapping.get(role_filter)
                if backend_role:
                    query = query.filter(Usuario.rol_id == backend_role)

            # Filtro por búsqueda (nombre o username)
            search = request.args.get('search')
            if search:
                search_pattern = f"%{search}%"
                query = query.join(Persona).filter(
                    db.or_(
                        Persona.nombres.ilike(search_pattern),
                        Persona.apellido_paterno.ilike(search_pattern),
                        Persona.apellido_materno.ilike(search_pattern),
                        Persona.dni.ilike(search_pattern)
                    )
                )

            usuarios = query.order_by(Usuario.id.desc()).all()

            # Mapear roles del backend (enteros) al frontend
            role_mapping_reverse = {
                1: 'admin',
                2: 'profesional',
                3: 'asistente'
            }

            # Nombres legibles de los roles
            role_names = {
                1: 'Administrador',
                2: 'Profesional',
                3: 'Asistente Técnico'
            }

            lista = []
            for u in usuarios:
                role_key = role_mapping_reverse.get(u.rol_id, u.rol_id)
                lista.append({
                    "id": u.id,
                    "name": u.nombres_completos or u.dni,
                    "username": u.dni,
                    "role": role_key,
                    "role_nombre": role_names.get(u.rol_id, str(u.rol_id)),
                    "dni": u.dni,
                    "activo": u.activo,
                    "createdAt": str(u.created_at) if u.created_at else None
                })

            return jsonify(lista), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def obtener_usuario(usuario_id):
        """
        Obtiene un usuario específico por su ID.
        """
        try:
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Mapear rol_id (entero) a string del frontend
            role_mapping_reverse = {
                1: 'admin',
                2: 'profesional',
                3: 'asistente'
            }

            return jsonify({
                "id": usuario.id,
                "name": usuario.nombres_completos or usuario.dni,
                "username": usuario.dni,
                "role": role_mapping_reverse.get(usuario.rol_id, usuario.rol_id),
                "dni": usuario.dni,
                "activo": usuario.activo,
                "createdAt": None
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def actualizar_usuario(usuario_id, data):
        """
        Actualiza un usuario existente.
        
        Body JSON:
        - name: Nombre completo
        - username: Nombre de usuario
        - password: Nueva contraseña (opcional, solo si se quiere cambiar)
        - role: Rol del usuario (admin, medico, asistente)
        """
        try:
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Mapear roles del frontend al backend (enteros)
            role_mapping = {
                'admin': 1,
                'profesional': 2,
                'asistente': 3
            }

            # Actualizar campos
            if 'name' in data:
                usuario.nombres_completos = data['name']
            
            # Soporte para nombres divididos
            if usuario.persona:
                if 'nombres' in data:
                    usuario.persona.nombres = data['nombres']
                if 'apellido_paterno' in data:
                    usuario.persona.apellido_paterno = data['apellido_paterno']
                if 'apellido_materno' in data:
                    usuario.persona.apellido_materno = data['apellido_materno']
                if 'email' in data:
                    usuario.persona.email = data['email']
                if 'telefono' in data:
                    usuario.persona.telefono = data['telefono']
                if 'direccion' in data:
                    usuario.persona.direccion = data['direccion']

            # Gestionar Especialidades (si es médico/profesional)
            if 'especialidades_ids' in data and usuario.rol_id == 2:
                ids = data['especialidades_ids']
                especialidades = Especialidad.query.filter(Especialidad.id.in_(ids)).all()
                usuario.especialidades = especialidades

            identifier = data.get('username') or data.get('dni')
            if identifier and identifier != usuario.dni:
                # Verificar que el nuevo DNI no esté en uso por otro usuario
                existing = Usuario.query.join(Persona).filter(
                    Persona.dni == identifier,
                    Usuario.id != usuario_id
                ).first()
                if existing:
                    return jsonify({"error": "El DNI ya está en uso por otro usuario"}), 409
                usuario.dni = identifier

            if 'password' in data and data['password']:
                usuario.password = generate_password_hash(data['password'])

            if 'role' in data:
                backend_role = role_mapping.get(data['role'])
                if backend_role:
                    usuario.rol_id = backend_role

            if 'activo' in data:
                usuario.activo = data['activo']

            db.session.commit()

            role_mapping_reverse = {
                1: 'admin',
                2: 'profesional',
                3: 'asistente'
            }

            return jsonify({
                "message": "Usuario actualizado correctamente",
                "usuario": {
                    "id": usuario.id,
                    "name": usuario.nombres_completos or usuario.dni,
                    "username": usuario.dni,
                    "role": role_mapping_reverse.get(usuario.rol_id, usuario.rol_id),
                    "dni": usuario.dni,
                    "activo": usuario.activo
                }
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def eliminar_usuario(usuario_id):
        """
        Elimina un usuario del sistema.
        También se puede implementar como soft delete cambiando activo = False
        """
        try:
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Verificar que no sea el único administrador
            if usuario.rol_id == 1:  # 1 = administrador
                admin_count = Usuario.query.filter_by(rol_id=1).count()
                if admin_count <= 1:
                    return jsonify({
                        "error": "No se puede eliminar el único administrador del sistema"
                    }), 400

            db.session.delete(usuario)
            db.session.commit()

            return jsonify({
                "message": "Usuario eliminado correctamente"
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def crear_usuario_completo(data):
        """
        Crea un nuevo usuario con todos los campos requeridos por el frontend.
        
        Body JSON:
        - name: Nombre completo
        - username: Nombre de usuario
        - password: Contraseña
        - role: Rol (admin, medico, asistente)
        """
        try:
            required = ["name", "username", "password", "role"]
            for field in required:
                if field not in data or not data[field]:
                    return jsonify({"error": f"El campo '{field}' es obligatorio"}), 400

            # Mapear roles del frontend al backend (enteros)
            role_mapping = {
                'admin': 1,
                'profesional': 2,
                'medico': 2,
                'asistente': 3
            }

            # El identificador principal es el DNI
            dni = data.get("dni") or data.get("username")
            if not dni:
                 return jsonify({"error": "El DNI es obligatorio"}), 400

            # Verificar DNI único en tabla personas vinculadas a usuarios
            if Usuario.query.join(Persona).filter(Persona.dni == dni).first():
                return jsonify({"error": "El DNI ya está registrado como usuario"}), 409
            
            # 1. Gestionar Persona
            persona = Persona.query.filter_by(dni=dni).first()
            if not persona:
                p_nombres = data.get("nombres")
                p_ap1 = data.get("apellido_paterno")
                p_ap2 = data.get("apellido_materno")

                # Si no vienen divididos, intentar split del 'name'
                if not p_nombres and "name" in data:
                    parts = data["name"].split(' ')
                    p_nombres = parts[0]
                    p_ap1 = parts[1] if len(parts) > 1 else ""
                    p_ap2 = " ".join(parts[2:]) if len(parts) > 2 else ""

                persona = Persona(
                    dni=dni,
                    nombres=p_nombres or "Usuario",
                    apellido_paterno=p_ap1 or "",
                    apellido_materno=p_ap2 or "",
                    email=data.get("email"),
                    telefono=data.get("telefono"),
                    direccion=data.get("direccion")
                )
                db.session.add(persona)
                db.session.flush()

            # 2. Gestionar Usuario
            usuario = Usuario(
                persona_id=persona.id,
                password=generate_password_hash(data["password"]),
                rol_id=role_mapping.get(data["role"], data["role"]),
                activo=True
            )
            
            # Asignar nombre completo si no se manejó por propiedades individuales
            if not data.get("nombres") and "name" in data:
                usuario.nombres_completos = data["name"]

            # 3. Gestionar Especialidades
            if 'especialidades_ids' in data and usuario.rol_id == 2:
                ids = data['especialidades_ids']
                especialidades = Especialidad.query.filter(Especialidad.id.in_(ids)).all()
                usuario.especialidades = especialidades

            db.session.add(usuario)
            db.session.commit()

            role_mapping_reverse = {
                1: 'admin',
                2: 'profesional',
                3: 'asistente'
            }

            return jsonify({
                "message": "Usuario creado correctamente",
                "usuario": {
                    "id": usuario.id,
                    "name": usuario.nombres_completos,
                    "username": usuario.dni,
                    "role": role_mapping_reverse.get(usuario.rol_id, usuario.rol_id),
                    "dni": usuario.dni,
                    "activo": usuario.activo,
                    "createdAt": None
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
