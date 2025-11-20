import streamlit as st
import datetime
import os  
from constants import PRODUCT_CATALOG, DEFAULT_EXCHANGE_RATE
from gemini_service import parse_client_info
from pdf_generator import generate_pdf_file

# --- Configuración de Página ---
st.set_page_config(page_title="PandaStore Facturación", layout="wide")

# --- Constantes ---
# CAMBIO AQUÍ: Ponemos el nombre exacto de tu archivo
LOGO_FILENAME = "logo.jpeg"  

# --- Inicialización de Estado ---
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []
if 'client_data' not in st.session_state:
    st.session_state.client_data = {"fullName": "", "address": "", "phone": "", "transportProvider": ""}
if 'consecutive' not in st.session_state:
    st.session_state.consecutive = "A001197"

# --- Sidebar (Configuración) ---
with st.sidebar:
    st.title("Configuración")
    
    # 1. Gestión de Logo Persistente
    st.subheader("Logotipo")
    
    # Cargar logo desde el disco (Predeterminado)
    logo_bytes = None
    
    # Verificamos si existe el archivo logo.jpeg
    if os.path.exists(LOGO_FILENAME):
        with open(LOGO_FILENAME, "rb") as f:
            logo_bytes = f.read()
        st.image(logo_bytes, width=120, caption="Logo Actual")
    else:
        st.info(f"No se encontró {LOGO_FILENAME} en la carpeta.")

    # Opción para cambiarlo temporalmente (opcional)
    uploaded_logo = st.file_uploader("Cambiar Logo temporalmente", type=['png', 'jpg', 'jpeg'])
    if uploaded_logo is not None:
        logo_bytes = uploaded_logo.getvalue()
        st.image(logo_bytes, width=120, caption="Nuevo Logo")

    st.divider()
    
    st.session_state.consecutive = st.text_input("No. Factura", st.session_state.consecutive)
    invoice_date = st.date_input("Fecha", datetime.date.today())
    
    st.divider()
    st.subheader("IA - Datos del Cliente")
    raw_text = st.text_area("Pegue texto aquí...", height=100)
    
    if st.button("✨ Autocompletar con IA"):
        if raw_text.strip():
            with st.spinner("Analizando..."):
                result = parse_client_info(raw_text)
                if result and "error" not in result:
                    st.session_state.client_data = result
                    st.success("Datos extraídos!")
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error')}")

# --- Área Principal ---
st.title("🧾 Generador de Facturas PandaStore")

# 1. Datos del Cliente
col1, col2 = st.columns(2)
with col1:
    c_name = st.text_input("Nombre Completo", st.session_state.client_data.get('fullName', ''))
    c_addr = st.text_input("Dirección", st.session_state.client_data.get('address', ''))
with col2:
    c_phone = st.text_input("Teléfono", st.session_state.client_data.get('phone', ''))
    c_trans = st.text_input("Transporte", st.session_state.client_data.get('transportProvider', ''))

st.session_state.client_data.update({
    "fullName": c_name, "address": c_addr, "phone": c_phone, "transportProvider": c_trans
})

st.divider()

# 2. Agregar Productos
st.subheader("Agregar Productos")

with st.container(border=True):
    col_prod, col_qty = st.columns([3, 1])
    with col_prod:
        product_options = {f"{p['id']} - {p['description']}": p for p in PRODUCT_CATALOG}
        selected_option = st.selectbox("Seleccionar del Catálogo", options=list(product_options.keys()))
        selected_product = product_options[selected_option]
    with col_qty:
        qty = st.number_input("Cant.", min_value=1, value=1)

    col_price, col_img = st.columns([1, 2])
    with col_price:
        price_c = st.number_input("Precio C$", min_value=0.0, step=10.0, format="%.2f")
        usd_val = price_c / DEFAULT_EXCHANGE_RATE if price_c else 0
        st.caption(f"Aprox: ${usd_val:.2f}")
    
    with col_img:
        item_image = st.file_uploader("Foto del Producto (Opcional)", type=['png', 'jpg', 'jpeg'], key="prod_img")

    if st.button("➕ Agregar Item a Factura", type="primary"):
        if price_c <= 0:
            st.warning("Ingrese un precio válido.")
        else:
            img_data = None
            if item_image:
                img_data = item_image.getvalue()

            new_item = {
                "product": selected_product,
                "quantity": qty,
                "priceCordobas": price_c,
                "priceDollars": price_c / DEFAULT_EXCHANGE_RATE,
                "custom_image_data": img_data
            }
            st.session_state.invoice_items.append(new_item)
            st.success("Agregado")
            st.rerun()

# 3. Lista de Items
if st.session_state.invoice_items:
    st.write("### Detalle")
    for i, item in enumerate(st.session_state.invoice_items):
        c1, c2, c3, c4 = st.columns([4, 1, 2, 1])
        with c1: 
            st.write(f"**{item['product']['description']}**")
            if item.get('custom_image_data'):
                st.image(item['custom_image_data'], width=100)
        with c2: st.write(f"x{item['quantity']}")
        with c3: st.write(f"C$ {item['priceCordobas'] * item['quantity']:.2f}")
        with c4: 
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.invoice_items.pop(i)
                st.rerun()

st.divider()

# 4. Totales
col_notes, col_totals = st.columns([2, 1])
with col_notes:
    note = st.text_area("Nota (Opcional)", placeholder="Ej: Se entrega Memoria MicroSD de regalo...")
with col_totals:
    subtotal = sum(item['priceCordobas'] * item['quantity'] for item in st.session_state.invoice_items)
    shipping = st.number_input("Envío (C$)", min_value=0.0, step=10.0)
    discount = st.number_input("Descuento (C$)", min_value=0.0, step=10.0)
    total = subtotal + shipping - discount
    st.markdown(f"<h3 style='text-align: right;'>Total: C$ {total:,.2f}</h3>", unsafe_allow_html=True)

# 5. Generar PDF
if st.button("🖨️ Generar PDF", type="secondary", use_container_width=True):
    if not st.session_state.invoice_items:
        st.warning("Factura vacía.")
    else:
        invoice_data = {
            "number": st.session_state.consecutive,
            "date": str(invoice_date),
            "client": st.session_state.client_data,
            "items": st.session_state.invoice_items,
            "shippingCost": shipping,
            "discount": discount,
            "note": note
        }
        
        safe_name = st.session_state.client_data.get('fullName', 'Cliente').strip().replace(" ", "_")
        filename = f"factura_{st.session_state.consecutive}_{safe_name}.pdf"
        
        try:
            # Pasamos el logo que ya leímos arriba
            generate_pdf_file(invoice_data, filename, logo_bytes=logo_bytes)
            
            with open(filename, "rb") as f:
                st.download_button("⬇️ Descargar PDF Final", f, file_name=filename, mime="application/pdf")
        except Exception as e:
            st.error(f"Error PDF: {e}")