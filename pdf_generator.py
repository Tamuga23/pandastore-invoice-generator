import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Image as PlatypusImage, Paragraph
from reportlab.lib.utils import ImageReader
from constants import PANDA_STORE_INFO

# --- COLORES DEL DISEÑO ---
COLOR_PRIMARY = colors.HexColor("#005b82")     # Azul Oscuro
COLOR_ACCENT_TEXT = colors.HexColor("#176B87") # Azul Petróleo
COLOR_BG_BLOCK = colors.HexColor("#eef6f9")    # Fondo Azul muy pálido
COLOR_TEXT = colors.HexColor("#333333")        # Gris oscuro
COLOR_GRAY_LIGHT = colors.HexColor("#dddddd")  # Líneas sutiles
COLOR_BORDER_BOX = colors.HexColor("#cccccc")  # Gris claro para bordes

def generate_pdf_file(invoice_data, filename, logo_bytes=None):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # --- SISTEMA DE GRILLA (ALINEACIÓN PERFECTA) ---
    MARGIN = 40                          # Margen izquierdo y derecho
    CONTENT_WIDTH = width - (MARGIN * 2) # Ancho útil de la página (515.27 pts)
    GAP = 20                             # Espacio entre columnas
    HALF_WIDTH = (CONTENT_WIDTH - GAP) / 2 # Ancho exacto de cada bloque azul (247.6 pts)

    # Estilos
    style_desc = ParagraphStyle('Desc', parent=styles['Normal'], fontSize=9, leading=11, textColor=COLOR_TEXT)
    style_block = ParagraphStyle('Block', parent=styles['Normal'], fontSize=9, leading=11, textColor=COLOR_TEXT)

    # ==========================================
    # 1. ENCABEZADO
    # ==========================================
    # Título alineado estrictamente a la IZQUIERDA (MARGIN)
    c.setFont("Helvetica", 28)
    c.setFillColor(COLOR_PRIMARY)
    c.drawString(MARGIN, height - 50, "Factura")
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(MARGIN, height - 80, "Factura No #")
    c.drawString(MARGIN, height - 95, "Fecha:")
    
    c.setFont("Helvetica", 10)
    # Alineamos los valores un poco más a la derecha pero consistentes
    c.drawString(MARGIN + 80, height - 80, f"{invoice_data['number']}")
    c.drawString(MARGIN + 80, height - 95, f"{invoice_data['date']}")

    # Logo alineado estrictamente a la DERECHA (width - MARGIN)
    if logo_bytes:
        try:
            logo_stream = io.BytesIO(logo_bytes)
            logo_img = ImageReader(logo_stream)
            logo_width = 120
            logo_height = 80
            # Posición X = Ancho total - Margen - Ancho del logo
            logo_x = width - MARGIN - logo_width
            c.drawImage(logo_img, logo_x, height - 100, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error dibujando logo: {e}")

    # ==========================================
    # 2. BLOQUES DE INFORMACIÓN (ALINEADOS)
    # ==========================================
    y_blocks = height - 130
    block_height = 145
    
    # --- Bloque Izquierdo ---
    # X = MARGIN
    # Ancho = HALF_WIDTH
    c.setFillColor(COLOR_BG_BLOCK)
    c.rect(MARGIN, y_blocks - block_height, HALF_WIDTH, block_height, fill=1, stroke=0)
    
    text_x_left = MARGIN + 10 # Padding interno de 10px
    current_y = y_blocks - 20 
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT_TEXT)
    c.drawString(text_x_left, current_y, "Facturado Por:")
    current_y -= 20 
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(text_x_left, current_y, PANDA_STORE_INFO["name"])
    current_y -= 15 
    
    c.setFont("Helvetica", 9) 
    c.setFillColor(COLOR_TEXT)
    for line in PANDA_STORE_INFO["address"]:
        c.drawString(text_x_left, current_y, line)
        current_y -= 12
    c.drawString(text_x_left, current_y, f"Correo: {PANDA_STORE_INFO['email']}")
    current_y -= 12
    c.drawString(text_x_left, current_y, f"Telefono: {PANDA_STORE_INFO['phone']}")

    # --- Bloque Derecho ---
    # X = MARGIN + HALF_WIDTH + GAP
    # El borde derecho caerá exactamente en (width - MARGIN)
    right_block_x = MARGIN + HALF_WIDTH + GAP
    
    c.setFillColor(COLOR_BG_BLOCK)
    c.rect(right_block_x, y_blocks - block_height, HALF_WIDTH, block_height, fill=1, stroke=0)
    
    text_x_right = right_block_x + 10
    current_y_right = y_blocks - 20
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT_TEXT)
    c.drawString(text_x_right, current_y_right, "Facturado a:")
    current_y_right -= 20
    
    client = invoice_data['client']
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(text_x_right, current_y_right, client.get('fullName', 'Cliente General').upper())
    current_y_right -= 15
    
    # Dirección
    addr = client.get('address', '')
    p_addr = Paragraph(f"Dirección: {addr}", style_block)
    # Ancho disponible dentro del bloque = HALF_WIDTH - 20 (padding)
    w_addr, h_addr = p_addr.wrap(HALF_WIDTH - 20, 1000)
    p_addr.drawOn(c, text_x_right, current_y_right - h_addr + 2)
    current_y_right -= (h_addr + 8) 
    
    # Teléfono
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT)
    c.drawString(text_x_right, current_y_right, f"{client.get('phone', '')}")
    current_y_right -= 20 
    
    # Transporte
    if client.get('transportProvider'):
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(COLOR_TEXT)
        c.drawString(text_x_right, current_y_right, "Proveedor de Transporte:")
        
        # Cajita blanca con borde gris claro
        c.setFillColor(colors.white)
        c.setStrokeColor(COLOR_BORDER_BOX)
        c.setLineWidth(1)
        c.roundRect(text_x_right + 115, current_y_right - 2, 80, 13, 3, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawCentredString(text_x_right + 155, current_y_right + 1, client.get('transportProvider'))

    # ==========================================
    # 3. TABLA DE PRODUCTOS (ALINEACIÓN EXACTA)
    # ==========================================
    headers = ['Artículo', 'Cantidad', 'Monto', 'Dolares', 'Total']
    table_data = [headers]
    
    total_amount = 0
    
    for item in invoice_data['items']:
        sub = item['priceCordobas'] * item['quantity']
        total_amount += sub
        
        desc_paragraph = Paragraph(f"<b>{item['product']['description']}</b>", style_desc)
        cell_content = [desc_paragraph]
        
        if item.get('custom_image_data'):
            try:
                img_stream = io.BytesIO(item['custom_image_data'])
                img = PlatypusImage(img_stream)
                max_height = 45
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

    # DEFINICIÓN DE ANCHOS DE COLUMNA PARA QUE SUMEN EXACTAMENTE 'CONTENT_WIDTH'
    # CONTENT_WIDTH es aprox 515 pts.
    # 225 + 50 + 80 + 70 + 90 = 515. ¡Exacto!
    col_widths = [225, 50, 80, 70, 90] # Ajustado para cuadrar con los márgenes
    
    table = Table(table_data, colWidths=col_widths)
    
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('LEFTPADDING', (0,0), (-1,0), 10),
        
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,1), (-1,-1), COLOR_TEXT),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, COLOR_GRAY_LIGHT),
    ])
    table.setStyle(style)
    
    table.wrapOn(c, width, height)
    table_height = table._height
    y_table = y_blocks - block_height - 40 - table_height
    
    # Dibujamos la tabla en MARGIN (40), alineada con los bloques
    table.drawOn(c, MARGIN, y_table)

    # ==========================================
    # 4. NOTAS Y TOTALES
    # ==========================================
    y_section = y_table - 20
    
    # --- Nota (Alineada a la Izquierda - MARGIN) ---
    if invoice_data['note']:
        note_content = invoice_data['note'].replace('\n', '<br/>')
        p_note = Paragraph(note_content, style_desc)
        
        # Ancho de la caja de notas = HALF_WIDTH (mitad de la página, alineado al bloque izq)
        note_box_width = HALF_WIDTH
        w, h_text = p_note.wrap(note_box_width - 20, 1000)
        
        box_height = h_text + 25 
        if box_height < 60: box_height = 60 
        
        c.setFillColor(colors.HexColor("#f9f9f9"))
        c.setStrokeColor(colors.transparent)
        box_y_start = y_section - box_height
        
        # Dibujar en MARGIN
        c.rect(MARGIN, box_y_start, note_box_width, box_height, fill=1, stroke=0)
        
        c.setFillColor(colors.darkgrey)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN + 10, box_y_start + box_height - 12, "Nota")
        
        p_note.drawOn(c, MARGIN + 10, box_y_start + 8)

    # --- Totales (Alineados a la Derecha - width - MARGIN) ---
    final_shipping = invoice_data['shippingCost']
    final_discount = invoice_data['discount']
    grand_total = total_amount + final_shipping - final_discount
    
    # Coordenadas alineadas a la derecha
    x_val = width - MARGIN      # Borde derecho exacto
    x_lbl = width - MARGIN - 100 # Etiquetas 100pts a la izquierda
    current_y_total = y_section - 10
    
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    
    c.drawRightString(x_lbl, current_y_total, "Monto")
    c.drawRightString(x_val, current_y_total, f"C$ {total_amount:,.2f}")
    current_y_total -= 18
    
    c.drawRightString(x_lbl, current_y_total, "Delivery")
    c.drawRightString(x_val, current_y_total, f"C$ {final_shipping:,.2f}")
    current_y_total -= 18
    
    c.setFillColor(colors.red)
    c.drawRightString(x_lbl, current_y_total, "Descuentos")
    c.drawRightString(x_val, current_y_total, f"C$ {final_discount:,.2f}")
    current_y_total -= 25
    
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    # Línea de total alineada
    c.line(x_lbl - 20, current_y_total + 15, x_val, current_y_total + 15)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(x_lbl, current_y_total, "Total (C$)")
    c.drawRightString(x_val, current_y_total, f"C$ {grand_total:,.2f}")

    # ==========================================
    # 5. FOOTER (Alineado a MARGIN)
    # ==========================================
    footer_y = 160
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT_TEXT)
    c.drawString(MARGIN, footer_y, "Pago")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT)
    c.drawString(MARGIN, footer_y - 15, "1. El pago debe realizarse en su totalidad en el momento de la compra, a menos que se haya acordado un plazo de crédito por escrito.")
    c.drawString(MARGIN, footer_y - 28, "2. Los métodos de pago aceptados son transferencia bancaria, efectivo y pago mediante Tarjeta de Credito/Debito")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_ACCENT_TEXT)
    c.drawString(MARGIN, footer_y - 55, "Garantía")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT)
    c.drawString(MARGIN, footer_y - 70, "1. Los productos vendidos por Panda Store tienen una garantía de [3] meses a partir de la fecha de compra.")
    c.drawString(MARGIN, footer_y - 83, "2. La garantía cubre defectos de fabricación y no incluye daños causados por mal uso o accidentes.")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#8E44AD"))
    c.drawCentredString(width/2, 40, "Powered By Refrens.com")
    
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 28, "This is an electronically generated document, no signature is required.")

    c.save()