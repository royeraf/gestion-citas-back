"""
Servicio para generación de PDFs de citas médicas.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFService:
    """Servicio para generación de documentos PDF."""
    
    @staticmethod
    def generar_pdf_citas_confirmadas(fecha: str, area: dict, citas: list, medico: dict = None) -> BytesIO:
        """
        Genera un PDF con la lista de citas confirmadas para impresión.
        Las citas se separan por turno (Mañana y Tarde).
        
        Args:
            fecha: Fecha de las citas (YYYY-MM-DD)
            area: Diccionario con id y nombre del área
            citas: Lista de citas con datos del paciente y horario
            medico: Diccionario con datos del médico (opcional)
            
        Returns:
            BytesIO: Buffer con el contenido del PDF
        """
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para el título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=6*mm,
            textColor=colors.HexColor('#1a365d'),
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulo
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=4*mm,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica'
        )
        
        # Estilo para información adicional
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=2*mm,
            textColor=colors.HexColor('#4a5568')
        )
        
        # Estilo para el pie de página
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#718096')
        )
        
        # Estilo para encabezado de turno - Mañana
        turno_manana_style = ParagraphStyle(
            'TurnoMananaStyle',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceBefore=8*mm,
            spaceAfter=4*mm,
            textColor=colors.HexColor('#b45309'),  # Amber-700
            fontName='Helvetica-Bold'
        )
        
        # Estilo para encabezado de turno - Tarde
        turno_tarde_style = ParagraphStyle(
            'TurnoTardeStyle',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceBefore=8*mm,
            spaceAfter=4*mm,
            textColor=colors.HexColor('#4338ca'),  # Indigo-700
            fontName='Helvetica-Bold'
        )
        
        # Elementos del documento
        elements = []
        
        # Título principal
        elements.append(Paragraph("CENTRO DE SALUD LA UNIÓN", title_style))
        elements.append(Paragraph("Listado de atención", subtitle_style))
        elements.append(Spacer(1, 3*mm))
        
        # Formatear fecha para mostrar
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_formateada = fecha_obj.strftime("%d de %B de %Y")
            # Traducir meses al español
            meses = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            for en, es in meses.items():
                fecha_formateada = fecha_formateada.replace(en, es)
        except:
            fecha_formateada = fecha
        
        # Información del área, fecha y médico
        # Información del área, fecha y médico en una sola línea
        info_parts = []
        info_parts.append(f"<b>Área:</b> {area.get('nombre', 'No especificada')}")
        
        if medico:
            info_parts.append(f"<b>Profesional:</b> {medico.get('nombre', 'No especificado')}")
            
        info_parts.append(f"<b>Fecha:</b> {fecha_formateada}")
        # info_parts.append(f"<b>Total:</b> {len(citas)}")

        
        # Unir partes con un separador visual
        info_text = "  <font color='#cbd5e0'>|</font>  ".join(info_parts)
        
        # Centrar la información
        info_style.alignment = TA_CENTER
        elements.append(Paragraph(info_text, info_style))
        
        # Separar citas por turno
        citas_manana = []
        citas_tarde = []
        citas_sin_turno = []
        
        for cita in citas:
            horario = cita.get('horario', {}) or {}
            turno = horario.get('turno', '')
            
            if turno == 'M':
                citas_manana.append(cita)
            elif turno == 'T':
                citas_tarde.append(cita)
            else:
                citas_sin_turno.append(cita)
        
        # Determinar si mostrar columna de médico (si no se filtró por uno específico)
        mostrar_columna_medico = medico is None
        
        # Función auxiliar para crear tabla de citas
        def crear_tabla_citas(citas_turno, color_header):
            if not citas_turno:
                return None
            
            # Encabezados de la tabla
            headers = ['N°', 'DNI', 'Paciente', 'Hora']
            if mostrar_columna_medico:
                headers.append('Profesional Asignado')
                
            table_data = [headers]
            
            # Agregar filas de citas
            for idx, cita in enumerate(citas_turno, start=1):
                paciente = cita.get('paciente', {}) or {}
                horario = cita.get('horario', {}) or {}
                medico_cita = cita.get('medico', {}) or {}
                
                # Nombre completo del paciente
                nombre_completo = f"{paciente.get('apellido_paterno', '')} {paciente.get('apellido_materno', '')}, {paciente.get('nombres', '')}"
                nombre_completo = nombre_completo.strip().strip(',').strip()
                
                # Horario
                hora_inicio = horario.get('hora_inicio', '')
                hora_fin = horario.get('hora_fin', '')
                if hora_inicio and hora_fin:
                    hora_inicio = hora_inicio[:5]
                    hora_fin = hora_fin[:5]
                    horario_str = f"{hora_inicio} - {hora_fin}"
                else:
                    horario_str = "-"
                
                row = [
                    str(idx),
                    paciente.get('dni', 'N/A'),
                    nombre_completo,
                    horario_str
                ]
                
                if mostrar_columna_medico:
                    row.append(medico_cita.get('nombre', 'No asignado'))
                
                table_data.append(row)
            
            # Configurar anchos de columna
            if mostrar_columna_medico:
                col_widths = [1.2*cm, 2.5*cm, 6*cm, 3*cm, 5*cm]
            else:
                col_widths = [1.2*cm, 2.5*cm, 10*cm, 3*cm]
                
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Estilo de la tabla
            table_style = TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), color_header),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Cuerpo
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # N°
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # DNI
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Paciente
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Hora
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('BOX', (0, 0), (-1, -1), 1, color_header),
                # ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ])
            
            # Alineación especial para la columna de médico si existe
            if mostrar_columna_medico:
                table_style.add('ALIGN', (4, 1), (4, -1), 'LEFT')
            
            table.setStyle(table_style)
            return table
        
        # Turno Mañana
        if citas_manana:
            elements.append(Paragraph(f"TURNO MAÑANA (07:30 - 13:30) — {len(citas_manana)} citas", turno_manana_style))
            tabla_manana = crear_tabla_citas(citas_manana, colors.HexColor('#d97706'))
            if tabla_manana:
                elements.append(tabla_manana)
        
        # Turno Tarde
        if citas_tarde:
            elements.append(Paragraph(f"TURNO TARDE (13:30 - 19:30) — {len(citas_tarde)} citas", turno_tarde_style))
            tabla_tarde = crear_tabla_citas(citas_tarde, colors.HexColor('#4f46e5'))
            if tabla_tarde:
                elements.append(tabla_tarde)
        
        # Sin Turno
        if citas_sin_turno:
            sin_turno_style = ParagraphStyle(
                'SinTurnoStyle',
                parent=styles['Heading3'],
                fontSize=12,
                alignment=TA_LEFT,
                spaceBefore=8*mm,
                spaceAfter=4*mm,
                textColor=colors.HexColor('#6b7280'),
                fontName='Helvetica-Bold'
            )
            elements.append(Paragraph(f"📋 SIN TURNO ASIGNADO — {len(citas_sin_turno)} citas", sin_turno_style))
            tabla_sin_turno = crear_tabla_citas(citas_sin_turno, colors.HexColor('#6b7280'))
            if tabla_sin_turno:
                elements.append(tabla_sin_turno)
                
        # Mensaje vacío
        if not citas_manana and not citas_tarde and not citas_sin_turno:
            no_data_style = ParagraphStyle(
                'NoDataStyle',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#718096'),
                spaceBefore=20*mm
            )
            elements.append(Paragraph("No hay citas confirmadas para esta fecha y área.", no_data_style))
        
        # Espacio final
        elements.append(Spacer(1, 10*mm))
        
        # Footer
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        elements.append(Paragraph(f"Documento generado el {fecha_generacion}", footer_style))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generar_pdf_reporte_estadisticas(
        fecha_inicio: str,
        fecha_fin: str,
        area_nombre: str,
        stats: dict,
        citas_por_especialidad: list,
        citas_detalle: list
    ) -> BytesIO:
        """
        Genera un PDF con el reporte de estadísticas de citas.
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReporteTitle', parent=styles['Heading1'],
            fontSize=16, alignment=TA_CENTER,
            spaceAfter=4*mm, textColor=colors.HexColor('#1a365d'),
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'ReporteSubtitle', parent=styles['Heading2'],
            fontSize=12, alignment=TA_CENTER,
            spaceAfter=6*mm, textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica'
        )
        section_style = ParagraphStyle(
            'ReporteSection', parent=styles['Heading3'],
            fontSize=11, alignment=TA_LEFT,
            spaceBefore=6*mm, spaceAfter=3*mm,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'ReporteInfo', parent=styles['Normal'],
            fontSize=9, alignment=TA_CENTER,
            spaceAfter=6*mm, textColor=colors.HexColor('#4a5568')
        )
        footer_style = ParagraphStyle(
            'ReporteFooter', parent=styles['Normal'],
            fontSize=8, alignment=TA_CENTER,
            textColor=colors.HexColor('#718096')
        )

        elements = []

        # Encabezado
        elements.append(Paragraph("CENTRO DE SALUD LA UNIÓN", title_style))
        elements.append(Paragraph("Reporte de Estadísticas de Citas Médicas", subtitle_style))

        # Período
        try:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").strftime("%d/%m/%Y")
            period_text = f"<b>Período:</b> {fi} — {ff}"
        except Exception:
            period_text = f"<b>Período:</b> {fecha_inicio} — {fecha_fin}"

        if area_nombre:
            period_text += f"  |  <b>Especialidad:</b> {area_nombre}"

        elements.append(Paragraph(period_text, info_style))

        # Tabla de resumen KPI
        elements.append(Paragraph("Resumen General", section_style))

        kpi_data = [
            ['Indicador', 'Valor'],
            ['Total de Citas', str(stats.get('totalCitas', 0))],
            ['Tasa de Asistencia', f"{stats.get('tasaAsistencia', 0)}%"],
            ['Cancelaciones', str(stats.get('cancelaciones', 0))],
        ]

        kpi_table = Table(kpi_data, colWidths=[10*cm, 6*cm])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(kpi_table)

        # Tabla de citas por especialidad
        if citas_por_especialidad:
            elements.append(Paragraph("Distribución por Especialidad", section_style))

            esp_data = [['Especialidad', 'Cantidad', 'Porcentaje']]
            for esp in citas_por_especialidad:
                esp_data.append([
                    esp.get('nombre', ''),
                    str(esp.get('cantidad', 0)),
                    f"{esp.get('porcentaje', 0)}%"
                ])

            esp_table = Table(esp_data, colWidths=[9*cm, 4*cm, 4*cm])
            esp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(esp_table)

        # Tabla de detalle de citas
        if citas_detalle:
            elements.append(Paragraph("Detalle de Citas", section_style))

            det_data = [['Fecha', 'Paciente', 'Especialidad', 'Estado']]
            for cita in citas_detalle:
                det_data.append([
                    cita.get('fecha', ''),
                    cita.get('paciente', ''),
                    cita.get('especialidad', ''),
                    cita.get('estado', '').capitalize()
                ])

            det_table = Table(det_data, colWidths=[3*cm, 6*cm, 4.5*cm, 3.5*cm])
            det_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (2, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(det_table)

        # Footer
        elements.append(Spacer(1, 8*mm))
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        elements.append(Paragraph(f"Documento generado el {fecha_generacion}", footer_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_nombre_archivo(fecha: str, area_nombre: str, medico_nombre: str = None) -> str:
        """
        Genera un nombre de archivo descriptivo.
        Si hay médico, lo incluye en el nombre.
        """
        area_limpia = area_nombre.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        
        nombre = f"citas_{area_limpia}_{fecha}"
        
        if medico_nombre:
            medico_limpio = medico_nombre.split()[0].lower() # Primer nombre/apellido
            nombre += f"_{medico_limpio}"
            
        return nombre
