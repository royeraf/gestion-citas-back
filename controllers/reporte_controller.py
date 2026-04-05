from flask import request, jsonify, send_file
from datetime import datetime, date
from extensions.database import db
from models.cita_model import Cita
from models.estado_cita_model import EstadoCita
from models.area_model import Area
from models.paciente_model import Paciente
from sqlalchemy import func
import calendar

class ReporteController:
    @staticmethod
    def obtener_estadisticas():
        try:
            fecha_inicio_str = request.args.get('fecha_inicio')
            fecha_fin_str = request.args.get('fecha_fin')
            area_id = request.args.get('area_id')
            
            # Default to current month if no dates provided
            today = date.today()
            if not fecha_inicio_str:
                fecha_inicio = today.replace(day=1)
            else:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                
            if not fecha_fin_str:
                fecha_fin = today
            else:
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

            # Base query
            query = db.session.query(Cita).join(EstadoCita).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin
            )
            
            if area_id:
                query = query.filter(Cita.area_id == area_id)

            todas_las_citas = query.all()
            
            # Stats Generales
            total_citas = len(todas_las_citas)
            
            # Count by estado
            estado_counts = {}
            for cita in todas_las_citas:
                estado_nombre = cita.estado_rel.nombre if cita.estado_rel else 'desconocido'
                estado_counts[estado_nombre] = estado_counts.get(estado_nombre, 0) + 1

            atendidas = estado_counts.get('atendida', 0)
            cancelaciones = estado_counts.get('cancelada', 0)
            confirmadas = estado_counts.get('confirmada', 0)
            
            tasa_asistencia = 0
            # Consideramos para la tasa de asistencia: atendidas / (atendidas + no_asistio + confirmadas previas)
            # Simplificamos: atendidas / total_citas
            if total_citas > 0:
                 # usually it's (atendidas) / (total programadas validas)
                 # programadas = total - canceladas
                 citas_validas = total_citas - cancelaciones
                 if citas_validas > 0:
                     tasa_asistencia = round((atendidas / citas_validas) * 100, 1)

            # Citas Atendidas Por Mes (para el gráfico)
            # Agrupamos por mes
            meses_str = {
                1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
            }
            citas_por_mes_dict = {}
            for cita in todas_las_citas:
                if cita.estado_rel and cita.estado_rel.nombre == 'atendida' and cita.fecha:
                    mes = cita.fecha.month
                    citas_por_mes_dict[mes] = citas_por_mes_dict.get(mes, 0) + 1
            
            citas_atendidas_por_mes = [
                {"nombre": meses_str[mes], "cantidad": cantidad}
                for mes, cantidad in sorted(citas_por_mes_dict.items())
            ]

            # Estado de Citas (Pie Chart)
            colores_estado = {
                'atendida': '#10b981',
                'cancelada': '#ef4444',
                'no_asistio': '#f59e0b',
                'pendiente': '#6366f1',
                'confirmada': '#3b82f6',
                'referido': '#8b5cf6'
            }
            
            estado_citas_arr = []
            for estado, count in estado_counts.items():
                if count > 0:
                    estado_citas_arr.append({
                        "label": estado.capitalize(),
                        "value": count,
                        "color": colores_estado.get(estado, '#9ca3af')
                    })
            
            # Citas por Especialidad
            especialidad_counts = {}
            for cita in todas_las_citas:
                esp_nombre = cita.area_rel.nombre if cita.area_rel else 'General'
                especialidad_counts[esp_nombre] = especialidad_counts.get(esp_nombre, 0) + 1
                
            citas_por_especialidad = []
            for nombre, cantidad in especialidad_counts.items():
                porcentaje = round((cantidad / total_citas) * 100, 1) if total_citas > 0 else 0
                citas_por_especialidad.append({
                    "nombre": nombre,
                    "cantidad": cantidad,
                    "porcentaje": porcentaje
                })
            
            # Sort citas por especialidad descendente
            citas_por_especialidad.sort(key=lambda x: x["cantidad"], reverse=True)

            # Detalle de Citas (latest 50 for the table to avoid massive payloads)
            todas_las_citas.sort(key=lambda x: x.fecha, reverse=True)
            citas_detalle = []
            for cita in todas_las_citas[:50]:
                paciente_nombre = "Desconocido"
                if cita.paciente:
                     paciente_nombre = f"{cita.paciente.nombres} {cita.paciente.apellido_paterno}"
                     
                citas_detalle.append({
                    "id": cita.id,
                    "fecha": str(cita.fecha),
                    "paciente": paciente_nombre,
                    "especialidad": cita.area_rel.nombre if cita.area_rel else "General",
                    "estado": cita.estado_rel.nombre if cita.estado_rel else "pendiente"
                })

            return jsonify({
                "success": True,
                "stats": {
                    "totalCitas": total_citas,
                    "tasaAsistencia": tasa_asistencia,
                    "cancelaciones": cancelaciones
                },
                "citasAtendidasPorMes": citas_atendidas_por_mes,
                "estadoCitas": estado_citas_arr,
                "citasPorEspecialidad": citas_por_especialidad,
                "citasDetalle": citas_detalle
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    def exportar_pdf():
        try:
            from services.pdf_service import PDFService

            fecha_inicio_str = request.args.get('fecha_inicio')
            fecha_fin_str = request.args.get('fecha_fin')
            area_id = request.args.get('area_id')

            today = date.today()
            if not fecha_inicio_str:
                fecha_inicio = today.replace(day=1)
            else:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()

            if not fecha_fin_str:
                fecha_fin = today
            else:
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

            query = db.session.query(Cita).outerjoin(EstadoCita).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin
            )

            area_nombre = None
            if area_id:
                query = query.filter(Cita.area_id == area_id)
                area_obj = db.session.query(Area).filter_by(id=area_id).first()
                if area_obj:
                    area_nombre = area_obj.nombre

            todas_las_citas = query.all()
            total_citas = len(todas_las_citas)

            estado_counts = {}
            for cita in todas_las_citas:
                estado_nombre = cita.estado_rel.nombre if cita.estado_rel else 'desconocido'
                estado_counts[estado_nombre] = estado_counts.get(estado_nombre, 0) + 1

            atendidas = estado_counts.get('atendida', 0)
            cancelaciones = estado_counts.get('cancelada', 0)

            tasa_asistencia = 0
            if total_citas > 0:
                citas_validas = total_citas - cancelaciones
                if citas_validas > 0:
                    tasa_asistencia = round((atendidas / citas_validas) * 100, 1)

            stats = {
                'totalCitas': total_citas,
                'tasaAsistencia': tasa_asistencia,
                'cancelaciones': cancelaciones
            }

            especialidad_counts = {}
            for cita in todas_las_citas:
                esp_nombre = cita.area_rel.nombre if cita.area_rel else 'General'
                especialidad_counts[esp_nombre] = especialidad_counts.get(esp_nombre, 0) + 1

            citas_por_especialidad = []
            for nombre, cantidad in especialidad_counts.items():
                porcentaje = round((cantidad / total_citas) * 100, 1) if total_citas > 0 else 0
                citas_por_especialidad.append({
                    "nombre": nombre,
                    "cantidad": cantidad,
                    "porcentaje": porcentaje
                })
            citas_por_especialidad.sort(key=lambda x: x["cantidad"], reverse=True)

            todas_las_citas.sort(key=lambda x: x.fecha, reverse=True)
            citas_detalle = []
            for cita in todas_las_citas[:50]:
                paciente_nombre = "Desconocido"
                if cita.paciente:
                    paciente_nombre = f"{cita.paciente.nombres} {cita.paciente.apellido_paterno}"
                citas_detalle.append({
                    "fecha": str(cita.fecha),
                    "paciente": paciente_nombre,
                    "especialidad": cita.area_rel.nombre if cita.area_rel else "General",
                    "estado": cita.estado_rel.nombre if cita.estado_rel else "pendiente"
                })

            pdf_buffer = PDFService.generar_pdf_reporte_estadisticas(
                fecha_inicio=str(fecha_inicio),
                fecha_fin=str(fecha_fin),
                area_nombre=area_nombre,
                stats=stats,
                citas_por_especialidad=citas_por_especialidad,
                citas_detalle=citas_detalle
            )

            filename = f"reporte_citas_{str(fecha_inicio)}_{str(fecha_fin)}.pdf"

            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500
