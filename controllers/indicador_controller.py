"""
Controlador de Indicadores de Gestión de Citas Médicas.
Implementa las 3 dimensiones para la tesis:
- Dimensión 1: Utilización de Capacidad
- Dimensión 2: Tasa de Inasistencia (No-Shows)
- Dimensión 3: Lead Time (Tiempo de Anticipación)
"""

from flask import jsonify, request
from extensions.database import db
from models.cita_model import Cita
from models.horario_medico_model import HorarioMedico
from models.area_model import Area
from sqlalchemy import func, case, extract
from datetime import datetime, timedelta


class IndicadorController:
    
    @staticmethod
    def obtener_indicadores():
        """
        Obtiene los 3 indicadores principales para el período especificado.
        
        Query params:
        - fecha_inicio: Fecha inicial (YYYY-MM-DD) (requerido)
        - fecha_fin: Fecha final (YYYY-MM-DD) (requerido)
        - area_id: Filtrar por área específica (opcional)
        
        Returns:
            JSON con los 3 indicadores calculados
        """
        try:
            fecha_inicio_str = request.args.get('fecha_inicio')
            fecha_fin_str = request.args.get('fecha_fin')
            area_id = request.args.get('area_id', type=int)
            
            # Validar fechas requeridas
            if not fecha_inicio_str or not fecha_fin_str:
                return jsonify({
                    'success': False,
                    'error': 'Los parámetros fecha_inicio y fecha_fin son requeridos (formato: YYYY-MM-DD)'
                }), 400
            
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400
            
            if fecha_inicio > fecha_fin:
                return jsonify({
                    'success': False,
                    'error': 'La fecha de inicio debe ser anterior o igual a la fecha fin'
                }), 400
            
            # ==================== INDICADOR 1: UTILIZACIÓN DE CAPACIDAD ====================
            # Fórmula: (Citas No Canceladas / Cupos Totales) * 100
            
            # Query para cupos totales
            cupos_query = db.session.query(func.sum(HorarioMedico.cupos)).filter(
                HorarioMedico.fecha >= fecha_inicio,
                HorarioMedico.fecha <= fecha_fin
            )
            if area_id:
                cupos_query = cupos_query.filter(HorarioMedico.area_id == area_id)
            
            cupos_totales = cupos_query.scalar() or 0
            
            # Query para citas no canceladas
            citas_query = db.session.query(func.count(Cita.id)).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado != 'cancelada'
            )
            if area_id:
                citas_query = citas_query.filter(Cita.area_id == area_id)
            
            citas_programadas = citas_query.scalar() or 0
            
            utilizacion = round((citas_programadas / cupos_totales * 100), 2) if cupos_totales > 0 else 0
            
            # ==================== INDICADOR 2: TASA DE INASISTENCIA ====================
            # Fórmula: (Citas No Asistió / Citas Confirmadas Totales) * 100
            
            # Citas con estado final (confirmadas que llegaron a resolución)
            citas_confirmadas_query = db.session.query(func.count(Cita.id)).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado.in_(['confirmada', 'atendida', 'no_asistio'])
            )
            if area_id:
                citas_confirmadas_query = citas_confirmadas_query.filter(Cita.area_id == area_id)
            
            citas_confirmadas_total = citas_confirmadas_query.scalar() or 0
            
            # No shows
            no_shows_query = db.session.query(func.count(Cita.id)).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado == 'no_asistio'
            )
            if area_id:
                no_shows_query = no_shows_query.filter(Cita.area_id == area_id)
            
            no_shows = no_shows_query.scalar() or 0
            
            tasa_inasistencia = round((no_shows / citas_confirmadas_total * 100), 2) if citas_confirmadas_total > 0 else 0
            
            # ==================== INDICADOR 3: LEAD TIME (TIEMPO DE ANTICIPACIÓN) ====================
            # Fórmula: Promedio de (Fecha Cita - Fecha Registro)
            # En PostgreSQL: la resta de dos fechas devuelve INTEGER (días)
            
            lead_time_query = db.session.query(
                func.avg(
                    func.cast(Cita.fecha, db.Date) - func.cast(Cita.fecha_registro, db.Date)
                )
            ).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado != 'cancelada',
                Cita.fecha.isnot(None)
            )
            if area_id:
                lead_time_query = lead_time_query.filter(Cita.area_id == area_id)
            
            lead_time_promedio = lead_time_query.scalar()
            lead_time_promedio = round(float(lead_time_promedio), 2) if lead_time_promedio else 0
            
            # ==================== ESTADÍSTICAS ADICIONALES ====================
            
            # Citas atendidas
            citas_atendidas_query = db.session.query(func.count(Cita.id)).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado == 'atendida'
            )
            if area_id:
                citas_atendidas_query = citas_atendidas_query.filter(Cita.area_id == area_id)
            
            citas_atendidas = citas_atendidas_query.scalar() or 0
            
            # Citas canceladas
            citas_canceladas_query = db.session.query(func.count(Cita.id)).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin,
                Cita.estado == 'cancelada'
            )
            if area_id:
                citas_canceladas_query = citas_canceladas_query.filter(Cita.area_id == area_id)
            
            citas_canceladas = citas_canceladas_query.scalar() or 0
            
            # Tasa de atención efectiva
            tasa_atencion = round((citas_atendidas / citas_confirmadas_total * 100), 2) if citas_confirmadas_total > 0 else 0
            
            return jsonify({
                'success': True,
                'periodo': {
                    'fecha_inicio': fecha_inicio_str,
                    'fecha_fin': fecha_fin_str,
                    'area_id': area_id
                },
                'indicadores': {
                    'utilizacion_capacidad': {
                        'nombre': 'Utilización de Capacidad',
                        'valor': utilizacion,
                        'unidad': '%',
                        'descripcion': 'Porcentaje de cupos utilizados respecto al total disponible',
                        'formula': '(Citas No Canceladas / Cupos Totales) × 100',
                        'componentes': {
                            'citas_programadas': citas_programadas,
                            'cupos_totales': cupos_totales
                        }
                    },
                    'tasa_inasistencia': {
                        'nombre': 'Tasa de Inasistencia (No-Shows)',
                        'valor': tasa_inasistencia,
                        'unidad': '%',
                        'descripcion': 'Porcentaje de pacientes que no asistieron a su cita confirmada',
                        'formula': '(Citas No Asistió / Citas Confirmadas Totales) × 100',
                        'componentes': {
                            'no_shows': no_shows,
                            'citas_confirmadas': citas_confirmadas_total
                        }
                    },
                    'lead_time': {
                        'nombre': 'Tiempo de Anticipación (Lead Time)',
                        'valor': lead_time_promedio,
                        'unidad': 'días',
                        'descripcion': 'Días promedio entre la solicitud y la fecha de la cita',
                        'formula': 'Promedio(Fecha Cita - Fecha Registro)',
                        'componentes': {}
                    }
                },
                'estadisticas_adicionales': {
                    'citas_atendidas': citas_atendidas,
                    'citas_canceladas': citas_canceladas,
                    'citas_no_asistio': no_shows,
                    'tasa_atencion_efectiva': tasa_atencion
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al calcular indicadores: {str(e)}'
            }), 500
    
    @staticmethod
    def obtener_indicadores_por_periodo():
        """
        Obtiene los indicadores agrupados por período (día, semana, mes).
        Útil para generar gráficos de tendencia.
        
        Query params:
        - fecha_inicio: Fecha inicial (YYYY-MM-DD)
        - fecha_fin: Fecha final (YYYY-MM-DD)
        - agrupacion: 'dia', 'semana', 'mes' (default: mes)
        - area_id: Filtrar por área (opcional)
        """
        try:
            fecha_inicio_str = request.args.get('fecha_inicio')
            fecha_fin_str = request.args.get('fecha_fin')
            agrupacion = request.args.get('agrupacion', 'mes')
            area_id = request.args.get('area_id', type=int)
            
            if not fecha_inicio_str or not fecha_fin_str:
                return jsonify({
                    'success': False,
                    'error': 'Los parámetros fecha_inicio y fecha_fin son requeridos'
                }), 400
            
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400
            
            # Determinar la función de agrupación
            if agrupacion == 'dia':
                group_func = Cita.fecha
                group_func_horario = HorarioMedico.fecha
            elif agrupacion == 'semana':
                group_func = func.date_trunc('week', Cita.fecha)
                group_func_horario = func.date_trunc('week', HorarioMedico.fecha)
            else:  # mes por defecto
                group_func = func.date_trunc('month', Cita.fecha)
                group_func_horario = func.date_trunc('month', HorarioMedico.fecha)
            
            # Obtener datos de citas agrupados
            citas_query = db.session.query(
                group_func.label('periodo'),
                func.count(Cita.id).label('total_citas'),
                func.count(case((Cita.estado != 'cancelada', 1))).label('citas_no_canceladas'),
                func.count(case((Cita.estado == 'no_asistio', 1))).label('no_shows'),
                func.count(case((Cita.estado == 'atendida', 1))).label('atendidas'),
                func.count(case((Cita.estado.in_(['confirmada', 'atendida', 'no_asistio']), 1))).label('confirmadas_total'),
                func.avg(
                    func.cast(Cita.fecha, db.Date) - func.cast(Cita.fecha_registro, db.Date)
                ).label('lead_time_promedio')
            ).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin
            )
            
            if area_id:
                citas_query = citas_query.filter(Cita.area_id == area_id)
            
            citas_data = citas_query.group_by(group_func).order_by(group_func).all()
            
            # Obtener cupos por período
            cupos_query = db.session.query(
                group_func_horario.label('periodo'),
                func.sum(HorarioMedico.cupos).label('cupos_totales')
            ).filter(
                HorarioMedico.fecha >= fecha_inicio,
                HorarioMedico.fecha <= fecha_fin
            )
            
            if area_id:
                cupos_query = cupos_query.filter(HorarioMedico.area_id == area_id)
            
            cupos_data = {
                str(row.periodo.date() if hasattr(row.periodo, 'date') else row.periodo): row.cupos_totales 
                for row in cupos_query.group_by(group_func_horario).all()
            }
            
            # Construir resultado
            resultado = []
            for row in citas_data:
                periodo_str = str(row.periodo.date() if hasattr(row.periodo, 'date') else row.periodo)
                cupos = cupos_data.get(periodo_str, 0) or 0
                
                utilizacion = round((row.citas_no_canceladas / cupos * 100), 2) if cupos > 0 else 0
                tasa_inasistencia = round((row.no_shows / row.confirmadas_total * 100), 2) if row.confirmadas_total > 0 else 0
                lead_time = round(float(row.lead_time_promedio), 2) if row.lead_time_promedio else 0
                
                resultado.append({
                    'periodo': periodo_str,
                    'utilizacion_capacidad': utilizacion,
                    'tasa_inasistencia': tasa_inasistencia,
                    'lead_time': lead_time,
                    'detalles': {
                        'total_citas': row.total_citas,
                        'citas_no_canceladas': row.citas_no_canceladas,
                        'no_shows': row.no_shows,
                        'atendidas': row.atendidas,
                        'cupos_totales': cupos
                    }
                })
            
            return jsonify({
                'success': True,
                'agrupacion': agrupacion,
                'periodo': {
                    'fecha_inicio': fecha_inicio_str,
                    'fecha_fin': fecha_fin_str
                },
                'datos': resultado
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al obtener indicadores por período: {str(e)}'
            }), 500
    
    @staticmethod
    def obtener_indicadores_por_area():
        """
        Obtiene los indicadores agrupados por área/especialidad.
        Útil para comparar el rendimiento entre diferentes servicios.
        
        Query params:
        - fecha_inicio: Fecha inicial (YYYY-MM-DD)
        - fecha_fin: Fecha final (YYYY-MM-DD)
        """
        try:
            fecha_inicio_str = request.args.get('fecha_inicio')
            fecha_fin_str = request.args.get('fecha_fin')
            
            if not fecha_inicio_str or not fecha_fin_str:
                return jsonify({
                    'success': False,
                    'error': 'Los parámetros fecha_inicio y fecha_fin son requeridos'
                }), 400
            
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400
            
            # Query principal agrupado por área
            citas_por_area = db.session.query(
                Area.id.label('area_id'),
                Area.nombre.label('area_nombre'),
                func.count(Cita.id).label('total_citas'),
                func.count(case((Cita.estado != 'cancelada', 1))).label('citas_no_canceladas'),
                func.count(case((Cita.estado == 'no_asistio', 1))).label('no_shows'),
                func.count(case((Cita.estado == 'atendida', 1))).label('atendidas'),
                func.count(case((Cita.estado.in_(['confirmada', 'atendida', 'no_asistio']), 1))).label('confirmadas_total'),
                func.avg(
                    func.cast(Cita.fecha, db.Date) - func.cast(Cita.fecha_registro, db.Date)
                ).label('lead_time_promedio')
            ).join(Area, Cita.area_id == Area.id).filter(
                Cita.fecha >= fecha_inicio,
                Cita.fecha <= fecha_fin
            ).group_by(Area.id, Area.nombre).all()
            
            # Cupos por área
            cupos_por_area = db.session.query(
                HorarioMedico.area_id,
                func.sum(HorarioMedico.cupos).label('cupos_totales')
            ).filter(
                HorarioMedico.fecha >= fecha_inicio,
                HorarioMedico.fecha <= fecha_fin
            ).group_by(HorarioMedico.area_id).all()
            
            cupos_dict = {row.area_id: row.cupos_totales or 0 for row in cupos_por_area}
            
            # Construir resultado
            resultado = []
            for row in citas_por_area:
                cupos = cupos_dict.get(row.area_id, 0)
                
                utilizacion = round((row.citas_no_canceladas / cupos * 100), 2) if cupos > 0 else 0
                tasa_inasistencia = round((row.no_shows / row.confirmadas_total * 100), 2) if row.confirmadas_total > 0 else 0
                lead_time = round(float(row.lead_time_promedio), 2) if row.lead_time_promedio else 0
                
                resultado.append({
                    'area_id': row.area_id,
                    'area_nombre': row.area_nombre,
                    'utilizacion_capacidad': utilizacion,
                    'tasa_inasistencia': tasa_inasistencia,
                    'lead_time': lead_time,
                    'detalles': {
                        'total_citas': row.total_citas,
                        'citas_no_canceladas': row.citas_no_canceladas,
                        'no_shows': row.no_shows,
                        'atendidas': row.atendidas,
                        'cupos_totales': cupos
                    }
                })
            
            return jsonify({
                'success': True,
                'periodo': {
                    'fecha_inicio': fecha_inicio_str,
                    'fecha_fin': fecha_fin_str
                },
                'areas': resultado
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al obtener indicadores por área: {str(e)}'
            }), 500
