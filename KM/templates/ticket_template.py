from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from datetime import datetime
import os
from config import TICKETS_DIR

def format_number(num):
    """Formatea un número al estilo español: 12.000 o 12.000,50"""
    if isinstance(num, str):
        try:
            num = float(num)
        except:
            return num
    integer_part = int(num)
    decimal_part = int(round((num - integer_part) * 100))
    integer_str = f"{integer_part:,}".replace(',', '.')
    if decimal_part == 0:
        return integer_str
    else:
        return f"{integer_str},{decimal_part:02d}"

def generate_ticket_pdf(ticket_data):
    """Genera un PDF con los datos del ticket para impresora térmica"""
    # Configurar tamaño de página (80mm de ancho estándar para impresoras térmicas)
    width = int(ticket_data["ancho"]) * mm
    height = 450 * mm  # Aumentamos la altura para el QR
    
    # Crear nombre de archivo
    filename = f"ticket_{ticket_data['numero']}.pdf"
    filepath = str(TICKETS_DIR / filename)
    
    # Crear directorio si no existe
    os.makedirs(TICKETS_DIR, exist_ok=True)
    
    # Crear PDF (modo blanco y negro)
    c = canvas.Canvas(filepath, pagesize=(width, height))
    
    # Configurar márgenes
    margin_left = 3 * mm
    margin_right = 3 * mm
    y_position = height - 10 * mm
    
    # --- ENCABEZADO ---
    company = ticket_data["empresa"]
    estado = str(ticket_data.get("estado", "ACTIVA")).upper()
    
    # Nombre de la empresa (negrita y grande)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y_position, company["nombre"].upper())
    y_position -= 6 * mm

    if estado == "ANULADA":
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, y_position, "***** ANULADA *****")
        y_position -= 6 * mm
    
    # Dirección de la empresa
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y_position, company.get("direccion", ""))
    y_position -= 5 * mm
    
    # Información fiscal en una sola línea (NIT + Régimen)
    c.setFont("Helvetica", 8)
    info_line = f"NIT: {company.get('nit', '')} | Régimen Simple"
    c.drawCentredString(width / 2, y_position, info_line)
    y_position -= 5 * mm
    
    # Contacto y ubicación en una sola línea
    contacto_line = f"Tel: {company['telefono']} | {company.get('departamento', '')} - {company.get('municipio', '')}"
    c.drawCentredString(width / 2, y_position, contacto_line)
    y_position -= 8 * mm
    
    # Línea divisoria gruesa
    c.setLineWidth(0.5)
    c.line(margin_left, y_position, width - margin_right, y_position)
    y_position -= 8 * mm
    
    # --- INFORMACIÓN DEL TICKET ---
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_left, y_position, "FACTURA DE VENTA Nº:")
    c.setFont("Helvetica", 9)
    c.drawString(margin_left + 40 * mm, y_position, ticket_data["numero"])
    y_position -= 5 * mm
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_left, y_position, "FECHA/HORA:")
    c.setFont("Helvetica", 9)
    c.drawString(margin_left + 25 * mm, y_position, f"{ticket_data['fecha']} {ticket_data['hora']}")
    y_position -= 5 * mm
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_left, y_position, "CAJERO:")
    c.setFont("Helvetica", 9)
    c.drawString(margin_left + 25 * mm, y_position, ticket_data.get("cajero", "ADMIN"))
    y_position -= 8 * mm
    
    # --- INFORMACIÓN DEL CLIENTE ---
    cliente = ticket_data.get("cliente") or {}

    def draw_label_value(label, value):
        nonlocal y_position
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin_left, y_position, label)
        c.setFont("Helvetica", 9)
        c.drawString(margin_left + 25 * mm, y_position, value)
        y_position -= 5 * mm

    draw_label_value("CLIENTE:", cliente.get("nombre", ""))
    if cliente.get("nit"):
        draw_label_value("NIT/CC:", cliente["nit"])
    if cliente.get("telefono"):
        draw_label_value("TEL:", cliente["telefono"])
    if cliente.get("correo"):
        draw_label_value("CORREO:", cliente["correo"])
    if cliente.get("departamento") or cliente.get("municipio"):
        ubicacion_cli = f"{cliente.get('departamento', '')} - {cliente.get('municipio', '')}"
        draw_label_value("DIRECCIÓN:", ubicacion_cli)

    # Línea divisoria
    c.line(margin_left, y_position, width - margin_right, y_position)
    y_position -= 8 * mm
    
    # --- DETALLE DE PRODUCTOS ---
    # Encabezados de columnas
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin_left, y_position, "DESCRIPCION")
    c.drawRightString(width - margin_right - 25 * mm, y_position, "CANT")

    # "VALOR UNITARIO" en 2 líneas para no invadir otras columnas
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(width - margin_right - 15 * mm, y_position, "VALOR")
    c.drawRightString(width - margin_right - 15 * mm, y_position - 3 * mm, "UNITARIO")

    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(width - margin_right, y_position, "TOTAL")
    y_position -= 7 * mm
    
    # Línea divisoria
    c.line(margin_left, y_position, width - margin_right, y_position)
    y_position -= 5 * mm
    
    # Lista de productos
    c.setFont("Helvetica", 8)
    subtotal = 0
    
    for product in ticket_data["productos"]:
        # Ajustar descripción si es muy larga
        desc = (product["nombre"][:25] + "...") if len(product["nombre"]) > 25 else product["nombre"]
        
        total = product["cantidad"] * product["precio"]
        subtotal += total
        
        # Dibujar producto
        c.drawString(margin_left, y_position, desc)
        c.drawRightString(width - margin_right - 25 * mm, y_position, f"{product['cantidad']:.0f}" if product['cantidad'].is_integer() else f"{product['cantidad']:.1f}")
        c.drawRightString(width - margin_right - 15 * mm, y_position, format_number(product['precio']))
        c.drawRightString(width - margin_right, y_position, format_number(total))
        y_position -= 5 * mm
        
        # Verificar si necesitamos nueva página
        if y_position < 100 * mm:  # Más espacio para el QR
            c.showPage()
            y_position = height - 10 * mm
            c.setFont("Helvetica", 8)
    
    # Línea divisoria para totales
    y_position -= 3 * mm
    c.line(margin_left, y_position, width - margin_right, y_position)
    y_position -= 5 * mm
    
    # --- TOTALES ---
    iva_percent = float(company.get('iva', 19))
    iva_value = subtotal * (iva_percent / (100 + iva_percent))  # IVA incluido
    
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - margin_right - 25 * mm, y_position, "SUBTOTAL:")
    c.drawRightString(width - margin_right, y_position, format_number(subtotal))
    y_position -= 5 * mm
    
    c.drawRightString(width - margin_right - 25 * mm, y_position, f"IVA ({iva_percent}% ):")
    c.drawRightString(width - margin_right, y_position, format_number(iva_value))
    y_position -= 5 * mm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - margin_right - 25 * mm, y_position, "TOTAL:")
    c.drawRightString(width - margin_right, y_position, format_number(subtotal))
    y_position -= 7 * mm
    
    # Información de pago
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - margin_right - 25 * mm, y_position, "PAGADO:")
    c.drawRightString(width - margin_right, y_position, format_number(ticket_data['pagado']))
    y_position -= 5 * mm
    
    c.drawRightString(width - margin_right - 25 * mm, y_position, "CAMBIO:")
    c.drawRightString(width - margin_right, y_position, format_number(float(ticket_data['pagado']) - subtotal))
    y_position -= 10 * mm
    
    # --- PIE DEL TICKET ---
    c.line(margin_left, y_position, width - margin_right, y_position)
    y_position -= 8 * mm
    
    # Código QR decorativo
    qr_code = qr.QrCodeWidget(f"TICKET#{ticket_data['numero']}")
    bounds = qr_code.getBounds()
    width_qr = bounds[2] - bounds[0]
    height_qr = bounds[3] - bounds[1]
    d = Drawing(150, 150, transform=[150.0/width_qr,0,0,150.0/height_qr,0,0])
    d.add(qr_code)
    
    # Centrar el QR
    qr_x = (width - 150) / 2
    d.drawOn(c, qr_x, y_position - 150)
    y_position -= 160  # Espacio después del QR
    
    # Mensaje final
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, y_position, "¡GRACIAS POR SU COMPRA!")
    y_position -= 6 * mm
    
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, y_position, "Conserve esta factura como comprobante")
    y_position -= 5 * mm
    c.drawCentredString(width / 2, y_position, "")
    
    # Guardar PDF
    c.save()
    
    return filepath
