from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import csv
from datetime import datetime, date
from decimal import Decimal

@login_required(login_url='/login/')
def finanza_view(request):
    """Vista principal del dashboard de finanzas"""
    return render(request, 'finanza/finanza.html', {
    
    })

@login_required
def exportar_reporte_pdf(request):
    """
    Exporta el reporte financiero a PDF
    """
    # Crear la respuesta HTTP con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_financiero_{date.today()}.pdf"'
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C0140'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4A008B'),
        spaceAfter=12,
    )
    
    # Título principal
    elements.append(Paragraph("FOCAL - Reporte Financiero", title_style))
    elements.append(Paragraph(f"Fecha: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Usuario: {request.user.nombres} {request.user.apellidos}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # === SECCIÓN: ESTADO DE RESULTADOS ===
    elements.append(Paragraph("Estado de Resultados - Septiembre 2025", heading_style))
    
    # Datos de ejemplo (deberías reemplazarlos con datos reales de tu BD)
    data_resultados = [
        ['Concepto', 'Monto (CLP)'],
        ['INGRESOS', ''],
        ['  Ventas', '$3,500,000'],
        ['  Consultoría', '$2,000,000'],
        ['  Otros', '$700,000'],
        ['Total Ingresos', '$6,200,000'],
        ['', ''],
        ['GASTOS', ''],
        ['  Sueldos', '$3,200,000'],
        ['  Marketing', '$450,000'],
        ['  Oficina', '$650,000'],
        ['Total Gastos', '$4,300,000'],
        ['', ''],
        ['RESULTADO NETO', '$1,900,000'],
    ]
    
    # Crear tabla
    table = Table(data_resultados, colWidths=[4*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A008B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (-1, 12), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#0AE8C6')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # === SECCIÓN: KPIs ===
    elements.append(Paragraph("Indicadores Clave (KPIs)", heading_style))
    
    data_kpis = [
        ['Indicador', 'Valor'],
        ['Saldo Actual', '$8,500,000'],
        ['Ingresos del Mes', '$6,200,000'],
        ['Gastos del Mes', '$4,300,000'],
        ['Resultado', '$1,900,000'],
        ['Margen de Utilidad', '30.6%'],
    ]
    
    table_kpis = Table(data_kpis, colWidths=[3*inch, 2*inch])
    table_kpis.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1FA2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3E8FF')),
    ]))
    
    elements.append(table_kpis)
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Documento generado automáticamente por FOCAL", styles['Normal']))
    
    # Construir PDF
    doc.build(elements)
    return response

@login_required
def exportar_reporte_csv(request):
    """
    Exporta el reporte financiero a CSV
    """
    # Crear la respuesta HTTP con el tipo de contenido CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_financiero_{date.today()}.csv"'
    
    # Configurar el escritor CSV
    writer = csv.writer(response)
    
    # Encabezado del reporte
    writer.writerow(['FOCAL - Reporte Financiero'])
    writer.writerow([f'Fecha: {date.today().strftime("%d/%m/%Y")}'])
    writer.writerow([f'Usuario: {request.user.nombres} {request.user.apellidos}'])
    writer.writerow([])
    
    # === ESTADO DE RESULTADOS ===
    writer.writerow(['ESTADO DE RESULTADOS - SEPTIEMBRE 2025'])
    writer.writerow(['Concepto', 'Monto (CLP)'])
    writer.writerow(['INGRESOS', ''])
    writer.writerow(['  Ventas', '3500000'])
    writer.writerow(['  Consultoría', '2000000'])
    writer.writerow(['  Otros', '700000'])
    writer.writerow(['Total Ingresos', '6200000'])
    writer.writerow([])
    writer.writerow(['GASTOS', ''])
    writer.writerow(['  Sueldos', '3200000'])
    writer.writerow(['  Marketing', '450000'])
    writer.writerow(['  Oficina', '650000'])
    writer.writerow(['Total Gastos', '4300000'])
    writer.writerow([])
    writer.writerow(['RESULTADO NETO', '1900000'])
    writer.writerow([])
    
    # === KPIs ===
    writer.writerow(['INDICADORES CLAVE (KPIs)'])
    writer.writerow(['Indicador', 'Valor'])
    writer.writerow(['Saldo Actual', '8500000'])
    writer.writerow(['Ingresos del Mes', '6200000'])
    writer.writerow(['Gastos del Mes', '4300000'])
    writer.writerow(['Resultado', '1900000'])
    writer.writerow(['Margen de Utilidad', '30.6%'])
    
    return response