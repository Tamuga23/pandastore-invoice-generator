import io  # <--- IMPORTANTE: Necesario para leer imágenes desde memoria
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Image as PlatypusImage, Paragraph
from reportlab.lib.utils import ImageReader
from constants import PANDA_STORE_INFO

def generate_pdf_file(invoice_data, filename, logo_bytes=None):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # --- 1. Header y Logo ---
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.1, 0.42, 0.63)
    c.drawString(50, height - 50, "Factura")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(50, height - 80, f"Factura No #: {invoice_data['number']}")
    c.drawString(50, height - 95, f"Fecha: {invoice_data['date']}")

    # --- CORRECCIÓN LOGO ---
    if logo_bytes:
        try:
            # Convertimos los bytes crudos en un 'archivo en memoria'
            logo_stream = io.BytesIO(logo_bytes)
            logo_img = ImageReader(logo_stream)
            
            # Dibujamos el logo (ajustamos posición y tamaño)
            c.drawImage(logo_img, width - 170, height - 110, width=120, height=80, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error dibujando logo: {e}")

    # --- 2. Bloques de Información ---
    # Caja Izquierda (PandaStore)
    c.setFillColorRGB(0.87, 0.95, 0.98)
    c.rect(50, height - 230, 240, 110, fill=1, stroke=0)
    
    c.setFillColorRGB(0.1, 0.42, 0.63)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, height - 140, "Facturado Por:")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, height - 160, PANDA_STORE_INFO["name"])
    c.setFont("Helvetica", 9)
    y_offset = 175
    for line in PANDA_STORE_INFO["address"]:
        c.drawString(60, height - y_offset, line)
        y_offset += 12
    c.drawString(60, height - y_offset - 5, f"Tel: {PANDA_STORE_INFO['phone']}")

    # Caja Derecha (Cliente)
    c.setFillColorRGB(0.87, 0.95, 0.98)
    c.rect(300, height - 230, 240, 110, fill=1, stroke=0)
    
    c.setFillColorRGB(0.1, 0.42, 0.63)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(310, height - 140, "Facturado a:")
    
    client = invoice_data['client']
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(310, height - 160, client.get('fullName', 'Unknown'))
    c.setFont("Helvetica", 9)
    
    # Dirección con recorte simple si es muy larga
    addr = client.get('address', '')
    if len(addr) > 45:
        c.drawString(310, height - 175, f"Dir: {addr[:45]}...")
    else:
        c.drawString(310, height - 175, f"Dir: {addr}")
        
    c.drawString(310, height - 190, f"Tel: {client.get('phone', '')}")
    c.drawString(310, height - 210, f"Transporte: {client.get('transportProvider', '')}")

    # --- 3. Tabla de Items con Imágenes ---
    # Encabezados
    table_data = [['Artículo', 'Cant', 'Monto', 'Dólares', 'Total']]
    
    total_amount = 0
    
    for item in invoice_data['items']:
        sub = item['priceCordobas'] * item['quantity']
        total_amount += sub
        
        # Descripción
        desc_paragraph = Paragraph(f"<b>{item['product']['description']}</b>", styles['Normal'])
        cell_content = [desc_paragraph]
        
        # --- CORRECCIÓN IMAGEN PRODUCTO ---
        if item.get('custom_image_data'):
            try:
                # Convertimos los bytes en stream
                img_stream = io.BytesIO(item['custom_image_data'])
                
                # Creamos la imagen para la tabla
                img = PlatypusImage(img_stream)
                
                # Lógica para mantener proporción de aspecto (máximo 50px alto)
                max_height = 50
                aspect = img.imageWidth / img.imageHeight
                img.drawHeight = max_height
                img.drawWidth = max_height * aspect
                
                cell_content.append(img)
            except Exception as e:
                print(f"Error imagen item: {e}")
        
        table_data.append([
            cell_content, 
            str(item['quantity']),
            f"C$ {item['priceCordobas']:.2f}",
            f"$ {item['priceDollars']:.2f}",
            f"C$ {sub:.2f}"
        ])

    # Estilo de tabla
    table = Table(table_data, colWidths=[240, 40, 70, 70, 70])
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0e5c7a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'), 
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])
    table.setStyle(style)
    
    table.wrapOn(c, width, height)
    table_height = table._height
    y_position = height - 260 - table_height
    table.drawOn(c, 50, y_position)

    # --- 4. Totales ---
    y_totals = y_position - 20
    
    final_total = total_amount + invoice_data['shippingCost'] - invoice_data['discount']
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawRightString(540, y_totals - 20, f"Subtotal: C$ {total_amount:.2f}")
    c.drawRightString(540, y_totals - 35, f"Envío: C$ {invoice_data['shippingCost']:.2f}")
    c.drawRightString(540, y_totals - 50, f"Descuento: C$ {invoice_data['discount']:.2f}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(540, y_totals - 70, f"TOTAL: C$ {final_total:.2f}")

    if invoice_data['note']:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, y_totals - 50, f"Nota: {invoice_data['note']}")

    # --- 5. Footer (Términos y Condiciones) ---
    # Footer estático al final de la hoja
    footer_y = 180 
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.1, 0.42, 0.63)
    c.drawString(50, footer_y, "Pago")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(65, footer_y - 15, "1. El pago debe realizarse en su totalidad en el momento de la compra, a menos que se haya")
    c.drawString(65, footer_y - 25, "   acordado un plazo de crédito por escrito.")
    c.drawString(65, footer_y - 40, "2. Los métodos de pago aceptados son transferencia bancaria y pago en efectivo.")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.1, 0.42, 0.63)
    c.drawString(50, footer_y - 70, "Garantía")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(65, footer_y - 85, "1. Los productos vendidos por Panda Store tienen una garantía de [3] meses a partir de la fecha de compra.")
    c.drawString(65, footer_y - 100, "2. La garantía cubre defectos de fabricación y no incluye daños causados por mal uso o accidentes.")
    
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 40, "Powered By Refrens.com")
    c.drawCentredString(width/2, 30, "This is an electronically generated document, no signature is required.")

    c.save()