import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Image as PlatypusImage, Paragraph
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from constants import PANDA_STORE_INFO

# Colores estilo "Refrens" (Azules corporativos y grises limpios)
COLOR_PRIMARY = colors.HexColor("#2C3E50") # Azul oscuro para títulos grandes
COLOR_ACCENT = colors.HexColor("#3498DB")  # Azul claro para encabezados de sección
COLOR_BG_HEADER = colors.HexColor("#F4F6F7") # Gris muy suave para fondos
COLOR_TEXT_GRAY = colors.HexColor("#555555")

def generate_pdf_file(invoice_data, filename, logo_bytes=None):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # Estilos de texto
    style_desc = ParagraphStyle('Desc', parent=styles['Normal'], fontSize=9, leading=11)
    
    # --- 1. Encabezado y Logo ---
    # El logo se dibuja si main.py lo envía (ahora lo enviará siempre si existe logo.jpeg)
    if logo_bytes:
        try:
            logo_stream = io.BytesIO(logo_bytes)
            logo_img = ImageReader(logo_stream)
            # Ajustamos posición y tamaño del logo
            c.drawImage(logo_img, 40, height - 100, width=100, height=80, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error dibujando logo: {e}")
            
    # Bloque de "FACTURA" a la derecha
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(COLOR_PRIMARY)
    c.drawRightString(width - 40, height - 60, "FACTURA")
    
    # Caja gris suave para Número y Fecha
    c.setFillColor(COLOR_BG_HEADER)
    c.roundRect(width - 220, height - 115, 180, 45, 6, fill=1, stroke=0)
    
    # Textos dentro de la caja
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 210, height - 90, "No. Factura:")
    c.drawRightString(width - 50, height - 90, f"#{invoice_data['number']}")
    
    c.drawString(width - 210, height - 105, "Fecha:")
    c.drawRightString(width - 50, height - 105, invoice_data['date'])

    # --- 2. Bloques de Información (Facturado Por / A) ---
    y_billing = height - 160
    
    # -- Columna Izquierda: FACTURADO POR --
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_ACCENT)
    c.drawString(40, y_billing, "FACTURADO POR")
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(40, y_billing - 20, PANDA_STORE_INFO["name"])
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_GRAY)
    y_offset = y_billing - 35
    for line in PANDA_STORE_INFO["address"]:
        c.drawString(40, y_offset, line)
        y_offset -= 12
    c.drawString(40, y_offset, f"Correo: {PANDA_STORE_INFO['email']}")
    c.drawString(40, y_offset - 12, f"Tel: {PANDA_STORE_INFO['phone']}")
    
    # -- Columna Derecha: FACTURADO A --
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_ACCENT)
    c.drawString(width/2 + 20, y_billing, "FACTURADO A")
    
    client = invoice_data['client']
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(width/2 + 20, y_billing - 20, client.get('fullName', 'Cliente General'))
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_GRAY)
    
    # Dirección con recorte si es muy larga
    addr = client.get('address', '')
    if len(addr) > 55:
        c.drawString(width/2 + 20, y_billing - 35, addr[:55] + "...")
    else:
        c.drawString(width/2 + 20, y_billing - 35, addr)
        
    c.drawString(width/2 + 20, y_billing - 50, f"Tel: {client.get('phone', '')}")
    if client.get('transportProvider'):
        c.drawString(width/2 + 20, y_billing - 65, f"Transporte: {client.get('transportProvider')}")

    # --- 3. Tabla de Items ---
    headers = ['Artículo', 'Cant.', 'Precio Unit.', 'Dólares', 'Total']
    table_data = [headers]
    
    total_amount = 0
    
    for item in invoice_data['items']:
        sub = item['priceCordobas'] * item['quantity']
        total_amount += sub
        
        # Descripción + Imagen
        desc_paragraph = Paragraph(f"{item['product']['description']}", style_desc)
        cell_content = [desc_paragraph]
        
        # Imagen del producto (si existe)
        if item.get('custom_image_data'):
            try:
                img_stream = io.BytesIO(item['custom_image_data'])
                img = PlatypusImage(img_stream)
                max_height = 35 
                aspect = img.imageWidth / img.imageHeight
                img.drawHeight = max_height
                img.drawWidth = max_height * aspect
                cell_content.append(img)
            except:
                pass
        
        table_data.append([
            cell_content,
            str(item['quantity']),
            f"C$ {item['priceCordobas']:,.2f}",
            f"$ {item['priceDollars']:,.2f}",
            f"C$ {sub:,.2f}"
        ])

    # Anchos de columna
    col_widths = [220, 40, 80, 70, 90]
    table = Table(table_data, colWidths=col_widths)
    
    # Estilo Visual de la Tabla
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),       # Encabezado Azul Oscuro
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),         # Texto Blanco
        ('ALIGN', (0,0), (-1,0), 'CENTER'),                 # Centrado
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),                # Cantidad y Precios centrados
        ('ALIGN', (0,1), (0,-1), 'LEFT'),                   # Descripción a la izquierda
        ('VALIGN', (0,0), (-1,-1), 'TOP'),                  # Todo alineado arriba
        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ])
    table.setStyle(style)
    
    table.wrapOn(c, width, height)
    table_height = table._height
    y_table = y_billing - 100 - table_height
    table.drawOn(c, 40, y_table)

    # --- 4. Totales ---
    y_totals = y_table - 20
    
    final_shipping = invoice_data['shippingCost']
    final_discount = invoice_data['discount']
    grand_total = total_amount + final_shipping - final_discount
    
    x_labels = width - 200
    x_values = width - 40
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    
    # Monto
    c.drawRightString(x_labels, y_totals, "Monto:")
    c.drawRightString(x_values, y_totals, f"C$ {total_amount:,.2f}")
    
    # Envío
    if final_shipping > 0:
        y_totals -= 20
        c.drawRightString(x_labels, y_totals, "Delivery:")
        c.drawRightString(x_values, y_totals, f"C$ {final_shipping:,.2f}")
    
    # Descuentos
    if final_discount > 0:
        y_totals -= 20
        c.setFillColor(colors.red)
        c.drawRightString(x_labels, y_totals, "Descuentos:")
        c.drawRightString(x_values, y_totals, f"- C$ {final_discount:,.2f}")
        c.setFillColor(colors.black)
    
    # Línea y Total Final
    y_totals -= 10
    c.setStrokeColor(colors.black)
    c.line(x_labels - 20, y_totals, width - 40, y_totals)
    
    y_totals -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(x_labels, y_totals, "Total (C$):")
    c.drawRightString(x_values, y_totals, f"C$ {grand_total:,.2f}")

    # Nota
    if invoice_data['note']:
        y_note = y_table - 30
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.darkgrey)
        c.drawString(40, y_note, "Nota:")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(40, y_note - 15, invoice_data['note'])

    # --- 5. Footer (Legal) ---
    footer_y = 150 
    
    # Pago
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT)
    c.drawString(40, footer_y, "Pago")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_GRAY)
    c.drawString(40, footer_y - 15, "1. El pago debe realizarse en su totalidad en el momento de la compra, a menos que se haya")
    c.drawString(50, footer_y - 25, " acordado un plazo de crédito por escrito.")
    c.drawString(40, footer_y - 40, "2. Los métodos de pago aceptados son transferencia bancaria y pago en efectivo.")

    # Garantía
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT)
    c.drawString(40, footer_y - 70, "Garantía")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_GRAY)
    c.drawString(40, footer_y - 85, "1. Los productos vendidos por Panda Store tienen una garantía de 3 meses a partir de la fecha de compra.")
    c.drawString(40, footer_y - 100, "2. La garantía cubre defectos de fabricación y no incluye daños causados por mal uso o accidentes.")
    
    # Powered By
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 40, "Powered By Refrens.com")
    c.drawCentredString(width/2, 28, "This is an electronically generated document, no signature is required.")

    c.save()