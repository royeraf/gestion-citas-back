"""
seed_posttest_data.py
=====================
Genera datos Post-Test de la tesis (Tablas 41, 43 y 45).
Período: 9 Dic 2025 → 7 Feb 2026 (50 días hábiles)

Uso:
    cd back-citas
    python seed_posttest_data.py

Requiere que la BD ya tenga: doctores, pacientes, estados_cita, áreas.
"""

import sys
import os
import random
from datetime import datetime, date, timedelta

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from factory import create_app
from extensions.database import db
from models.horario_medico_model import HorarioMedico
from models.cita_model import Cita
from models.historial_estado_cita_model import HistorialEstadoCita
from models.paciente_model import Paciente

# ============================================================
# DATOS DE LAS TABLAS DE LA TESIS
# ============================================================

# Tabla 41 – Días de Anticipación (50 citas individuales)
# (fecha_solicitud, fecha_cita, dias_anticipacion)
TABLA_41 = [
    ("2025-12-09", "2025-12-15", 6),
    ("2025-12-09", "2025-12-12", 3),
    ("2025-12-10", "2025-12-12", 2),
    ("2025-12-11", "2025-12-13", 2),
    ("2025-12-11", "2025-12-15", 4),
    ("2025-12-11", "2025-12-14", 3),
    ("2025-12-13", "2025-12-16", 3),
    ("2025-12-13", "2025-12-18", 5),
    ("2025-12-15", "2025-12-18", 3),
    ("2025-12-16", "2025-12-19", 3),
    ("2025-12-17", "2025-12-19", 2),
    ("2025-12-17", "2025-12-19", 2),
    ("2025-12-18", "2025-12-21", 3),
    ("2025-12-20", "2025-12-24", 4),
    ("2025-12-20", "2025-12-25", 5),
    ("2025-12-22", "2025-12-24", 2),
    ("2025-12-23", "2025-12-27", 4),
    ("2025-12-23", "2025-12-26", 3),
    ("2025-12-23", "2025-12-27", 4),
    ("2025-12-26", "2025-12-27", 1),
    ("2025-12-27", "2025-12-30", 3),
    ("2025-12-27", "2025-12-31", 4),
    ("2025-12-29", "2025-12-30", 1),
    ("2025-12-30", "2026-01-01", 2),
    ("2025-12-31", "2026-01-04", 4),
    ("2026-01-02", "2026-01-05", 3),
    ("2026-01-03", "2026-01-06", 3),
    ("2026-01-03", "2026-01-08", 5),
    ("2026-01-03", "2026-01-05", 2),
    ("2026-01-05", "2026-01-09", 4),
    ("2026-01-05", "2026-01-07", 2),
    ("2026-01-05", "2026-01-08", 3),
    ("2026-01-06", "2026-01-12", 6),
    ("2026-01-09", "2026-01-13", 4),
    ("2026-01-09", "2026-01-15", 6),
    ("2026-01-10", "2026-01-13", 3),
    ("2026-01-12", "2026-01-14", 2),
    ("2026-01-13", "2026-01-15", 2),
    ("2026-01-13", "2026-01-18", 5),
    ("2026-01-13", "2026-01-16", 3),
    ("2026-01-15", "2026-01-19", 4),
    ("2026-01-15", "2026-01-17", 2),
    ("2026-01-15", "2026-01-20", 5),
    ("2026-01-16", "2026-01-18", 2),
    ("2026-01-16", "2026-01-20", 4),
    ("2026-01-16", "2026-01-19", 3),
    ("2026-01-17", "2026-01-22", 5),
    ("2026-01-19", "2026-01-20", 1),
    ("2026-01-20", "2026-01-23", 3),
    ("2026-01-22", "2026-01-24", 2),
]

# Tabla 43 – Ocupación: (fecha, citas_programadas)
# Total cupos = 25 por día
TABLA_43 = [
    ("2025-12-09", 20), ("2025-12-10", 19), ("2025-12-11", 16), ("2025-12-12", 15),
    ("2025-12-13", 17), ("2025-12-15", 18), ("2025-12-16", 14), ("2025-12-17", 13),
    ("2025-12-18", 16), ("2025-12-19", 15), ("2025-12-20", 18), ("2025-12-22", 15),
    ("2025-12-23", 19), ("2025-12-24", 17), ("2025-12-26", 16), ("2025-12-27", 20),
    ("2025-12-29", 20), ("2025-12-30", 16), ("2025-12-31", 18), ("2026-01-02", 18),
    ("2026-01-03", 18), ("2026-01-05", 17), ("2026-01-06", 18), ("2026-01-07", 18),
    ("2026-01-08", 18), ("2026-01-09", 21), ("2026-01-10", 16), ("2026-01-12", 18),
    ("2026-01-14", 17), ("2026-01-15", 18), ("2026-01-16", 15), ("2026-01-17", 20),
    ("2026-01-19", 15), ("2026-01-20", 20), ("2026-01-21", 20), ("2026-01-22", 20),
    ("2026-01-23", 16), ("2026-01-24", 15), ("2026-01-26", 15), ("2026-01-27", 16),
    ("2026-01-28", 18), ("2026-01-29", 17), ("2026-01-30", 19), ("2026-01-31", 19),
    ("2026-02-02", 17), ("2026-02-03", 18), ("2026-02-04", 15), ("2026-02-05", 18),
    ("2026-02-06", 15), ("2026-02-07", 18),
]

# Tabla 45 – No-Shows: (fecha, citas_no_asistio)
TABLA_45 = [
    ("2025-12-09", 3), ("2025-12-10", 2), ("2025-12-11", 2), ("2025-12-12", 2),
    ("2025-12-13", 3), ("2025-12-15", 2), ("2025-12-16", 2), ("2025-12-17", 4),
    ("2025-12-18", 4), ("2025-12-19", 4), ("2025-12-20", 2), ("2025-12-22", 3),
    ("2025-12-23", 4), ("2025-12-24", 3), ("2025-12-26", 3), ("2025-12-27", 3),
    ("2025-12-29", 3), ("2025-12-30", 2), ("2025-12-31", 3), ("2026-01-02", 1),
    ("2026-01-03", 4), ("2026-01-05", 3), ("2026-01-06", 3), ("2026-01-07", 3),
    ("2026-01-08", 2), ("2026-01-09", 2), ("2026-01-10", 2), ("2026-01-12", 4),
    ("2026-01-14", 3), ("2026-01-15", 3), ("2026-01-16", 1), ("2026-01-17", 1),
    ("2026-01-19", 2), ("2026-01-20", 4), ("2026-01-21", 4), ("2026-01-22", 2),
    ("2026-01-23", 6), ("2026-01-24", 3), ("2026-01-26", 2), ("2026-01-27", 2),
    ("2026-01-28", 3), ("2026-01-29", 2), ("2026-01-30", 3), ("2026-01-31", 3),
    ("2026-02-02", 4), ("2026-02-03", 2), ("2026-02-04", 2), ("2026-02-05", 2),
    ("2026-02-06", 2), ("2026-02-07", 4),
]

# ============================================================
# CONSTANTES
# ============================================================

# IDs de doctores activos
DOCTOR_IDS = [31, 32, 33, 34, 35, 36, 37, 38]
# Brandon=31, Rudy=32, Yessenia=33, Mahali=34, Rene=35, Edward=36, Federico=37, Karla=38

BRANDON_ID = 31
AREA_ID = 1  # Medicina general
CUPOS_POR_DIA = 25
CUPOS_POR_DOCTOR = 5

# Estados de cita
ESTADO_PENDIENTE = 1
ESTADO_CONFIRMADA = 2
ESTADO_ATENDIDA = 3
ESTADO_NO_ASISTIO = 5

# Síntomas genéricos variados
SINTOMAS = [
    "Dolor de cabeza recurrente",
    "Control rutinario",
    "Dolor abdominal",
    "Fiebre y malestar general",
    "Dolor de garganta",
    "Tos persistente",
    "Dolor lumbar",
    "Mareos frecuentes",
    "Control de presión arterial",
    "Dolor articular",
    "Problemas digestivos",
    "Fatiga y cansancio",
    "Dolor de oído",
    "Infección urinaria",
    "Alergia cutánea",
    "Control de peso",
    "Dolor muscular",
    "Náuseas y vómitos",
    "Dificultad para respirar",
    "Dolor de pecho leve",
    "Revisión general",
    "Dolor en las rodillas",
    "Insomnio",
    "Estrés y ansiedad",
    "Resfriado común",
    "Control de diabetes",
    "Dolor de espalda",
    "Dolor estomacal",
    "Cefalea tensional",
    "Control post-tratamiento",
]

random.seed(42)  # Reproducibilidad


def parse_date(s):
    return date.fromisoformat(s)


def get_dia_semana(d):
    """0=Lunes, 6=Domingo (igual que el modelo)"""
    return d.weekday()


def run_seed():
    force = '--force' in sys.argv
    app = create_app('development')

    with app.app_context():
        # Verificar estado actual
        citas_count = Cita.query.count()
        historial_count = HistorialEstadoCita.query.count()

        if citas_count > 0 or historial_count > 0:
            print(f"⚠️  Ya existen {citas_count} citas y {historial_count} registros de historial.")
            if not force:
                resp = input("¿Desea eliminar los datos existentes y regenerar? (s/n): ").strip().lower()
                if resp != 's':
                    print("Operación cancelada.")
                    return
            print("Eliminando datos existentes...")
            HistorialEstadoCita.query.delete()
            Cita.query.delete()
            # Eliminar TODOS los horarios con cupos=5 (todos son generados por seed)
            # Los originales de Brandon tienen cupos=7, así que se preservan
            seed_horarios = HorarioMedico.query.filter(
                HorarioMedico.cupos == CUPOS_POR_DOCTOR,  # 5 = seed-created
            ).all()
            print(f"   Eliminando {len(seed_horarios)} horarios generados por seed previo...")
            for h in seed_horarios:
                db.session.delete(h)
            db.session.commit()

            # Verificar que solo quedan los originales de Brandon
            restantes = HorarioMedico.query.count()
            print(f"   Horarios restantes (originales): {restantes}")
            print("Datos eliminados.")

        # Obtener pacientes existentes
        pacientes = Paciente.query.all()
        paciente_ids = [p.id for p in pacientes]
        if len(paciente_ids) < 50:
            print(f"❌ Se necesitan al menos 50 pacientes. Hay {len(paciente_ids)}.")
            return
        print(f"✅ {len(paciente_ids)} pacientes disponibles")

        # Construir lookup de no-shows por fecha
        noshows_por_fecha = {parse_date(f): n for f, n in TABLA_45}

        # Construir lookup de citas de Tabla 41 por fecha_cita
        tabla41_por_fecha_cita = {}
        for sol, cita_f, dias in TABLA_41:
            fecha_cita = parse_date(cita_f)
            if fecha_cita not in tabla41_por_fecha_cita:
                tabla41_por_fecha_cita[fecha_cita] = []
            tabla41_por_fecha_cita[fecha_cita].append((parse_date(sol), dias))

        # ============================================================
        # PASO 1: Crear horarios médicos (50 días × 25 cupos)
        # ============================================================
        print("\n📅 Creando horarios médicos...")

        # Obtener horarios ORIGINALES de Brandon (cupos=7, Feb-Mar 2026)
        brandon_horarios = HorarioMedico.query.filter(
            HorarioMedico.medico_id == BRANDON_ID,
            HorarioMedico.cupos == 7,
        ).all()
        brandon_fechas = {h.fecha for h in brandon_horarios}
        print(f"   Brandon tiene {len(brandon_horarios)} horarios originales (cupos=7)")

        horarios_creados = 0
        # Mapa: fecha -> lista de horario_ids para asignar citas
        horarios_por_fecha = {}

        # ---- Rotación por bloques de 2 semanas hábiles (10 días c/u) ----
        # 50 días → 5 bloques de 10 días, cada bloque con 5 doctores
        todas_fechas = [parse_date(f) for f, _ in TABLA_43]

        # 5 bloques de 10 días hábiles
        bloques = [todas_fechas[i:i+10] for i in range(0, 50, 10)]
        # Bloque 0: Dic  9-19  | Bloque 1: Dic 20 - Ene 2
        # Bloque 2: Ene  3-15  | Bloque 3: Ene 16-27
        # Bloque 4: Ene 28 - Feb 7

        # Asignar 5 doctores por bloque, rotando entre los 8
        # Brandon(31) Rudy(32) Yessenia(33) Mahali(34) Rene(35) Edward(36) Federico(37) Karla(38)
        doctores_por_bloque = [
            [31, 32, 33, 34, 35],  # Bloque 0: Brandon, Rudy, Yessenia, Mahali, Rene
            [36, 37, 38, 31, 32],  # Bloque 1: Edward, Federico, Karla, Brandon, Rudy
            [33, 34, 35, 36, 37],  # Bloque 2: Yessenia, Mahali, Rene, Edward, Federico
            [38, 31, 32, 33, 34],  # Bloque 3: Karla, Brandon, Rudy, Yessenia, Mahali
            [35, 36, 37, 38, 31],  # Bloque 4: Rene, Edward, Federico, Karla, Brandon
        ]

        print("   Rotación por bloques de 2 semanas:")
        for b_idx, (bloque_fechas, docs) in enumerate(zip(bloques, doctores_por_bloque)):
            doc_nombres = {31:'Brandon',32:'Rudy',33:'Yessenia',34:'Mahali',
                          35:'Rene',36:'Edward',37:'Federico',38:'Karla'}
            nombres = [doc_nombres[d] for d in docs]
            print(f"   Bloque {b_idx+1} ({bloque_fechas[0]} → {bloque_fechas[-1]}): {', '.join(nombres)}")

        # Crear mapa fecha → doctores del bloque
        fecha_a_doctores = {}
        for bloque_fechas, docs in zip(bloques, doctores_por_bloque):
            for f in bloque_fechas:
                fecha_a_doctores[f] = docs

        # Turnos alternados: 3 mañana + 2 tarde, o 2 mañana + 3 tarde (alternar por día)
        TURNOS_PATRON = [
            ['M', 'M', 'M', 'T', 'T'],  # 3 mañana, 2 tarde
            ['M', 'M', 'T', 'T', 'T'],  # 2 mañana, 3 tarde
        ]

        for dia_idx, (fecha_str, _) in enumerate(TABLA_43):
            fecha = parse_date(fecha_str)
            dia_semana = get_dia_semana(fecha)
            horarios_del_dia = []
            doctores_dia = fecha_a_doctores[fecha]
            turnos_dia = TURNOS_PATRON[dia_idx % 2]  # Alternar patrón

            for i, doc_id in enumerate(doctores_dia):
                turno = turnos_dia[i]

                # Si Brandon ya tiene horario original (cupos=7) para esta fecha
                if doc_id == BRANDON_ID and fecha in brandon_fechas:
                    # Buscar cualquier turno original de Brandon para esta fecha
                    brandon_h = HorarioMedico.query.filter(
                        HorarioMedico.medico_id == BRANDON_ID,
                        HorarioMedico.fecha == fecha,
                        HorarioMedico.cupos == 7,
                    ).first()
                    if brandon_h:
                        horarios_del_dia.append(brandon_h.id)
                        continue

                # Verificar si ya existe el horario para este doctor+fecha+turno
                existe = HorarioMedico.query.filter_by(
                    medico_id=doc_id, fecha=fecha, turno=turno
                ).first()

                if existe:
                    horarios_del_dia.append(existe.id)
                else:
                    h = HorarioMedico(
                        medico_id=doc_id,
                        area_id=AREA_ID,
                        fecha=fecha,
                        dia_semana=dia_semana,
                        turno=turno,
                        cupos=CUPOS_POR_DOCTOR,
                    )
                    db.session.add(h)
                    db.session.flush()
                    horarios_del_dia.append(h.id)
                    horarios_creados += 1

            horarios_por_fecha[fecha] = horarios_del_dia

        db.session.commit()

        # Resumen de turnos
        from sqlalchemy import func as sqlfunc
        turnos_count = db.session.query(
            HorarioMedico.turno, sqlfunc.count(HorarioMedico.id)
        ).filter(HorarioMedico.cupos == CUPOS_POR_DOCTOR).group_by(HorarioMedico.turno).all()
        for turno, cnt in turnos_count:
            nombre = "Mañana" if turno == 'M' else "Tarde"
            print(f"   {nombre} ({turno}): {cnt} horarios")
        print(f"   ✅ {horarios_creados} horarios nuevos creados")

        # ============================================================
        # PASO 2: Crear citas
        # ============================================================
        print("\n🏥 Creando citas...")

        total_citas = 0
        total_noshows = 0
        total_atendidas = 0
        citas_tabla41_usadas = 0

        # Pool de pacientes para usar
        paciente_pool = list(paciente_ids)

        for idx, (fecha_str, n_programadas) in enumerate(TABLA_43):
            fecha = parse_date(fecha_str)
            n_noshows = noshows_por_fecha.get(fecha, 0)
            n_atendidas = n_programadas - n_noshows

            horarios_dia = horarios_por_fecha.get(fecha, [])
            if not horarios_dia:
                print(f"   ⚠️ Sin horarios para {fecha}, saltando...")
                continue

            # Obtener citas de Tabla 41 para esta fecha
            citas_t41 = tabla41_por_fecha_cita.get(fecha, [])

            # Mezclar pacientes para el día
            random.shuffle(paciente_pool)
            pac_idx = 0

            for i in range(n_programadas):
                # Determinar si es no_asistio o atendida
                if i < n_noshows:
                    estado_final_id = ESTADO_NO_ASISTIO
                    total_noshows += 1
                else:
                    estado_final_id = ESTADO_ATENDIDA
                    total_atendidas += 1

                # Asignar horario (round-robin entre los del día)
                horario_id = horarios_dia[i % len(horarios_dia)]
                horario = db.session.get(HorarioMedico, horario_id)
                doctor_id = horario.medico_id

                # Determinar fecha_registro (solicitud)
                if citas_t41 and citas_tabla41_usadas < 50:
                    # Usar datos exactos de Tabla 41
                    fecha_sol, dias_antic = citas_t41.pop(0)
                    fecha_registro = datetime(fecha_sol.year, fecha_sol.month, fecha_sol.day,
                                            random.randint(7, 16), random.randint(0, 59))
                    citas_tabla41_usadas += 1
                else:
                    # Generar fecha_registro aleatoria (1-6 días antes)
                    dias_antes = random.randint(1, 6)
                    fecha_sol = fecha - timedelta(days=dias_antes)
                    fecha_registro = datetime(fecha_sol.year, fecha_sol.month, fecha_sol.day,
                                            random.randint(7, 16), random.randint(0, 59))

                # Paciente
                paciente_id = paciente_pool[pac_idx % len(paciente_pool)]
                pac_idx += 1

                # Síntomas
                sintoma = random.choice(SINTOMAS)

                # Crear la cita
                cita = Cita(
                    paciente_id=paciente_id,
                    horario_id=horario_id,
                    doctor_id=doctor_id,
                    area_id=AREA_ID,
                    fecha=fecha,
                    sintomas=sintoma,
                    fecha_registro=fecha_registro,
                    estado_id=estado_final_id,
                )
                db.session.add(cita)
                db.session.flush()

                # ============================================================
                # PASO 3: Crear historial de estados
                # ============================================================

                # 1. Pendiente → al registrar
                h1 = HistorialEstadoCita(
                    cita_id=cita.id,
                    estado_anterior_id=None,
                    estado_nuevo_id=ESTADO_PENDIENTE,
                    usuario_id=None,
                    fecha_cambio=fecha_registro,
                    comentario="Cita registrada por el sistema",
                )
                db.session.add(h1)

                # 2. Pendiente → Confirmada (~1 día después)
                fecha_confirmacion = fecha_registro + timedelta(
                    hours=random.randint(2, 24),
                    minutes=random.randint(0, 59)
                )
                h2 = HistorialEstadoCita(
                    cita_id=cita.id,
                    estado_anterior_id=ESTADO_PENDIENTE,
                    estado_nuevo_id=ESTADO_CONFIRMADA,
                    usuario_id=None,
                    fecha_cambio=fecha_confirmacion,
                    comentario="Cita confirmada",
                )
                db.session.add(h2)

                # 3. Confirmada → Estado final (el día de la cita)
                hora_final = random.randint(8, 17)
                fecha_estado_final = datetime(fecha.year, fecha.month, fecha.day,
                                             hora_final, random.randint(0, 59))
                comentario_final = (
                    "Paciente atendido" if estado_final_id == ESTADO_ATENDIDA
                    else "Paciente no se presentó a la cita"
                )
                h3 = HistorialEstadoCita(
                    cita_id=cita.id,
                    estado_anterior_id=ESTADO_CONFIRMADA,
                    estado_nuevo_id=estado_final_id,
                    usuario_id=None,
                    fecha_cambio=fecha_estado_final,
                    comentario=comentario_final,
                )
                db.session.add(h3)

                total_citas += 1

            # Commit cada 10 días para no acumular demasiado en memoria
            if (idx + 1) % 10 == 0:
                db.session.commit()
                print(f"   ... {idx + 1}/50 días procesados ({total_citas} citas)")

        db.session.commit()

        # ============================================================
        # PASO 4: Crear citas huérfanas de Tabla 41
        # (fecha_cita no está en Tabla 43 → fechas no hábiles)
        # ============================================================
        tabla43_fechas = {parse_date(f) for f, _ in TABLA_43}
        citas_huerfanas = [
            (sol, cita_f, dias) for sol, cita_f, dias in TABLA_41
            if parse_date(cita_f) not in tabla43_fechas
        ]

        if citas_huerfanas:
            print(f"\n📌 Creando {len(citas_huerfanas)} citas de Tabla 41 en fechas no hábiles...")
            for sol_str, cita_str, dias in citas_huerfanas:
                fecha_sol = parse_date(sol_str)
                fecha_cita = parse_date(cita_str)
                dia_semana = get_dia_semana(fecha_cita)

                # Crear o reusar horario para esta fecha
                doc_id = random.choice(DOCTOR_IDS)
                horario_extra = HorarioMedico.query.filter_by(
                    medico_id=doc_id, fecha=fecha_cita, turno='M'
                ).first()
                if not horario_extra:
                    horario_extra = HorarioMedico(
                        medico_id=doc_id, area_id=AREA_ID, fecha=fecha_cita,
                        dia_semana=dia_semana, turno='M', cupos=CUPOS_POR_DOCTOR,
                    )
                    db.session.add(horario_extra)
                    db.session.flush()

                fecha_registro = datetime(fecha_sol.year, fecha_sol.month, fecha_sol.day,
                                         random.randint(7, 16), random.randint(0, 59))
                paciente_id = random.choice(paciente_ids)

                cita = Cita(
                    paciente_id=paciente_id, horario_id=horario_extra.id,
                    doctor_id=doc_id, area_id=AREA_ID, fecha=fecha_cita,
                    sintomas=random.choice(SINTOMAS), fecha_registro=fecha_registro,
                    estado_id=ESTADO_ATENDIDA,
                )
                db.session.add(cita)
                db.session.flush()

                # Historial: pendiente → confirmada → atendida
                h1 = HistorialEstadoCita(
                    cita_id=cita.id, estado_anterior_id=None,
                    estado_nuevo_id=ESTADO_PENDIENTE, usuario_id=None,
                    fecha_cambio=fecha_registro, comentario="Cita registrada por el sistema",
                )
                db.session.add(h1)
                h2 = HistorialEstadoCita(
                    cita_id=cita.id, estado_anterior_id=ESTADO_PENDIENTE,
                    estado_nuevo_id=ESTADO_CONFIRMADA, usuario_id=None,
                    fecha_cambio=fecha_registro + timedelta(hours=random.randint(2, 24)),
                    comentario="Cita confirmada",
                )
                db.session.add(h2)
                h3 = HistorialEstadoCita(
                    cita_id=cita.id, estado_anterior_id=ESTADO_CONFIRMADA,
                    estado_nuevo_id=ESTADO_ATENDIDA, usuario_id=None,
                    fecha_cambio=datetime(fecha_cita.year, fecha_cita.month, fecha_cita.day,
                                         random.randint(8, 17), random.randint(0, 59)),
                    comentario="Paciente atendido",
                )
                db.session.add(h3)
                citas_tabla41_usadas += 1
                total_citas += 1

            db.session.commit()
            print(f"   ✅ {len(citas_huerfanas)} citas adicionales creadas")
            print(f"   Citas Tabla 41 usadas ahora: {citas_tabla41_usadas}/50")

        # ============================================================
        # VERIFICACIÓN
        # ============================================================
        print("\n" + "=" * 60)
        print("📊 VERIFICACIÓN DE DATOS GENERADOS")
        print("=" * 60)

        # Total citas
        total_bd = Cita.query.count()
        total_historial = HistorialEstadoCita.query.count()
        print(f"\nTotal citas: {total_bd} (esperado: {sum(n for _, n in TABLA_43)})")
        print(f"Total historial: {total_historial} (esperado: {total_bd * 3})")
        print(f"Citas atendidas: {total_atendidas}")
        print(f"Citas no_asistio: {total_noshows} (esperado: {sum(n for _, n in TABLA_45)})")
        print(f"Citas Tabla 41 usadas: {citas_tabla41_usadas}/50")

        # Verificar horarios de Brandon
        brandon_total = HorarioMedico.query.filter_by(medico_id=BRANDON_ID).count()
        print(f"\nHorarios Brandon: {brandon_total} (originales + nuevos)")

        # Verificar ocupación promedio
        print("\n--- Verificación por día ---")
        ocupaciones = []
        noshows_pcts = []
        for fecha_str, esperado in TABLA_43:
            fecha = parse_date(fecha_str)
            n_citas = Cita.query.filter_by(fecha=fecha).count()
            n_noshows_bd = Cita.query.filter_by(fecha=fecha, estado_id=ESTADO_NO_ASISTIO).count()
            ocupacion = (n_citas / CUPOS_POR_DIA) * 100
            noshows_pct = (n_noshows_bd / CUPOS_POR_DIA) * 100
            ocupaciones.append(ocupacion)
            noshows_pcts.append(noshows_pct)

            esperado_noshows = noshows_por_fecha.get(fecha, 0)
            ok_citas = "✅" if n_citas == esperado else "❌"
            ok_noshows = "✅" if n_noshows_bd == esperado_noshows else "❌"
            if n_citas != esperado or n_noshows_bd != esperado_noshows:
                print(f"  {fecha}: citas={n_citas}/{esperado} {ok_citas}, "
                      f"no-shows={n_noshows_bd}/{esperado_noshows} {ok_noshows}")

        avg_ocup = sum(ocupaciones) / len(ocupaciones)
        avg_noshows = sum(noshows_pcts) / len(noshows_pcts)

        print(f"\n📈 Ocupación promedio: {avg_ocup:.2f}% (esperado: 69.20%)")
        print(f"📉 No-shows promedio: {avg_noshows:.2f}% (esperado: 11.04%)")

        # Verificar anticipación (Tabla 41)
        print(f"\n📅 Anticipación (muestra de Tabla 41): {citas_tabla41_usadas} citas con fechas exactas")

        print("\n✅ Seed Post-Test completado exitosamente!")


if __name__ == "__main__":
    run_seed()
