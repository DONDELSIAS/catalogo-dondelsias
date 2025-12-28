import streamlit as st
import os
import json
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Catálogo V3.0 (Galería)", page_icon="🛍️", layout="wide")

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_BASE = os.path.join(DIRECTORIO_ACTUAL, "Base De Datos")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .card { background-color: #ffffff; border-radius: 10px; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px; text-align: center; }
    .price-tag { background-color: #2e7d32; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .fb-price { color: #1877F2; font-weight: bold; font-size: 0.9em; }
    .brand-tag { font-weight: 700; color: #333; text-transform: uppercase; font-size: 0.9em; }
    .size-tag { background-color: #1976d2; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }
    .status-vendido { color: #d32f2f; font-weight: bold; border: 1px solid #d32f2f; padding: 2px 4px; border-radius: 4px; font-size: 0.8em;}
    .status-dispo { color: #388e3c; font-weight: bold; border: 1px solid #388e3c; padding: 2px 4px; border-radius: 4px; font-size: 0.8em;}
    div[data-testid="stImage"] { border-radius: 8px; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_inventario_completo():
    items = []
    if not os.path.exists(CARPETA_BASE): return []

    for sesion in os.listdir(CARPETA_BASE):
        ruta_s = os.path.join(CARPETA_BASE, sesion)
        if not os.path.isdir(ruta_s): continue
        
        for cat in os.listdir(ruta_s):
            ruta_c = os.path.join(ruta_s, cat)
            if not os.path.isdir(ruta_c): continue
            
            for prenda in os.listdir(ruta_c):
                ruta_p = os.path.join(ruta_c, prenda)
                ruta_j = os.path.join(ruta_p, "metadata.json")
                
                if os.path.exists(ruta_j):
                    try:
                        with open(ruta_j, 'r', encoding='utf-8') as f: m = json.load(f)
                        
                        fin = m.get('finanzas', {})
                        estado = fin.get('estado_venta', 'Disponible')
                        
                        # --- BÚSQUEDA DE FOTOS (GALERÍA) ---
                        # 1. Foto Principal (Portada)
                        foto_portada = None
                        posibles_portada = [f"{prenda}_Frente_Mini.jpg", f"{prenda}_Frente.jpg", "Frente.jpg"]
                        
                        for p in posibles_portada:
                            if os.path.exists(os.path.join(ruta_p, p)):
                                foto_portada = os.path.join(ruta_p, p)
                                break
                        
                        if not foto_portada: continue # Si no hay portada, no mostramos
                        
                        # 2. Galería Completa (Todas las Mini)
                        galeria = []
                        # Listamos todos los archivos de la carpeta
                        for f in os.listdir(ruta_p):
                            if f.lower().endswith("_mini.jpg"):
                                galeria.append(os.path.join(ruta_p, f))
                        
                        # Si no hay minis, usamos las normales (Plan B)
                        if not galeria:
                            for f in os.listdir(ruta_p):
                                if f.lower().endswith(('.jpg', '.jpeg', '.png')) and "story" not in f.lower():
                                    galeria.append(os.path.join(ruta_p, f))
                        
                        # Ordenamos: Frente primero
                        galeria.sort(key=lambda x: 0 if "frente" in x.lower() else 1)

                        # DATOS
                        intel = m.get('inteligencia_negocio', {})
                        items.append({
                            "id": prenda,
                            "marca": m.get('marca', 'GENERICO').upper(),
                            "talla": intel.get('talla_real_v8', m.get('talla', 'N/A')),
                            "tipo": intel.get('tipo_cuerpo', 'SUPERIOR').upper(),
                            "subtipo": m.get('subtipo', 'Prenda'),
                            "precio": fin.get('precio_venta_clp', 0),
                            "precio_fb": fin.get('precio_facebook', 0), # Precio FB Específico
                            "estado": estado,
                            "img_portada": foto_portada,
                            "galeria_paths": galeria,
                            "desc": m.get('descripcion', ''),
                            "medidas": m.get('medidas', {}),
                            "ubi": m.get('logistica', {}).get('ubicacion', '?')
                        })
                    except: pass
    return items

# --- INTERFAZ ---
st.title("🛍️ Catálogo Maestro")

inventario = cargar_inventario_completo()

if not inventario:
    st.warning("No hay inventario cargado.")
    st.stop()

# --- FILTROS ---
with st.expander("🔍 Filtros Avanzados", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    todas_tallas = sorted(list(set([x['talla'] for x in inventario])))
    todas_marcas = sorted(list(set([x['marca'] for x in inventario])))
    
    f_estado = c1.multiselect("Estado", ["Disponible", "Reservado", "Vendido"], default=["Disponible"])
    f_talla = c2.multiselect("Talla", todas_tallas)
    f_marca = c3.multiselect("Marca", todas_marcas)
    f_orden = c4.selectbox("Orden", ["Más Nuevos", "Menor Precio", "Mayor Precio"])

# Lógica de Filtrado
filtrados = [x for x in inventario if x['estado'] in f_estado]
if f_talla: filtrados = [x for x in filtrados if x['talla'] in f_talla]
if f_marca: filtrados = [x for x in filtrados if x['marca'] in f_marca]

if f_orden == "Menor Precio": filtrados.sort(key=lambda x: x['precio'])
elif f_orden == "Mayor Precio": filtrados.sort(key=lambda x: x['precio'], reverse=True)
else: filtrados.sort(key=lambda x: x['id'], reverse=True)

# --- PAGINACIÓN ---
st.divider()
items_por_pagina = 24
if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = 0
if 'filtro_hash' not in st.session_state: st.session_state.filtro_hash = str(len(filtrados))
if str(len(filtrados)) != st.session_state.filtro_hash:
    st.session_state.pagina_actual = 0
    st.session_state.filtro_hash = str(len(filtrados))

inicio = st.session_state.pagina_actual * items_por_pagina
fin = inicio + items_por_pagina
lote_a_mostrar = filtrados[inicio:fin]

st.caption(f"Viendo {len(lote_a_mostrar)} de {len(filtrados)} prendas.")

cols = st.columns(3)
for i, item in enumerate(lote_a_mostrar):
    col = cols[i % 3]
    with col:
        # TARJETA PRINCIPAL
        try:
            st.image(item['img_portada'], use_container_width=True)
        except: st.error("Error img")
        
        # Estado Visual
        clase_estado = "status-dispo" if item['estado'] == 'Disponible' else "status-vendido"
        
        st.markdown(f"""
            <div class='card'>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                    <span class='brand-tag'>{item['marca']}</span>
                    <span class='{clase_estado}'>{item['estado']}</span>
                </div>
                <div style='color: #666; font-size: 0.8em; margin-bottom: 5px;'>{item['subtipo']}</div>
                <div>
                    <span class='size-tag'>{item['talla']}</span>
                    <span class='price-tag'>${item['precio']:,}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- DESPLEGABLE CON GALERÍA Y PRECIO FB ---
        with st.popover(f"ℹ️ +Info / Fotos"):
            # 1. Datos Financieros
            if item['precio_fb'] > 0:
                st.markdown(f"🔵 **Precio Facebook:** <span class='fb-price'>${item['precio_fb']:,}</span>", unsafe_allow_html=True)
            
            st.markdown(f"**ID:** `{item['id']}`")
            st.markdown(f"📍 **Ubicación:** {item['ubi']}")
            
            m = item['medidas']
            if item['tipo'] == 'SUPERIOR': st.write(f"📐 **Medidas:** {m.get('ancho',0)} x {m.get('largo',0)} cm")
            else: st.write(f"📐 **Cintura:** {m.get('ancho',0)} cm | Largo: {m.get('largo',0)} cm")
            
            if item['desc']: st.info(item['desc'])
            
            st.divider()
            st.markdown("📸 **Galería de Fotos:**")
            
            # 2. Galería de Fotos (Scroll vertical simple dentro del popover)
            for path_foto in item['galeria_paths']:
                try:
                    st.image(path_foto, caption=os.path.basename(path_foto).split('_')[1], use_container_width=True)
                except: pass

st.divider()
c_prev, c_info, c_next = st.columns([1, 2, 1])
with c_prev:
    if st.session_state.pagina_actual > 0:
        if st.button("⬅️ Anterior"): st.session_state.pagina_actual -= 1; st.rerun()
with c_next:
    if fin < len(filtrados):
        if st.button("Siguiente ➡️"): st.session_state.pagina_actual += 1; st.rerun()