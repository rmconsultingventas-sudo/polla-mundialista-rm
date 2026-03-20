import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
import random
from datetime import datetime, timedelta
import time
import base64
import os
import streamlit.components.v1 as components
import pytz

# --- CONFIGURACIÓN DE GIDs ---
# ✅ CORRECCIÓN: Credenciales movidas a st.secrets
# Crea el archivo .streamlit/secrets.toml con:
#
# [email]
# sender = "rm.consulting.ventas@gmail.com"
# password = "gddrauovosjjpmat"
#
SENDER_EMAIL = st.secrets["email"]["sender"]
SENDER_PASSWORD = st.secrets["email"]["password"]

URL_BASE_READ = "https://docs.google.com/spreadsheets/d/1zPNq5f7FcPcYgz6hIgdqhQyaa72MzVQw2p_CL725WJA"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbz8OpHR9QUuE6Re-cswjYoh7upO4VUfXTBLv1cFRNBSwwQrSQZA8u-lCbSol2vluch4RA/exec"

GIDS = {
    "empleados": "0",
    "partidos": "694697724",
    "apuestas": "494338606",
    "config": "204016232",
    "ayuda": "1463155466",
    "banderas": "639193403"
}

st.set_page_config(page_title="Polla Mundialista 2026 - RM", layout="wide")

# --- FUNCIÓN HORA COLOMBIA ---
def obtener_hora_colombia():
    tz = pytz.timezone('America/Bogota')
    return "'" + datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")

# --- FUNCIÓN PARA CARGAR IMAGEN ---
@st.cache_data
def obtener_base64_imagen(nombre_archivo):
    try:
        ruta_actual = os.path.dirname(__file__)
        ruta_archivo = os.path.join(ruta_actual, nombre_archivo)
        with open(ruta_archivo, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

img_base64 = obtener_base64_imagen("fondo.jpeg")

# --- CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp, h1, h2, h3, p, label, .stMarkdown {{
        color: #ffffff !important;
    }}
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }}
    h1 {{
        margin-top: -1.5rem !important;
        padding-bottom: 0.5rem !important;
    }}
    header[data-testid="stHeader"] button {{
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        margin: 5px !important;
    }}
    header[data-testid="stHeader"] svg {{
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(30, 41, 59, 0.3) !important;
        backdrop-filter: none !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }}
    [data-testid="stForm"], .stTabs [data-baseweb="tab-panel"] {{
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        backdrop-filter: blur(10px);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: none;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(40, 167, 69, 0.8) !important;
        color: white !important;
    }}
    div.stButton > button:first-child {{
        background-color: #28a745; color: white; border-radius: 8px;
        border: 2px solid #1e7e34; font-weight: bold;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: #218838; border-color: #1e7e34; color: white;
        box-shadow: 0px 0px 15px rgba(40, 167, 69, 0.5);
    }}
    </style>
""", unsafe_allow_html=True)

# --- LECTURA DE DATOS CON MANEJO DE ERRORES MEJORADO ---
# ✅ CORRECCIÓN: leer_datos() ahora reporta qué pestaña falló en lugar de silenciar el error
@st.cache_data(ttl=60)
def leer_datos():
    data = {}
    errores = []
    for nombre, gid in GIDS.items():
        try:
            url = f"{URL_BASE_READ}/export?format=csv&gid={gid}&t={time.time()}"
            df = pd.read_csv(url, on_bad_lines='skip', engine='python').fillna("")
            df.columns = df.columns.str.strip().str.lower()
            data[nombre] = df
        except Exception as e:
            data[nombre] = pd.DataFrame()
            errores.append(f"**{nombre}**: {str(e)[:80]}")
    return data, errores

def enviar_correo(destinatario, codigo):
    mensaje = MIMEText(f"Tu código de acceso es: {codigo}")
    mensaje["Subject"] = "Código de Acceso - Sistema Polla Mundialista 2026"
    mensaje["From"] = f"Sistema Polla Mundialista 2026 <{SENDER_EMAIL}>"
    mensaje["To"] = destinatario
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, destinatario, mensaje.as_string())
        server.quit()
        return True
    except Exception:
        return False

def parse_fecha(fecha_str):
    try:
        return datetime.strptime(str(fecha_str).strip(), "%d/%m/%Y %H:%M")
    except Exception:
        return None  # ✅ CORRECCIÓN: Retorna None en lugar de fecha futura silenciosa

def obtener_bandera(equipo, df_banderas, es_local=True):
    equipo_limpio = str(equipo).strip().lower()
    if not df_banderas.empty and 'equipo' in df_banderas.columns:
        match = df_banderas[df_banderas['equipo'].astype(str).str.strip().str.lower() == equipo_limpio]
        if not match.empty:
            if 'bandera' in match.columns:
                return match.iloc[0]['bandera']
            if 'url' in match.columns:
                return match.iloc[0]['url']
    if "ganador" in equipo_limpio or "play-off" in equipo_limpio or "1ro" in equipo_limpio or "2do" in equipo_limpio:
        return "🟦" if es_local else "🟥"
    return "🏳️"

def render_equipo_con_bandera(equipo, bandera, es_local=True):
    if str(bandera).startswith("http"):
        img_html = f'<img src="{bandera}" width="24" style="border-radius:2px; box-shadow: 0px 0px 3px rgba(0,0,0,0.3);">'
    else:
        img_html = f'<span style="font-size:18px;">{bandera}</span>'
    if es_local:
        return f'<div style="display:flex; align-items:center; gap:8px;">{img_html} <span style="font-weight:500;">{equipo}</span></div>'
    else:
        return f'<div style="display:flex; align-items:center; justify-content:flex-end; gap:8px;"><span style="font-weight:500;">{equipo}</span> {img_html}</div>'

# --- FLUJO DE PANTALLAS ---
if 'paso' not in st.session_state:
    st.session_state.paso = 'inicio'

# ✅ CORRECCIÓN: leer_datos ahora retorna también los errores
all_data, errores_carga = leer_datos()
config_df = all_data.get('config', pd.DataFrame())

st.title("⚽ Polla Mundialista 2026 - RM Consulting")

# ✅ MEJORA: Mostrar errores de carga de pestañas si los hay
if errores_carga:
    with st.expander("⚠️ Advertencia: algunas pestañas no cargaron correctamente", expanded=False):
        for err in errores_carga:
            st.warning(err)

# --- 1. LOGIN ---
if st.session_state.paso == 'inicio':
    cedula = st.text_input("Introduce tu Cédula para ingresar")
    if st.button("Validar y Enviar Código"):
        df_e = all_data['empleados']
        if not df_e.empty:
            df_e['cedula'] = df_e['cedula'].astype(str).str.strip()
            user = df_e[df_e['cedula'] == str(cedula).strip()]
            if not user.empty:
                token = str(random.randint(100000, 999999))
                st.session_state.token_verif = token
                # ✅ CORRECCIÓN: OTP con expiración de 10 minutos
                st.session_state.token_expira = datetime.now() + timedelta(minutes=10)
                st.session_state.datos_usuario = user.iloc[0].to_dict()
                if enviar_correo(st.session_state.datos_usuario['correo'], token):
                    st.session_state.paso = 'verificar'
                    st.success("Código enviado a tu correo.")
                    st.rerun()
                else:
                    st.error("Error al enviar el correo. Verifica la configuración SMTP.")
            else:
                st.error("Cédula no registrada en el sistema.")
        else:
            st.error("No se pudo cargar la lista de empleados. Intenta refrescando la página.")

elif st.session_state.paso == 'verificar':
    st.info("📩 **¡Código enviado!** Por favor, revisa tu correo electrónico para obtener tu PIN de acceso de 6 dígitos. Si no lo ves en tu bandeja principal, **verifica la carpeta de Spam o Correo no deseado**.")

    # ✅ CORRECCIÓN: Verificar expiración del OTP antes de validar
    tiempo_restante = st.session_state.get('token_expira', datetime.now()) - datetime.now()
    minutos_restantes = int(tiempo_restante.total_seconds() // 60)
    segundos_restantes = int(tiempo_restante.total_seconds() % 60)

    if tiempo_restante.total_seconds() > 0:
        st.caption(f"⏳ El código expira en {minutos_restantes}m {segundos_restantes}s")
    else:
        st.error("⏰ El código ha expirado. Por favor, vuelve a iniciar sesión.")
        if st.button("Volver al inicio"):
            st.session_state.paso = 'inicio'
            st.rerun()
        st.stop()

    cod = st.text_input("Ingresa el código de 6 dígitos", type="password")
    if st.button("Entrar"):
        # ✅ CORRECCIÓN: Doble chequeo de expiración al momento de validar
        if datetime.now() > st.session_state.get('token_expira', datetime.now()):
            st.error("⏰ El código expiró. Vuelve a ingresar tu cédula.")
            st.session_state.paso = 'inicio'
            st.rerun()
        elif cod == st.session_state.token_verif:
            # ✅ Invalidar token tras uso exitoso
            st.session_state.token_verif = None
            st.session_state.token_expira = None
            st.session_state.paso = 'apostador'
            st.rerun()
        else:
            st.error("Código incorrecto.")

# --- 2. ENTORNO DEL APOSTADOR ---
elif st.session_state.paso == 'apostador':
    user = st.session_state.datos_usuario
    st.sidebar.success(f"Sesión activa: {user.get('nombre', 'Usuario')}")

    df_banderas = all_data['banderas']
    estados_dict = {}
    if not df_banderas.empty and 'equipo' in df_banderas.columns and 'estado' in df_banderas.columns:
        estados_dict = dict(zip(
            df_banderas['equipo'].astype(str).str.strip().str.lower(),
            df_banderas['estado'].astype(str).str.strip().str.lower()
        ))

    def obtener_etiqueta_estado(equipo):
        if not equipo or pd.isna(equipo) or str(equipo).strip() == "":
            return ""
        estado = str(estados_dict.get(str(equipo).strip().lower(), "activo"))
        if estado == "activo":
            return '<span style="font-size: 13px; font-weight: bold; color: #09ab3b; background-color: #e6ffec; padding: 2px 6px; border-radius: 4px;">✅ Oportunidad activa</span>'
        else:
            return '<span style="font-size: 13px; font-weight: bold; color: #ff4b4b; background-color: #ffe6e6; padding: 2px 6px; border-radius: 4px;">🚫 Pronóstico nulo, equipo fuera del torneo</span>'

    ahora = datetime.now()

    # ✅ CORRECCIÓN: Validación de estado de config con advertencia explícita
    rondas_activas = []
    f_apertura = None
    f_cierre = None
    config_valida = False

    if not config_df.empty and 'estado' in config_df.columns:
        df_activas = config_df[config_df['estado'].astype(str).str.strip().str.lower() == 'activo']
        if not df_activas.empty:
            rondas_activas = df_activas['ronda_activa'].astype(str).str.strip().tolist()
            f_apertura = parse_fecha(df_activas.iloc[0]['apertura'])
            f_cierre = parse_fecha(df_activas.iloc[0]['cierre'])

            # ✅ CORRECCIÓN: Advertir si las fechas no tienen formato válido
            if f_apertura is None or f_cierre is None:
                st.warning("⚠️ **Aviso al administrador:** Las fechas de apertura/cierre en la hoja `config` tienen un formato inválido. Se esperan fechas con formato `DD/MM/YYYY HH:MM`. Las apuestas están bloqueadas hasta que se corrija.")
            else:
                config_valida = True
        else:
            # ✅ CORRECCIÓN: Advertir si ninguna ronda está activa
            estados_encontrados = config_df['estado'].astype(str).str.strip().unique().tolist()
            st.warning(f"⚠️ **Aviso:** Ninguna ronda está marcada como `Activo` en la hoja `config`. Estados encontrados: `{', '.join(estados_encontrados)}`. Verifica que el valor sea exactamente `Activo` (con A mayúscula).")
    else:
        st.warning("⚠️ No se pudo cargar la hoja `config` o le falta la columna `estado`.")

    # Fallback seguro si config no es válida
    if not config_valida:
        f_apertura = ahora + timedelta(days=365)
        f_cierre = ahora + timedelta(days=365)
        rondas_activas = ["—"]

    nombres_rondas_display = " + ".join(rondas_activas) if len(rondas_activas) <= 2 else f"Múltiples Fases ({len(rondas_activas)})"

    # --- MAQUETACIÓN: RELOJ, FECHA E INSTRUCTIVO ---
    st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
    col_timer, col_deadline, col_inst = st.columns([1.2, 1.2, 2])

    with col_timer:
        if config_valida and f_apertura <= ahora <= f_cierre:
            cierre_iso = f_cierre.strftime("%Y-%m-%dT%H:%M:%S")
            reloj_html = f"""
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Courier New', Courier, monospace; background-color: transparent; }}
                .timer-box {{
                    background-color: rgba(15, 23, 42, 0.7);
                    color: #ffc107;
                    padding: 8px 10px;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 193, 7, 0.4);
                    font-size: 15px;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }}
            </style>
            <div class="timer-box" id="clock">⏳ Calculando...</div>
            <script>
                var countDownDate = new Date("{cierre_iso}").getTime();
                var x = setInterval(function() {{
                    var now = new Date().getTime();
                    var distance = countDownDate - now;
                    if (distance < 0) {{
                        clearInterval(x);
                        document.getElementById("clock").innerHTML = "🔒 CERRADO";
                    }} else {{
                        var d = Math.floor(distance / (1000 * 60 * 60 * 24));
                        var h = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var m = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var s = Math.floor((distance % (1000 * 60)) / 1000);
                        h = (h < 10) ? "0" + h : h; m = (m < 10) ? "0" + m : m; s = (s < 10) ? "0" + s : s;
                        document.getElementById("clock").innerHTML = "⏳ " + d + "d " + h + ":" + m + ":" + s;
                    }}
                }}, 1000);
            </script>
            """
            components.html(reloj_html, height=45)

    with col_deadline:
        if config_valida and f_apertura <= ahora <= f_cierre:
            st.markdown(f"""
                <div style="background-color: rgba(15, 23, 42, 0.7); color: #e2e8f0; padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); font-size: 14px; text-align: center; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 38px; display: flex; align-items: center; justify-content: center;">
                    🕒 Límite: {f_cierre.strftime('%d/%m/%y %H:%M')}
                </div>
            """, unsafe_allow_html=True)

    with col_inst:
        with st.expander("📖 ¿Cómo funciona? Instructivo rápido"):
            st.markdown("📝 **Pronósticos:** Ingresa goles y guarda.\n🥇 **Podio:** Elige Campeón, Sub y Tercero.\n📊 **Ranking:** Tu posición en tiempo real.")

    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Mis Pronósticos", "🥇 Mi Podio", "📊 Ranking", "❓ Ayuda"])

    # --- PESTAÑA 1: APUESTAS ---
    with tab1:
        if not config_valida:
            st.error("🔒 Las apuestas no están disponibles porque la configuración de rondas no es válida.")
        elif ahora < f_apertura:
            st.info(f"🕒 La fase de apuestas abrirá el {f_apertura.strftime('%d/%m/%Y %H:%M')}.")
        elif ahora > f_cierre:
            st.error(f"🔒 Las apuestas cerraron el {f_cierre.strftime('%d/%m/%Y %H:%M')}.")
        else:
            with st.form("form_masivo"):
                st.subheader(f"Carga de marcadores: {nombres_rondas_display}")
                df_p = all_data['partidos']
                df_ap = all_data['apuestas']
                df_banderas = all_data['banderas']

                rondas_lower = [r.lower() for r in rondas_activas]
                condiciones = df_p['fase'].astype(str).str.strip().str.lower().isin(rondas_lower)
                partidos_ronda = df_p[condiciones]

                mis_apuestas = df_ap[df_ap['cedula'].astype(str).str.strip() == str(user['cedula']).strip()].copy()
                mis_apuestas['timestamp'] = pd.to_datetime(mis_apuestas['timestamp'], errors='coerce')
                mis_apuestas = mis_apuestas.sort_values('timestamp', ascending=False)

                c1, c2, c3, c_vs, c4, c5, c6 = st.columns([1.5, 2, 0.9, 0.7, 0.9, 2, 1.5])
                c1.markdown("**Partido/Grupo**")
                c2.markdown("**Equipo Local**")
                c3.markdown("**Goles L**")
                c_vs.markdown("")
                c4.markdown("**Goles V**")
                c5.markdown("**Equipo Visitante**")
                c6.markdown("**Estado / Puntos**")
                st.divider()

                respuestas = {}

                for _, p in partidos_ronda.iterrows():
                    pid = str(p['id_partido'])
                    ap_previa = mis_apuestas[mis_apuestas['id_partido'].astype(str) == pid]
                    ya_apostado = not ap_previa.empty and str(ap_previa.iloc[0]['goles_a_pred']).strip() != ""

                    def_ga = int(float(ap_previa.iloc[0]['goles_a_pred'])) if ya_apostado else 0
                    def_gb = int(float(ap_previa.iloc[0]['goles_b_pred'])) if ya_apostado else 0

                    real_a = str(p.get('goles_a_real', '')).strip()
                    real_b = str(p.get('goles_b_real', '')).strip()
                    partido_jugado = real_a != "" and real_b != "" and real_a != "nan" and real_b != "nan"

                    if partido_jugado and ya_apostado:
                        gr, br = int(float(real_a)), int(float(real_b))
                        gp, bp = def_ga, def_gb
                        if gp == gr and bp == br:
                            msg_estado = "🎯 +5 Pts (Exacto)"
                        elif (gp > bp and gr > br) or (gp < bp and gr < br) or (gp == bp and gr == br):
                            msg_estado = "📈 +3 Pts (Tend)"
                        elif gp == gr or bp == br:
                            msg_estado = "⚽ +1 Pt (Goles)"
                        else:
                            msg_estado = "❌ 0 Pts"
                    elif ya_apostado:
                        msg_estado = "✅ Guardado"
                    else:
                        msg_estado = "⏳ Sin definir"

                    fase_txt = str(p.get('fase', ''))
                    grupo_letra = str(p.get('grupo', '?')).strip()
                    contexto_txt = f"(Grupo {grupo_letra})" if "grupos" in fase_txt.lower() and grupo_letra != "" else f"({fase_txt})"

                    fecha_str = str(p.get('fecha_hora', '')).strip()
                    if fecha_str != "" and fecha_str.lower() != "nan":
                        fecha_corta = fecha_str[:5] + " " + fecha_str[-5:] if len(fecha_str) >= 15 else fecha_str
                    else:
                        fecha_corta = "Por definir"

                    c1, c2, c3, c_vs, c4, c5, c6 = st.columns([1.5, 2, 0.9, 0.7, 0.9, 2, 1.5], vertical_alignment="center")
                    c1.caption(f"#{pid} {contexto_txt}")

                    eq_a = str(p.get('equipo_a', ''))
                    eq_b = str(p.get('equipo_b', ''))

                    bandera_a = obtener_bandera(eq_a, df_banderas, True)
                    bandera_b = obtener_bandera(eq_b, df_banderas, False)

                    c2.markdown(render_equipo_con_bandera(eq_a, bandera_a, True), unsafe_allow_html=True)

                    disabled_input = partido_jugado
                    ga = c3.number_input("A", min_value=0, max_value=20, value=def_ga, key=f"ga_{pid}", label_visibility="collapsed", disabled=disabled_input)

                    c_vs.markdown(f"""
                        <div style="text-align: center; line-height: 1.1; margin-top: 5px;">
                            <strong style="font-size: 14px; color: white;">VS</strong><br>
                            <span style="font-size: 10px; color: #a0aec0;">{fecha_corta}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    gb = c4.number_input("B", min_value=0, max_value=20, value=def_gb, key=f"gb_{pid}", label_visibility="collapsed", disabled=disabled_input)

                    c5.markdown(render_equipo_con_bandera(eq_b, bandera_b, False), unsafe_allow_html=True)
                    c6.caption(msg_estado)
                    st.divider()

                    if not disabled_input:
                        respuestas[pid] = (eq_a, eq_b, ga, gb)

                st.info(f"💡 Recuerda que puedes modificar tus valores hasta el **{f_cierre.strftime('%d/%m/%Y %H:%M')}**. Los partidos en blanco se guardarán como 0 - 0.")
                confirmacion = st.checkbox("Confirmo que deseo guardar estos marcadores en la base de datos.")

                enviado = st.form_submit_button("💾 GUARDAR TODOS MIS PRONÓSTICOS", use_container_width=True)

                if enviado:
                    if not confirmacion:
                        st.error("⚠️ Debes marcar la casilla de confirmación antes de guardar.")
                    else:
                        texto_estado = st.empty()
                        barra_carga = st.progress(0)
                        texto_estado.info("⏳ Empaquetando y enviando pronósticos... Por favor espera.")
                        barra_carga.progress(40)

                        ts = obtener_hora_colombia()
                        lote_apuestas = []

                        for id_p, datos in respuestas.items():
                            # ✅ CORRECCIÓN: Estructura con 9 columnas alineadas con Google Sheets
                            # Orden: id_apuesta, cedula, id_partido, goles_a_pred, goles_b_pred,
                            #        puntos_ganados, timestamp, equipo_a_pred, equipo_b_pred
                            lote_apuestas.append({
                                "id_apuesta": f"AP-{id_p}-{random.randint(100, 999)}",
                                "cedula": str(user['cedula']),
                                "id_partido": id_p,
                                "goles_a_pred": datos[2],
                                "goles_b_pred": datos[3],
                                "puntos_ganados": "",
                                "timestamp": ts,
                                "equipo_a_pred": datos[0],
                                "equipo_b_pred": datos[1]
                            })

                        barra_carga.progress(70)

                        if len(lote_apuestas) > 0:
                            try:
                                res = requests.post(URL_APPS_SCRIPT, json=lote_apuestas, timeout=15)
                                if res.text == "Success":
                                    texto_estado.empty()
                                    barra_carga.progress(100)
                                    st.balloons()
                                    st.success("¡Marcadores guardados exitosamente!")
                                    time.sleep(3)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    texto_estado.error(f"Error de base de datos: {res.text}")
                            except requests.exceptions.Timeout:
                                texto_estado.error("⏰ La solicitud tardó demasiado. Verifica tu conexión e intenta de nuevo.")
                            except Exception:
                                texto_estado.error("Hubo un error de conexión. Intenta nuevamente.")

    # --- PESTAÑA 2: MI PODIO ---
    with tab2:
        st.subheader("Define tu Podio Final")
        df_ap = all_data['apuestas'].copy()
        df_p = all_data['partidos']

        equipos_raw = list(set(df_p['equipo_a']).union(set(df_p['equipo_b'])))
        paises_validos = sorted([
            eq for eq in equipos_raw
            if "Ganador" not in eq and "Play-Off" not in eq
            and "1ro" not in eq and "2do" not in eq and eq != ""
        ])
        if not paises_validos:
            paises_validos = ["Colombia", "Brasil", "Argentina"]

        ids_podio = {"999": "Campeón 🥇", "998": "Subcampeón 🥈", "997": "Tercero 🥉"}

        for pid, lab in ids_podio.items():
            f_podio = df_ap[
                (df_ap['cedula'].astype(str).str.strip() == str(user['cedula']).strip()) &
                (df_ap['id_partido'].astype(str) == pid)
            ].copy()

            if not f_podio.empty:
                f_podio['timestamp'] = pd.to_datetime(f_podio['timestamp'], errors='coerce')
                f_podio = f_podio.sort_values('timestamp', ascending=False)

                equipo_guardado = str(f_podio.iloc[0]['equipo_a_pred']).strip()
                fecha_guardada = str(f_podio.iloc[0]['timestamp']).replace("'", "").strip()
                if len(fecha_guardada) > 16:
                    fecha_guardada = fecha_guardada[:16]

                st.markdown(f"#### {lab}")
                st.markdown(f"**{equipo_guardado}**")
                st.markdown(
                    f"{obtener_etiqueta_estado(equipo_guardado)} "
                    f"<span style='color:gray; font-size:11px; margin-left: 10px;'>(Guardado: {fecha_guardada})</span>",
                    unsafe_allow_html=True
                )
                st.divider()
            else:
                if config_valida and f_apertura <= ahora <= f_cierre:
                    c1, c2 = st.columns([3, 1])
                    sel_p = c1.selectbox(f"Elige {lab}", paises_validos, key=f"p{pid}")
                    if c2.button(f"Fijar {lab}", key=f"bp{pid}"):
                        ts_podio = obtener_hora_colombia()
                        # ✅ CORRECCIÓN: Estructura podio con 9 columnas alineadas
                        pay = [{
                            "id_apuesta": f"POD-{pid}",
                            "cedula": str(user['cedula']),
                            "id_partido": pid,
                            "goles_a_pred": 0,
                            "goles_b_pred": 0,
                            "puntos_ganados": "",
                            "timestamp": ts_podio,
                            "equipo_a_pred": sel_p,
                            "equipo_b_pred": "N/A"
                        }]
                        if requests.post(URL_APPS_SCRIPT, json=pay, timeout=15).text == "Success":
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.warning("Selección de podio deshabilitada por límite de tiempo.")

    # --- PESTAÑA 3: RANKING ---
    with tab3:
        st.subheader("🏆 Ranking General")
        df_ap = all_data['apuestas'].copy()
        df_pa = all_data['partidos']
        df_e = all_data['empleados']
        df_c = all_data['config']

        df_pa_reales = df_pa[
            (df_pa['goles_a_real'].astype(str).str.strip() != "") &
            (df_pa['goles_a_real'].astype(str).str.strip() != "nan")
        ]

        if df_pa_reales.empty:
            st.info("Aún no hay resultados reales cargados para calcular el ranking.")
        else:
            ranking_list = []
            for cedula_u in df_ap['cedula'].astype(str).str.strip().unique():
                if cedula_u == "":
                    continue
                user_ap = df_ap[df_ap['cedula'].astype(str).str.strip() == cedula_u].copy()
                user_ap['timestamp'] = pd.to_datetime(user_ap['timestamp'], errors='coerce')
                user_ap = user_ap.sort_values('timestamp', ascending=False).drop_duplicates(subset=['id_partido'])

                pts, exactos, tendencias = 0, 0, 0
                ultima_apuesta = user_ap['timestamp'].max()

                for _, ap in user_ap.iterrows():
                    p_real = df_pa_reales[df_pa_reales['id_partido'].astype(str) == str(ap['id_partido'])]
                    if not p_real.empty:
                        gr = int(float(p_real.iloc[0]['goles_a_real']))
                        br = int(float(p_real.iloc[0]['goles_b_real']))
                        if str(ap['goles_a_pred']).strip() == "" or str(ap['goles_a_pred']).strip() == "nan":
                            continue
                        gp = int(float(ap['goles_a_pred']))
                        bp = int(float(ap['goles_b_pred']))

                        if gp == gr and bp == br:
                            pts += 5; exactos += 1; tendencias += 1
                        elif (gp > bp and gr > br) or (gp < bp and gr < br) or (gp == bp and gr == br):
                            pts += 3; tendencias += 1
                        elif gp == gr or bp == br:
                            pts += 1

                nom_u = df_e[df_e['cedula'].astype(str).str.strip() == cedula_u]['nombre'].values
                full_name = str(nom_u[0]).strip() if len(nom_u) > 0 else f"User_{cedula_u[-4:]}"
                nombre_label = f"{full_name}_{cedula_u[-4:]}"

                ranking_list.append({
                    "Empleado": nombre_label,
                    "Pts Totales": pts,
                    "1er Criterio": exactos,
                    "2do Criterio": tendencias,
                    "3er Criterio": ultima_apuesta,
                    "cedula": cedula_u
                })

            if len(ranking_list) == 0:
                st.info("Aún no hay pronósticos guardados por ningún usuario para calcular el ranking.")
            else:
                df_rank_base = pd.DataFrame(ranking_list).sort_values(
                    by=["Pts Totales", "1er Criterio", "2do Criterio", "3er Criterio"],
                    ascending=[False, False, False, True]
                )
                df_rank_base.reset_index(drop=True, inplace=True)
                df_rank_base.insert(0, "Pos", range(1, len(df_rank_base) + 1))

                limite_r = 15
                if not df_c.empty and 'limite_ranking' in df_c.columns:
                    val = str(df_c.iloc[0]['limite_ranking']).strip()
                    if val != "" and val != "nan":
                        try:
                            limite_r = int(float(val))
                        except ValueError:
                            pass  # Mantiene el default de 15

                df_mostrar = df_rank_base.head(limite_r).copy()
                ced_activa = str(user['cedula']).strip()

                if ced_activa not in df_mostrar['cedula'].astype(str).values:
                    user_row = df_rank_base[df_rank_base['cedula'].astype(str) == ced_activa]
                    if not user_row.empty:
                        dummy_row = pd.DataFrame([{
                            "Pos": None,
                            "Empleado": "... ⬇️ ...",
                            "Pts Totales": "...",
                            "1er Criterio": "...",
                            "2do Criterio": "...",
                            "3er Criterio": pd.NaT,
                            "cedula": "separador"
                        }])
                        df_mostrar = pd.concat([df_mostrar, dummy_row, user_row], ignore_index=True)

                df_para_mostrar = df_mostrar.rename(columns={
                    "Pos": "𝐏𝐎𝐒",
                    "Empleado": "𝐄𝐌𝐏𝐋𝐄𝐀𝐃𝐎",
                    "Pts Totales": "𝐏𝐓𝐒 𝐓𝐎𝐓𝐀𝐋𝐄𝐒",
                    "1er Criterio": "𝟏𝐄𝐑 𝐂𝐑𝐈𝐓𝐄𝐑𝐈𝐎: 𝐄𝐗𝐀𝐂𝐓𝐎𝐒",
                    "2do Criterio": "𝟐𝐃𝐎 𝐂𝐑𝐈𝐓𝐄𝐑𝐈𝐎: 𝐓𝐄𝐍𝐃𝐄𝐍𝐂𝐈𝐀",
                    "3er Criterio": "Ú𝐋𝐓. 𝐀𝐏𝐔𝐄𝐒𝐓𝐀",
                    "cedula": "cedula"
                })

                indices_usuario = df_para_mostrar.index[
                    df_para_mostrar['cedula'].astype(str) == ced_activa
                ].tolist()
                df_publico = df_para_mostrar.drop(columns=['cedula'])

                def estilo_usuario_seguro(x):
                    df_estilos = pd.DataFrame('text-align: center', index=x.index, columns=x.columns)
                    for idx in indices_usuario:
                        if idx in df_estilos.index:
                            df_estilos.loc[idx, :] = 'background-color: #198754; color: white; text-align: center'
                    return df_estilos

                st.dataframe(
                    df_publico.style.apply(estilo_usuario_seguro, axis=None),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "𝟏𝐄𝐑 𝐂𝐑𝐈𝐓𝐄𝐑𝐈𝐎: 𝐄𝐗𝐀𝐂𝐓𝐎𝐒": st.column_config.NumberColumn(help="Marcadores exactos acertados (+5 Pts)"),
                        "𝟐𝐃𝐎 𝐂𝐑𝐈𝐓𝐄𝐑𝐈𝐎: 𝐓𝐄𝐍𝐃𝐄𝐍𝐂𝐈𝐀": st.column_config.NumberColumn(help="Tendencias de ganador acertadas (+3 Pts)"),
                        "Ú𝐋𝐓. 𝐀𝐏𝐔𝐄𝐒𝐓𝐀": st.column_config.DatetimeColumn(help="Fecha y hora de desempate", format="DD/MM/YYYY HH:mm:ss")
                    }
                )

    # --- PESTAÑA 4: AYUDA ---
    with tab4:
        df_ayuda = all_data['ayuda']
        if not df_ayuda.empty:
            columna_texto = df_ayuda.columns[0]
            texto_manual = str(df_ayuda.iloc[0][columna_texto]).strip()
            if texto_manual != "" and texto_manual != "nan":
                st.markdown(texto_manual)
            else:
                st.info("El administrador aún no ha escrito el manual en la celda A2 de la pestaña 'ayuda'.")
        else:
            st.info("No se pudo conectar con la pestaña 'ayuda' del Excel. Verifica el GID.")

    # --- MENÚ LATERAL ---
    st.sidebar.divider()
    if st.sidebar.button("🔄 Refrescar Datos (Actualizar Ranking)"):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()