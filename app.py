import streamlit as st
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
import random
from datetime import datetime, timedelta
import time
import re

# --- CONFIGURACIÓN DE SEGURIDAD ---
SENDER_EMAIL = "rm.consulting.ventas@gmail.com" 
SENDER_PASSWORD = "gddrauovosjjpmat" 
URL_BASE_READ = "https://docs.google.com/spreadsheets/d/1zPNq5f7FcPcYgz6hIgdqhQyaa72MzVQw2p_CL725WJA"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbz8OpHR9QUuE6Re-cswjYoh7upO4VUfXTBLv1cFRNBSwwQrSQZA8u-lCbSol2vluch4RA/exec"

GIDS = {"empleados": "0", "partidos": "694697724", "apuestas": "494338606"}

# DICCIONARIO DE GRUPOS
GRUPOS_MUNDIAL = {
    'A': ['México', 'Sudáfrica', 'Rep. de Corea', 'Play-Off D'],
    'B': ['Canadá', 'Play-Off A', 'Qatar', 'Suiza'],
    'C': ['Brasil', 'Marruecos', 'Haiti', 'Escocia'],
    'D': ['EE.UU.', 'Paraguay', 'Australia', 'Play-Off C'],
    'E': ['Alemania', 'Curazao', 'Costa de Marfil', 'Ecuador'],
    'F': ['Países Bajos', 'Japón', 'Play-Off B', 'Túnez'],
    'G': ['Bélgica', 'Egipto', 'IR Irán', 'Nueva Zelanda'],
    'H': ['España', 'Cabo Verde', 'Arabia Saudita', 'Uruguay'],
    'I': ['Francia', 'Senegal', 'Play-Off 2', 'Noruega'],
    'J': ['Argentina', 'Argelia', 'Austria', 'Jordán'],
    'K': ['Portugal', 'Play-Off 1', 'Uzbekistán', 'Colombia'],
    'L': ['Inglaterra', 'Croacia', 'Ghana', 'Panamá']
}
PAISES_LISTA = sorted([p for sub in GRUPOS_MUNDIAL.values() for p in sub])

st.set_page_config(page_title="Polla Mundialista 2026", layout="wide")

# --- MOTOR DE DATOS OPTIMIZADO ---
@st.cache_data(ttl=300)
def leer_datos_full():
    data = {}
    for nombre, gid in GIDS.items():
        try:
            url = f"{URL_BASE_READ}/export?format=csv&gid={gid}&t={time.time()}"
            df = pd.read_csv(url, on_bad_lines='skip', engine='python')
            df.columns = df.columns.str.strip()
            # Corrección de NaN: Convertimos todo a string y llenamos vacíos
            df = df.fillna("")
            data[nombre] = df
        except:
            data[nombre] = pd.DataFrame()
    return data

def enviar_correo(destinatario, asunto, cuerpo):
    mensaje = MIMEText(cuerpo)
    mensaje["Subject"] = asunto
    mensaje["From"] = f"Sistema Polla Mundialista 2026 <{SENDER_EMAIL}>"
    mensaje["To"] = destinatario
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, destinatario, mensaje.as_string())
        server.quit()
        return True
    except: return False

def obtener_opciones_dinamicas(texto_equipo, df_partidos):
    txt = str(texto_equipo)
    match_g = re.search(r'grupo\s+([A-L])', txt, re.IGNORECASE)
    if match_g:
        letra = match_g.group(1).upper()
        return GRUPOS_MUNDIAL.get(letra, ["Error"])
    match_p = re.search(r'partido\s*#?\s*(\d+)', txt, re.IGNORECASE)
    if match_p:
        id_buscado = str(match_p.group(1))
        p_prev = df_partidos[df_partidos['id_partido'].astype(str) == id_buscado]
        if not p_prev.empty:
            return [str(p_prev.iloc[0]['equipo_a']), str(p_prev.iloc[0]['equipo_b'])]
    return [txt] if txt != "" else ["Por definir"]

# --- LÓGICA DE NAVEGACIÓN ---
if 'paso' not in st.session_state: st.session_state.paso = 'inicio'

st.title("⚽ Polla Mundialista 2026 - RM Consulting")

if st.session_state.paso == 'inicio':
    cedula_input = st.text_input("Introduce tu Cédula")
    if st.button("Validar y Enviar Código"):
        all_d = leer_datos_full()
        df_e = all_d['empleados']
        if not df_e.empty:
            df_e['cedula'] = df_e['cedula'].astype(str).str.strip()
            u_row = df_e[df_e['cedula'] == str(cedula_input).strip()]
            if not u_row.empty:
                token = str(random.randint(100000, 999999))
                st.session_state.token_verif = token
                st.session_state.datos_usuario = u_row.iloc[0].to_dict()
                if enviar_correo(st.session_state.datos_usuario['correo'], "Código Acceso", f"Tu código: {token}"):
                    st.session_state.paso = 'verificar'
                    st.rerun()
            else: st.error("Cédula no registrada.")

elif st.session_state.paso == 'verificar':
    cod = st.text_input("Ingresa el código enviado", type="password")
    if st.button("Entrar"):
        if cod == st.session_state.token_verif:
            st.session_state.paso = 'apostador'
            st.rerun()
        else: st.error("Código incorrecto.")

elif st.session_state.paso == 'apostador':
    user = st.session_state.datos_usuario
    st.sidebar.success(f"Sesión: {user['nombre']}")
    
    all_d = leer_datos_full()
    df_partidos = all_d['partidos']
    df_apuestas = all_d['apuestas']
    df_empleados = all_d['empleados']
    ahora = datetime.now()

    t1, t2, t3 = st.tabs(["📝 Mis Pronósticos", "🏆 Mi Podio", "📊 Ranking"])

    with t1:
        e_base = {"Ronda grupos": 3, "Dieciseisavos de final": 4, "Octavos de final": 5, "Cuartos de final": 6, "Semifinales": 8, "Tercer lugar": 6, "Final": 10}
        e_extra = {"Ronda grupos": 2, "Dieciseisavos de final": 2, "Octavos de final": 3, "Cuartos de final": 3, "Semifinales": 4, "Tercer lugar": 3, "Final": 5}
        bono_clasifica = {"Octavos de final": 3, "Cuartos de final": 4, "Semifinales": 5, "Final": 6}

        for i, p in df_partidos.iterrows():
            fase = str(p['fase'])
            fecha_p = pd.to_datetime(p['fecha_hora'], dayfirst=True, errors='coerce')
            
            if fase == 'Ronda grupos' or (pd.notna(fecha_p) and ahora >= (fecha_p - timedelta(days=5))):
                df_apuestas['cedula'] = df_apuestas['cedula'].astype(str).str.strip()
                filtro = df_apuestas[(df_apuestas['cedula'] == str(user['cedula'])) & (df_apuestas['id_partido'].astype(str) == str(p['id_partido']))]
                ya = not filtro.empty
                
                with st.expander(f"{fase} | {p['equipo_a']} vs {p['equipo_b']} {'✅' if ya else '⏳'}"):
                    if ya:
                        ap = filtro.iloc[0]
                        # CORRECCIÓN: Aseguramos que los nombres no salgan como nan
                        eq_a_p = str(ap['equipo_a_pred'])
                        eq_b_p = str(ap['equipo_b_pred'])
                        st.info(f"**Tu Pronóstico:** {eq_a_p} {int(ap['goles_a_pred'])} - {int(ap['goles_b_pred'])} {eq_b_p}")
                        
                        # CORRECCIÓN: Mostrar detalle de puntos si hay marcador real
                        if p['goles_a_real'] != "":
                            st.divider()
                            ga_r, gb_r = int(p['goles_a_real']), int(p['goles_b_real'])
                            st.write(f"**Resultado Real:** {ga_r} - {gb_r}")
                            
                            ga_p, gb_p = int(ap['goles_a_pred']), int(ap['goles_b_pred'])
                            pts_p, motivos = 0, []
                            
                            if (ga_p > gb_p and ga_r > gb_r) or (ga_p < gb_p and ga_r < gb_r) or (ga_p == gb_p and ga_r == gb_r):
                                pts_p += e_base.get(fase, 0); motivos.append(f"✅ Ganador/Empate: +{e_base.get(fase, 0)}")
                                if ga_p == ga_r and gb_p == gb_r: pts_p += e_extra.get(fase, 0); motivos.append(f"🎯 Exacto: +{e_extra.get(fase, 0)}")
                            elif ga_p == ga_r or gb_p == gb_r: pts_p = 1; motivos.append("⚽ Goles un equipo: +1")
                            
                            if fase in bono_clasifica:
                                bc = 0
                                if eq_a_p in [str(p['equipo_a']), str(p['equipo_b'])]: bc += bono_clasifica[fase]
                                if eq_b_p in [str(p['equipo_a']), str(p['equipo_b'])]: bc += bono_clasifica[fase]
                                if bc > 0: pts_p += bc; motivos.append(f"🏃 Clasificación: +{bc}")
                            
                            st.subheader(f"Puntos Ganados: {pts_p}")
                            for m in motivos: st.caption(m)
                    else:
                        c1, c2 = st.columns(2)
                        op_a = obtener_opciones_dinamicas(p['equipo_a'], df_partidos)
                        op_b = obtener_opciones_dinamicas(p['equipo_b'], df_partidos)
                        sel_a = c1.selectbox("Equipo A", op_a, key=f"sa{i}")
                        sel_b = c2.selectbox("Equipo B", op_b, key=f"sb{i}")
                        ga = c1.number_input(f"Goles {sel_a}", 0, 15, key=f"ga{i}")
                        gb = c2.number_input(f"Goles {sel_b}", 0, 15, key=f"gb{i}")
                        if st.button("Guardar", key=f"btn{i}"):
                            pay = {"id_apuesta": f"AP-{random.randint(1000,9999)}", "cedula": str(user['cedula']), "id_partido": str(p['id_partido']), "goles_a_pred": ga, "goles_b_pred": gb, "equipo_a_pred": sel_a, "equipo_b_pred": sel_b, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            if requests.post(URL_APPS_SCRIPT, json=pay).text == "Success":
                                st.cache_data.clear(); st.rerun()

    with t2:
        # [Sección de Podio se mantiene igual]
        st.subheader("Tu Podio Final")
        ids_podio = {"999": "Campeón 🥇", "998": "Subcampeón 🥈", "997": "Tercero 🥉"}
        for pid, lab in ids_podio.items():
            f_podio = df_apuestas[(df_apuestas['cedula'] == str(user['cedula'])) & (df_apuestas['id_partido'].astype(str) == pid)]
            if not f_podio.empty: st.success(f"{lab}: {f_podio.iloc[0]['equipo_a_pred']}")
            else:
                sel_p = st.selectbox(f"Elige {lab}", PAISES_LISTA, key=f"p{pid}")
                if st.button(f"Fijar {lab}", key=f"bp{pid}"):
                    pay = {"id_apuesta": f"POD-{pid}", "cedula": str(user['cedula']), "id_partido": pid, "goles_a_pred": 0, "goles_b_pred": 0, "equipo_a_pred": sel_p, "equipo_b_pred": "N/A", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    if requests.post(URL_APPS_SCRIPT, json=pay).text == "Success":
                        st.cache_data.clear(); st.rerun()

    with t3:
        # [Ranking Maestro se mantiene igual]
        st.subheader("Top 15")
        df_res = df_partidos[df_partidos['goles_a_real'] != ""]
        puntos_u, envio_u = {}, {}
        for _, ap in df_apuestas.iterrows():
            ced = str(ap['cedula']).strip()
            id_p = str(ap['id_partido']).strip()
            pts = 0
            p_list = df_partidos[df_partidos['id_partido'].astype(str) == id_p]
            if not p_list.empty:
                m = p_list.iloc[0]
                if m['fase'] in bono_clasifica:
                    if str(ap['equipo_a_pred']) in [str(m['equipo_a']), str(m['equipo_b'])]: pts += bono_clasifica[m['fase']]
                    if str(ap['equipo_b_pred']) in [str(m['equipo_a']), str(m['equipo_b'])]: pts += bono_clasifica[m['fase']]
                if m['goles_a_real'] != "":
                    ga_p, gb_p, ga_r, gb_r = int(ap['goles_a_pred']), int(ap['goles_b_pred']), int(m['goles_a_real']), int(m['goles_b_real'])
                    if ga_p == ga_r and gb_p == gb_r: pts += (e_base.get(m['fase'], 0) + e_extra.get(m['fase'], 0))
                    elif (ga_p > gb_p and ga_r > gb_r) or (ga_p < gb_p and ga_r < gb_r) or (ga_p == gb_p and ga_r == gb_r): pts += e_base.get(m['fase'], 0)
                    elif ga_p == ga_r or gb_p == gb_r: pts += 1
            puntos_u[ced] = puntos_u.get(ced, 0) + pts
            ts = pd.to_datetime(ap['timestamp'])
            if ced not in envio_u or ts < envio_u[ced]: envio_u[ced] = ts

        rk_l = [{"cedula": k, "Empleado": df_empleados[df_empleados['cedula'].astype(str)==k]['nombre'].values[0] if not df_empleados[df_empleados['cedula'].astype(str)==k].empty else k, "Puntos": v, "Ult": envio_u.get(k)} for k, v in puntos_u.items()]
        if rk_l:
            df_f = pd.DataFrame(rk_l).sort_values(by=["Puntos", "Ult"], ascending=[False, True])
            df_f.insert(0, "Pos", range(1, len(df_f)+1))
            c_u = str(user['cedula']).strip()
            df_f["Pos"] = df_f.apply(lambda r: f"🥇 Oro{' ⚽' if r['cedula']==c_u else ''}" if r['Pos']==1 else (f"🥈 Plata{' ⚽' if r['cedula']==c_u else ''}" if r['Pos']==2 else (f"🥉 Bronce{' ⚽' if r['cedula']==c_u else ''}" if r['Pos']==3 else f"{r['Pos']}{' ⚽' if r['cedula']==c_u else ''}")), axis=1)
            df_t = df_f.head(15).copy()
            if not (df_t["cedula"] == c_u).any():
                u_r = df_f[df_f["cedula"] == c_u].copy()
                if not u_r.empty: df_t = pd.concat([df_t, pd.DataFrame([{"Pos": "...", "Empleado": "...", "Puntos": "...", "cedula": "", "Ult": ""}]), u_r], ignore_index=True)
            st.table(df_t.style.apply(lambda x: ['background-color: #198754; color: white; font-weight: bold' if str(x['cedula'])==c_u else '' for _ in x], axis=1).hide(axis='columns', subset=['cedula', 'Ult']))

    if st.sidebar.button("Refrescar Datos"):
        st.cache_data.clear(); st.rerun()
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear(); st.rerun()