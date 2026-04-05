"""
seed_posttest_data.py
=====================
Genera datos Post-Test de la tesis (observaciones diarias):
  - Población: N=53 días hábiles (Lun-Sáb) en el período
  - Muestra:   n=50 días hábiles (3 excluidos: 25/Dic, 01/Ene, 13/Ene)
  - Horarios médicos: 50 DH × 25 cupos/día = 1250 cupos totales
  - 865 citas no canceladas → Ocupación: 69.20%
  - 138 citas no_asistio → No-Shows: 11.04%
  - Lead time promedio diario: 3.24 días

Período: 9 Dic 2025 → 7 Feb 2026

Uso:
    cd back-citas
    source venv/bin/activate
    python seed_posttest_data.py --force
"""

import sys
import os
import random
from datetime import datetime, date, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from factory import create_app
from extensions.database import db
from models.horario_medico_model import HorarioMedico
from models.cita_model import Cita
from models.historial_estado_cita_model import HistorialEstadoCita
from models.paciente_model import Paciente
from models.persona_model import Persona
from models.usuario_model import Usuario

# ============================================================
# DATOS DE TESIS - OBSERVACIONES DIARIAS (n=50, N=53)
# ============================================================

# 50 días hábiles de la muestra (Lun-Sáb, excluyendo feriados)
DIAS_HABILES = [
    "2025-12-09","2025-12-10","2025-12-11","2025-12-12","2025-12-13",
    "2025-12-15","2025-12-16","2025-12-17","2025-12-18","2025-12-19",
    "2025-12-20","2025-12-22","2025-12-23","2025-12-24","2025-12-26",
    "2025-12-27","2025-12-29","2025-12-30","2025-12-31",
    "2026-01-02","2026-01-03","2026-01-05","2026-01-06","2026-01-07",
    "2026-01-08","2026-01-09","2026-01-10","2026-01-12","2026-01-14",
    "2026-01-15","2026-01-16","2026-01-17","2026-01-19","2026-01-20",
    "2026-01-21","2026-01-22","2026-01-23","2026-01-24","2026-01-26",
    "2026-01-27","2026-01-28","2026-01-29","2026-01-30","2026-01-31",
    "2026-02-02","2026-02-03","2026-02-04","2026-02-05","2026-02-06",
    "2026-02-07",
]

# 3 días excluidos de la muestra (N=53 - n=50 = 3)
DIAS_EXCLUIDOS = ["2025-12-25", "2026-01-01", "2026-01-13"]

# Tabla 41 PostTest - Días promedio de anticipación por día hábil (sum=162, avg=3.24)
LEAD_TIME_POR_DIA = [
    3.21, 3.20, 3.23, 3.55, 3.22,  # 12-09 a 12-13
    2.67, 3.40, 3.16, 3.18, 3.32,  # 12-15 a 12-19
    3.36, 3.74, 3.53, 3.31, 2.97,  # 12-20 a 12-26
    2.86, 3.37, 3.78, 3.28, 3.22,  # 12-27 a 01-02
    3.47, 2.68, 3.14, 3.46, 3.61,  # 01-03 a 01-08
    3.16, 3.41, 3.36, 3.57, 2.81,  # 01-09 a 01-15
    3.49, 2.65, 2.21, 3.02, 2.89,  # 01-16 a 01-21
    3.61, 3.53, 2.77, 3.60, 2.86,  # 01-22 a 01-27
    3.23, 3.14, 3.31, 3.59, 3.52,  # 01-28 a 02-02
    3.40, 3.52, 3.45, 3.01, 2.97,  # 02-03 a 02-07
]

# Tabla 43 PostTest - Citas programadas por día hábil (sum=865, avg=69.20% de 25 cupos)
CITAS_POR_DIA = [
    20, 19, 16, 15, 17, 18, 14, 13, 16, 15,
    18, 15, 19, 17, 16, 20, 20, 16, 18, 18,
    18, 17, 18, 18, 18, 21, 16, 18, 17, 18,
    15, 20, 15, 20, 20, 20, 16, 15, 15, 16,
    18, 17, 19, 19, 17, 18, 15, 18, 15, 18,
]

# Tabla 45 PostTest - No-asistió por día hábil (sum=138, avg=11.04% de 25 cupos)
NOASISTIO_POR_DIA = [
    3, 2, 2, 2, 3, 2, 2, 4, 4, 4,
    2, 3, 4, 3, 3, 3, 3, 2, 3, 1,
    4, 3, 3, 3, 2, 2, 2, 4, 3, 3,
    1, 1, 2, 4, 4, 2, 6, 3, 2, 2,
    3, 2, 3, 3, 4, 2, 2, 2, 2, 4,
]

# ============================================================
# CONSTANTES
# ============================================================

DOCTOR_IDS = [31, 32, 33, 34, 35, 36, 37, 38]
BRANDON_ID = 31
AREA_ID = 1
BRANDON_ORIG_IDS = set(range(570, 620))

ESTADO_PENDIENTE = 1
ESTADO_CONFIRMADA = 2
ESTADO_ATENDIDA = 3
ESTADO_NO_ASISTIO = 5

PACIENTES_EXCLUIDOS = {15, 16, 18, 19, 20, 729}

SINTOMAS = [
    # --- Cortos (asistente apurado, algunos con errores tipicos) ---
    "Dolor de cabeza",
    "Control",
    "Dolor abdominal",
    "Fiebre",
    "Tos",
    "Dolor lumvar",
    "Mareos",
    "Dolor de garganta",
    "Dolor articuler",
    "Resfriado",
    "Dolor de espalda",
    "Nauseas",
    "Dolor de oido",
    "Alergia",
    "Dolor muscular",
    "Fatiga",
    "Dolor estomacal",
    "Insomnio",
    "Control de peso",
    "Dolor de pecho",
    # --- Medianos (descripcion breve, algunos con faltas) ---
    "Dolor de cabesa recurrente desde hace 3 dias",
    "Control rutinario mensual",
    "Dolor abdominal lado derecho",
    "Fiebre y malestar jeneral desde ayer",
    "Tos persistente con flema",
    "Mareos frecuentes al levantarce",
    "Control de precion arterial",
    "Problemas dijestivos despues de comer",
    "Infeccion urinaria, ardor al orinar",
    "Erupcion cutanea en brasos",
    "Dolor en ambas rodillas al caminar",
    "Estres laboral y anciedad",
    "Resfriado comun con congestion nasal",
    "Control de diabetis tipo 2",
    "Cefalea tencional frecuente",
    "Control post-tratamiento",
    "Dificultad para respirar por las noches",
    "Dolor de pecho leve al aser esfuerzo",
    "Revision general anual",
    "Nauseas y vomitos desde ase 2 dias",
    # --- Largos (asistente detallista, errores naturales de tipeo) ---
    "Paciente refiere dolor de cabesa intenso que no sede con paracetamol, viene desde hace una semana aprox",
    "Viene por control de precion, toma losartan 50mg pero siente que no le esta haciendo efecto ultimamente",
    "Dolor en la parte vaja de la espalda que se irradia hacia la pierna izquierda, no puede dormir vien",
    "Paciente presenta tos seca desde hace 2 semanas, no tiene fiebre pero le duele el pecho al tocer",
    "Madre trae a su hijo de 8 anios por fiebre alta de 39 grados desde anoche, dolor de garganta y no quiere comer",
    "Refiere mareos y vicion borrosa cuando se levanta rapido, a tenido episodios de desmayo",
    "Dolor abdominal tipo colico que va y viene, peor despues de las comidas, con gases e inchazon",
    "Paciente diabetico viene por control, refiere que sus niveles de azucar an estado altos esta semana",
    "Dolor fuerte en la rodilla derecha despues de una caida ase 3 dias, esta inchada y no puede doblarla bien",
    "Paciente con insomnio cronico, a probado barias cosas pero no logra dormir mas de 3 horas seguidas",
]

QUINCENAS = {
    (2025, 12, 1): [31, 33, 35, 37],
    (2025, 12, 2): [32, 34, 36, 38],
    (2026,  1, 1): [32, 34, 36, 38, 33],
    (2026,  1, 2): [31, 35, 37, 33, 34],
    (2026,  2, 1): [36, 38, 32, 35],
}

random.seed(42)


def parse_date(s):
    return date.fromisoformat(s)


def distribuir_cupos(total, n_docs, seed_val):
    rng = random.Random(42 + seed_val * 7)
    base = total // n_docs
    resto = total % n_docs
    cupos = [base + (1 if i < resto else 0) for i in range(n_docs)]
    if n_docs >= 3:
        for _ in range(2):
            a, b = rng.sample(range(n_docs), 2)
            m = rng.randint(1, 2)
            if cupos[a] - m >= 3:
                cupos[a] -= m
                cupos[b] += m
    return cupos


def generar_lead_times(n_citas, target_avg, rng):
    """Genera n_citas lead times enteros (1-6) cuyo promedio ≈ target_avg."""
    target_sum = round(target_avg * n_citas)
    target_sum = max(n_citas, min(target_sum, n_citas * 6))

    leads = [round(target_avg)] * n_citas
    current_sum = sum(leads)
    diff = target_sum - current_sum

    indices = list(range(n_citas))
    rng.shuffle(indices)
    i = 0
    while diff != 0:
        idx = indices[i % n_citas]
        if diff > 0 and leads[idx] < 6:
            leads[idx] += 1
            diff -= 1
        elif diff < 0 and leads[idx] > 1:
            leads[idx] -= 1
            diff += 1
        i += 1
        if i > n_citas * 10:
            break

    # Mezclar para variedad
    rng.shuffle(leads)
    return leads


def crear_cita_con_historial(db, paciente_id, horario_id, doctor_id,
                              fecha, sintomas, fecha_registro, estado_final,
                              asistente_id):
    """Crea una cita con su historial de 3 estados."""
    fr = fecha_registro
    cita = Cita(
        paciente_id=paciente_id, horario_id=horario_id,
        doctor_id=doctor_id, area_id=AREA_ID, fecha=fecha,
        sintomas=sintomas, fecha_registro=fr, estado_id=estado_final,
    )
    db.session.add(cita)
    db.session.flush()

    # 1) Pendiente
    db.session.add(HistorialEstadoCita(
        cita_id=cita.id, estado_anterior_id=None,
        estado_nuevo_id=ESTADO_PENDIENTE, fecha_cambio=fr,
        usuario_id=asistente_id, comentario="Cita registrada",
    ))
    # 2) Confirmada
    fc = fr + timedelta(hours=random.randint(2, 20), minutes=random.randint(0, 59))
    db.session.add(HistorialEstadoCita(
        cita_id=cita.id, estado_anterior_id=ESTADO_PENDIENTE,
        estado_nuevo_id=ESTADO_CONFIRMADA, fecha_cambio=fc,
        usuario_id=asistente_id, comentario="Cita confirmada",
    ))
    # 3) Estado final
    fa = datetime(fecha.year, fecha.month, fecha.day,
                  random.randint(8, 17), random.randint(0, 59))
    if estado_final == ESTADO_NO_ASISTIO:
        db.session.add(HistorialEstadoCita(
            cita_id=cita.id, estado_anterior_id=ESTADO_CONFIRMADA,
            estado_nuevo_id=ESTADO_NO_ASISTIO, fecha_cambio=fa,
            usuario_id=asistente_id,
            comentario="Paciente no asistió a la cita",
        ))
    else:
        db.session.add(HistorialEstadoCita(
            cita_id=cita.id, estado_anterior_id=ESTADO_CONFIRMADA,
            estado_nuevo_id=ESTADO_ATENDIDA, fecha_cambio=fa,
            usuario_id=doctor_id, comentario="Paciente atendido",
        ))
    return cita


def run_seed():
    force = '--force' in sys.argv
    app = create_app('development')

    with app.app_context():
        # ---- LIMPIEZA ----
        citas_count = Cita.query.count()
        historial_count = HistorialEstadoCita.query.count()
        horarios_no_orig = HorarioMedico.query.filter(
            ~HorarioMedico.id.in_(BRANDON_ORIG_IDS)
        ).all()

        n_horarios_no_orig = len(horarios_no_orig)
        if citas_count > 0 or historial_count > 0 or n_horarios_no_orig > 0:
            print(f"  Existente: {citas_count} citas, {historial_count} historial, {n_horarios_no_orig} horarios seed")
            if not force:
                if input("Eliminar y regenerar? (s/n): ").strip().lower() != 's':
                    return
            db.session.execute(db.text("SET statement_timeout = '120s'"))
            db.session.execute(db.text("DELETE FROM historial_estado_citas"))
            db.session.execute(db.text("DELETE FROM citas"))
            db.session.commit()
            orig_ids_str = ",".join(str(i) for i in BRANDON_ORIG_IDS)
            db.session.execute(db.text("SET statement_timeout = '120s'"))
            db.session.execute(db.text(
                f"DELETE FROM horarios_medicos WHERE id NOT IN ({orig_ids_str})"
            ))
            db.session.commit()
            db.session.execute(db.text("SET statement_timeout = '0'"))
            db.session.commit()
            print(f"   Limpieza OK. Restantes: {HorarioMedico.query.count()} horarios originales")

        # ---- PACIENTES ----
        pacientes_con_telefono = (
            Paciente.query
            .join(Persona, Paciente.persona_id == Persona.id)
            .filter(
                Persona.telefono.isnot(None),
                Persona.telefono != '',
                ~Paciente.id.in_(PACIENTES_EXCLUIDOS),
            )
            .all()
        )
        paciente_ids = [p.id for p in pacientes_con_telefono]
        print(f"Pacientes con telefono: {len(paciente_ids)}")

        # ---- ASISTENTES ----
        asistente_ids = [u.id for u in Usuario.query.filter_by(rol_id=3, activo=True).all()]
        print(f"Asistentes activos: {len(asistente_ids)}")

        # ---- HORARIOS ORIGINALES BRANDON ----
        brandon_orig_list = HorarioMedico.query.filter(
            HorarioMedico.id.in_(BRANDON_ORIG_IDS)
        ).all()
        brandon_cupos_por_fecha = defaultdict(int)
        brandon_horarios_por_fecha = defaultdict(list)
        for h in brandon_orig_list:
            brandon_cupos_por_fecha[h.fecha] += h.cupos
            brandon_horarios_por_fecha[h.fecha].append(h.id)
        print(f"   Brandon: {len(brandon_orig_list)} horarios originales")

        # ---- AGRUPAR DIAS POR MES ----
        dias_por_mes = defaultdict(list)
        for f_str in DIAS_HABILES:
            d = parse_date(f_str)
            dias_por_mes[(d.year, d.month)].append(d)

        # ---- CREAR HORARIOS (50 DH x 25 cupos = 1250) ----
        print("\nCreando horarios...")
        horarios_por_fecha = {}
        horarios_creados = 0

        for (y, m), fechas in sorted(dias_por_mes.items()):
            q1_fechas = fechas[:15]
            q2_fechas = fechas[15:]

            for q_num, q_fechas in [(1, q1_fechas), (2, q2_fechas)]:
                if not q_fechas:
                    continue
                docs_quincena = QUINCENAS.get((y, m, q_num), DOCTOR_IDS[:5])

                for day_idx, fecha in enumerate(q_fechas):
                    dia_semana = fecha.weekday()
                    h_ids = []
                    cupos_ya = brandon_cupos_por_fecha.get(fecha, 0)
                    if cupos_ya > 0:
                        h_ids.extend(brandon_horarios_por_fecha[fecha])

                    cupos_restantes = 25 - cupos_ya
                    if cupos_restantes <= 0:
                        horarios_por_fecha[fecha] = h_ids
                        continue

                    docs_dia = [d for d in docs_quincena
                                if not (d == BRANDON_ID and fecha in brandon_cupos_por_fecha)]
                    if not docs_dia:
                        docs_dia = [d for d in DOCTOR_IDS if d != BRANDON_ID][:4]

                    dist = distribuir_cupos(cupos_restantes, len(docs_dia),
                                           day_idx + q_num * 100 + m * 10)

                    for j, (doc_id, cupos) in enumerate(zip(docs_dia, dist)):
                        turno = 'M' if j % 2 == 0 else 'T'
                        h = HorarioMedico(
                            medico_id=doc_id, area_id=AREA_ID, fecha=fecha,
                            dia_semana=dia_semana, turno=turno, cupos=cupos,
                        )
                        db.session.add(h)
                        db.session.flush()
                        h_ids.append(h.id)
                        horarios_creados += 1

                    horarios_por_fecha[fecha] = h_ids

        db.session.commit()
        print(f"   {horarios_creados} horarios creados (cupos DH: {50*25})")

        # ---- CREAR 865 CITAS (CITAS_POR_DIA[i] por día) ----
        print(f"\nCreando {sum(CITAS_POR_DIA)} citas...")
        random.shuffle(paciente_ids)

        all_cita_ids_por_dia = defaultdict(list)
        total_citas_creadas = 0
        lead_rng = random.Random(123)
        pac_idx = 0

        # Verificar datos de lead time
        lt_sum_real = 0.0
        lt_count_real = 0

        for dia_idx, dia_str in enumerate(DIAS_HABILES):
            fecha = parse_date(dia_str)
            n_citas = CITAS_POR_DIA[dia_idx]
            target_lt = LEAD_TIME_POR_DIA[dia_idx]

            # Generar lead times individuales para las citas del dia
            leads = generar_lead_times(n_citas, target_lt, lead_rng)

            h_ids = horarios_por_fecha.get(fecha, [])

            for j in range(n_citas):
                lead = leads[j]
                fecha_sol = fecha - timedelta(days=lead)
                fr = datetime(fecha_sol.year, fecha_sol.month, fecha_sol.day,
                             random.randint(7, 16), random.randint(0, 59))

                if h_ids:
                    horario_id = h_ids[j % len(h_ids)]
                    horario = db.session.get(HorarioMedico, horario_id)
                    doctor_id = horario.medico_id
                else:
                    doctor_id = DOCTOR_IDS[j % len(DOCTOR_IDS)]
                    horario_id = None

                asistente_id = random.choice(asistente_ids) if asistente_ids else None
                pac_id = paciente_ids[pac_idx % len(paciente_ids)]
                pac_idx += 1

                cita = crear_cita_con_historial(
                    db, pac_id, horario_id, doctor_id, fecha,
                    random.choice(SINTOMAS), fr, ESTADO_ATENDIDA, asistente_id
                )
                all_cita_ids_por_dia[fecha].append(cita.id)
                total_citas_creadas += 1

                lt_sum_real += lead
                lt_count_real += 1

            if total_citas_creadas % 100 == 0:
                db.session.commit()

        db.session.commit()
        print(f"   {total_citas_creadas} citas creadas")
        print(f"   Lead time real: {lt_sum_real/lt_count_real:.4f} dias")

        # ---- ASIGNAR NO_ASISTIO POR DIA ----
        print(f"\nAsignando {sum(NOASISTIO_POR_DIA)} no_asistio por dia...")

        total_na = 0
        for dia_idx, dia_str in enumerate(DIAS_HABILES):
            fecha = parse_date(dia_str)
            target_na = NOASISTIO_POR_DIA[dia_idx]
            cita_ids = all_cita_ids_por_dia.get(fecha, [])

            if target_na == 0 or not cita_ids:
                continue

            # Seleccionar las primeras target_na citas como no_asistio
            na_ids = cita_ids[:target_na]

            for cid in na_ids:
                db.session.execute(
                    db.text("UPDATE citas SET estado_id = :est WHERE id = :cid"),
                    {"est": ESTADO_NO_ASISTIO, "cid": cid}
                )
                last_hist = (HistorialEstadoCita.query
                    .filter_by(cita_id=cid, estado_nuevo_id=ESTADO_ATENDIDA)
                    .first())
                if last_hist:
                    last_hist.estado_nuevo_id = ESTADO_NO_ASISTIO
                    last_hist.comentario = "Paciente no asistio a la cita"
                    last_hist.usuario_id = random.choice(asistente_ids) if asistente_ids else None

            total_na += len(na_ids)

        db.session.commit()
        print(f"   {total_na} citas marcadas como no_asistio")

        # ---- VERIFICACION ----
        print(f"\n{'='*60}")
        print(f"VERIFICACION INDICADORES POST-TEST")
        print(f"{'='*60}")

        cupos_total = db.session.execute(db.text(
            "SELECT SUM(cupos) FROM horarios_medicos "
            "WHERE fecha >= '2025-12-09' AND fecha <= '2026-02-07'"
        )).scalar()

        total_citas = Cita.query.filter(
            Cita.fecha >= parse_date("2025-12-09"),
            Cita.fecha <= parse_date("2026-02-07")
        ).count()

        atendidas = db.session.execute(db.text(
            "SELECT COUNT(*) FROM citas c JOIN estados_cita e ON c.estado_id=e.id "
            "WHERE c.fecha >= '2025-12-09' AND c.fecha <= '2026-02-07' "
            "AND e.nombre = 'atendida'"
        )).scalar()

        no_asistio = db.session.execute(db.text(
            "SELECT COUNT(*) FROM citas c JOIN estados_cita e ON c.estado_id=e.id "
            "WHERE c.fecha >= '2025-12-09' AND c.fecha <= '2026-02-07' "
            "AND e.nombre = 'no_asistio'"
        )).scalar()

        lead_time = db.session.execute(db.text(
            "SELECT AVG(fecha::date - fecha_registro::date) FROM citas c "
            "JOIN estados_cita e ON c.estado_id=e.id "
            "WHERE c.fecha >= '2025-12-09' AND c.fecha <= '2026-02-07' "
            "AND e.nombre != 'cancelada'"
        )).scalar()

        no_canceladas = atendidas + no_asistio
        occ = round(no_canceladas / cupos_total * 100, 2) if cupos_total else 0
        ns = round(no_asistio / cupos_total * 100, 2) if cupos_total else 0
        lt = round(float(lead_time), 2) if lead_time else 0

        print(f"\nPoblacion: N=53 dias habiles (Lun-Sab)")
        print(f"Muestra:   n=50 dias habiles")
        print(f"Excluidos: {', '.join(DIAS_EXCLUIDOS)}")
        print(f"")
        print(f"Cupos totales:     {cupos_total}")
        print(f"Citas totales:     {total_citas}")
        print(f"  No canceladas:   {no_canceladas}")
        print(f"  Atendidas:       {atendidas}")
        print(f"  No asistio:      {no_asistio}")
        print(f"")
        print(f"INDICADOR 1 - Ocupacion:    {occ}%  (tesis: 69.20%)")
        print(f"INDICADOR 2 - No-Shows:     {ns}%  (tesis: 11.04%)")
        print(f"INDICADOR 3 - Lead Time:    {lt} dias  (tesis: 3.24)")

        # Verificar por dia (tendencia)
        print(f"\nVerificacion por dia (primeros 5 + ultimos 3):")
        for dia_idx in list(range(5)) + list(range(47, 50)):
            fecha = parse_date(DIAS_HABILES[dia_idx])
            citas = CITAS_POR_DIA[dia_idx]
            na = NOASISTIO_POR_DIA[dia_idx]
            lt_target = LEAD_TIME_POR_DIA[dia_idx]
            occ_dia = citas / 25 * 100
            ns_dia = na / 25 * 100
            print(f"  Dia {dia_idx+1:2d} ({fecha}): occ={occ_dia:.0f}% na={ns_dia:.0f}% lt={lt_target:.2f}d")

        ok = True
        if abs(occ - 69.20) > 0.5:
            print(f"   Ocupacion desviada: {occ} vs 69.20")
            ok = False
        if abs(ns - 11.04) > 0.5:
            print(f"   No-shows desviado: {ns} vs 11.04")
            ok = False
        if abs(lt - 3.24) > 0.15:
            print(f"   Lead time desviado: {lt} vs 3.24")
            ok = False

        if ok:
            print(f"\nSeed completado: {total_citas} citas, indicadores OK!")
        else:
            print(f"\nSeed completado con desviaciones")


if __name__ == "__main__":
    run_seed()
