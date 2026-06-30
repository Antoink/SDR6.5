import streamlit as st
import pandas as pd
import base64
import os
import re
import unicodedata
import matplotlib.pyplot as plt
import numpy as np
from math import pi
from io import BytesIO
from scipy import stats
from PIL import Image, ImageDraw
import io
import plotly.graph_objects as go

from utils import SDR_RED, load_data, get_kpi_card_html

from team_profiling import show_team_page
from profiling_report import generate_report
from clustering import show_clustering_page

from config_rapport import OFFICIAL_STRUCTURE, TEAM_STRUCTURE, REPORT_NORMES, UNITS

# ajouts en cours 
from evolution import show_evolution_page
from comparateur import show_comparateur_page
from classement import show_classement_page
import glob



# Mapping pour faire correspondre les Libellés UI -> Colonnes Excel
# Mapping pour faire correspondre les Libellés UI -> Colonnes Excel
COL_MAPPING = {
    "Knee To Wall (D)": "Knee to wall D",
    "Sit And Reach": "Sit and reach",
    "Somme ADD": "Somme ADD", "Adducteurs (G)": "Adducteur G", "Adducteurs (D)": "Adducteur D",
    "Ratio Squeeze": "Ratio Squeeze (ADD/ABD)", "Somme ABD": "Somme ABD",
    "Abducteurs (G)": "Abducteur G", "Abducteurs (D)": "Abducteur D",
    "Nordic Ischio (G)": "Nordic G", "Nordic Ischio (D)": "Nordic D",
    "Inverseur (G)": "Inverseur G", "Inverseur (D)": "Inverseur D",
    "Everseur (G)": "Everseur G", "Everseur (D)": "Everseur D",
    "Endurance Heel Raise (G)": "Endurance Heel Raise G", "Endurance Heel Raise (D)": "Endurance Heel Raise D",
    
    
    # ---- SAUTS (Mise à jour) ----
    "CMJ 2JB": "CMJ 2JB", 
    "Drop jump": "Drop jump",
    "Peak Force CMJ": "Peak Force CMJ", 
    "RFD CMJ": "RFD CMJ", 
    "RSI CMJ": "RSI",
    # -----------------------------
    
    "Wattbike (6s)": "Wattbike 6s (W)", "Squat belt (N)": "Squat belt (N)",
    "SV1": "SV1", "SV2": "SV2", "FC": "FC", "VMA": "VMA",
    "Distance Totale": "Distance totale", "Distance HSR": "Distance HSR", "Distance Sprint (92% Vimax)": "Distance Sprint (92% Vimax)",
    "Nb Accélérations": "Nb Acc", "Nb Décélérations": "Nb Dec",
    "Vmax": "Vmax", "Amax": "Amax", "Dmax": "Dmax", "Temps sur 10m": "Temps sur 10m",
    "Q Conc 60° (G)": "Q G conc 60°/s", "Q Conc 60° (D)": "Q Dt conc 60°/s",
    "Q Conc 240° (G)": "Q G conc 240°/s", "Q Conc 240° (D)": "Q Dt conc 240°/s",
    "IJ Conc 60° (G)": "IJ G conc 60°/s", "IJ Conc 60° (D)": "IJ Dt conc 60°/s",
    "IJ Conc 240° (G)": "IJ G conc 240°/s", "IJ Conc 240° (D)": "IJ Dt conc 240°/s",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s", "IJ Exc 30° (D)": "IJ Dt exc 30°/s"
}

KEYWORD_MAPPING = {
    "Taille": ["taille", "height"], "Poids": ["poids", "weight"],
    "Masse Grasse Plis (mm)": ["masse grasse", "fat", "img"], "Age":["age", "âge"],
    "Numéro": ["numero", "numéro", "number", "maillot"],
    "Poste": ["poste", "position"], "Latéralité": ["latéralité", "laterality", "pied"],
    "Knee To Wall (D)": ["knee to wall d", "ktw d"],
    "Sit And Reach": ["sit and reach", "souplesse"],
    "Adducteurs (G)": ["adducteur g", "add g"], "Adducteurs (D)": ["adducteur d", "add d"],
    "Abducteurs (G)": ["abducteur g", "abd g"], "Abducteurs (D)": ["abducteur d", "abd d"],
    "Nordic Ischio (G)": ["nordic g"], "Nordic Ischio (D)": ["nordic d"],
    "Inverseur (G)": ["inverseur g"], "Inverseur (D)": ["inverseur d"],
    "Everseur (G)": ["everseur g"], "Everseur (D)": ["everseur d"],
    "Endurance Heel Raise (G)": ["endurance heel raise g"], "Endurance Heel Raise (D)": ["endurance heel raise d"],
    
    "Q Conc 60° (G)": ["q g conc 60"], "Q Conc 60° (D)": ["q dt conc 60"],
    "Q Conc 240° (G)": ["q g conc 240"], "Q Conc 240° (D)": ["q dt conc 240"],
    "IJ Conc 60° (G)": ["ij g conc 60"], "IJ Conc 60° (D)": ["ij dt conc 60"],
    "IJ Conc 240° (G)": ["ij g conc 240"], "IJ Conc 240° (D)": ["ij dt conc 240"],
    "IJ Exc 30° (G)": ["ij g exc 30"], "IJ Exc 30° (D)": ["ij dt exc 30"],
    "Ratio Mixte (G)": ["ratio mixte g", "mixte g"],
    "Ratio Mixte (D)": ["ratio mixte dt", "mixte d", "mixte dt", "ratio mixte d"],
    
    # ---- SAUTS (Mise à jour) ----
    "CMJ 2JB": ["cmj 2jb", "cmj"], 
    "Drop jump": ["drop jump"],
    "Peak Force CMJ": ["peak force cmj", "force max cmj", "pic de force max (n)"],
    "RFD CMJ": ["rfd cmj", "pic de rfd max (n/s)"],
    "RSI CMJ": ["rsi cmj", "mrsi", "mrsi (jh/ct) (m/s)"],
    # -----------------------------
    
    "Wattbike (6s)": ["wattbike"], "Squat belt (N)": ["squat belt", "squat"],
    "VMA": ["vma"], "SV1": ["sv1"], "SV2": ["sv2"], "FC": ["fc"],
    "Temps sur 10m": ["temps sur 10m", "chrono 10m", "10m"],
    "Distance Totale": ["distance totale", "total dist"], "Distance HSR": ["distance hsr", "hsr"],
    "Distance Sprint (92% Vimax)" : ["distance sprint", "sprint"],
    "Nb Accélérations": ["nb acc"], "Nb Décélérations": ["nb dec"],
    "Vmax": ["vmax"], "Amax": ["amax"], "Dmax": ["dmax"]
}

REL_COL_MAPPING = {
    "Somme ADD": "Somme ADD (N/kg)", "Somme ABD": "Somme ABD (N/kg)",
    "Adducteurs (G)": "Adducteur G (N/kg)", "Adducteurs (D)": "Adducteur D (N/kg)",
    "Abducteurs (G)": "Abducteur G (N/kg)", "Abducteurs (D)": "Abducteur D (N/kg)",
    "Nordic Ischio (G)": "Nordic G (N/kg)", "Nordic Ischio (D)": "Nordic D (N/kg)",
    
    "Q Conc 60° (G)": "Q G conc 60°/s (N/kg)", "Q Conc 60° (D)": "Q Dt conc 60°/s (N/kg)",
    "Q Conc 240° (G)": "Q G conc 240°/s (N/kg)", "Q Conc 240° (D)": "Q Dt conc 240°/s (N/kg)",
    "IJ Conc 60° (G)": "IJ G conc 60°/s (N/kg)", "IJ Conc 60° (D)": "IJ Dt conc 60°/s (N/kg)",
    "IJ Conc 240° (G)": "IJ G conc 240°/s (N/kg)", "IJ Conc 240° (D)": "IJ Dt conc 240°/s (N/kg)",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s (N/kg)", "IJ Exc 30° (D)": "IJ Dt exc 30°/s (N/kg)",
    "Q Exc 30° (G)": "Q G exc 30°/s (N/kg)", "Q Exc 30° (D)": "Q Dt exc 30°/s (N/kg)"
}

SOURCES_CONFIG = {
    "Q Conc 60°": "Scientifique", "Q Conc 240°": "Scientifique", 
    "IJ Conc 60°": "Scientifique", "IJ Conc 240°": "Scientifique", "IJ Exc 30°": "Scientifique"
}

KEYWORD_MAPPING = {
    "Taille": ["taille", "height"], "Poids": ["poids", "weight"],
    "Masse Grasse Plis (mm)": ["masse grasse", "fat", "img"], "Age":["age", "âge"],
    "Numéro": ["numero", "numéro", "number", "maillot"],
    "Poste": ["poste", "position"], "Latéralité": ["latéralité", "laterality", "pied"],
    "Knee To Wall (D)": ["knee to wall d", "ktw d"],
    "Sit And Reach": ["sit and reach", "souplesse"],
    "Adducteurs (G)": ["adducteur g", "add g"], "Adducteurs (D)": ["adducteur d", "add d"],
    "Abducteurs (G)": ["abducteur g", "abd g"], "Abducteurs (D)": ["abducteur d", "abd d"],
    "Nordic Ischio (G)": ["nordic g"], "Nordic Ischio (D)": ["nordic d"],
    "Inverseur (G)": ["inverseur g"], "Inverseur (D)": ["inverseur d"],
    "Everseur (G)": ["everseur g"], "Everseur (D)": ["everseur d"],
    "Endurance Heel Raise (G)": ["endurance heel raise g"], "Endurance Heel Raise (D)": ["endurance heel raise d"],
    
    
    "Q Conc 60° (G)": ["q g conc 60"], "Q Conc 60° (D)": ["q dt conc 60"],
    "Q Conc 240° (G)": ["q g conc 240"], "Q Conc 240° (D)": ["q dt conc 240"],
    "IJ Conc 60° (G)": ["ij g conc 60"], "IJ Conc 60° (D)": ["ij dt conc 60"],
    "IJ Conc 240° (G)": ["ij g conc 240"], "IJ Conc 240° (D)": ["ij dt conc 240"],
    "IJ Exc 30° (G)": ["ij g exc 30"], "IJ Exc 30° (D)": ["ij dt exc 30"],
    "Ratio Mixte (G)": ["ratio mixte g", "mixte g"],
    "Ratio Mixte (D)": ["ratio mixte dt", "mixte d", "mixte dt", "ratio mixte d"],
    
    # ---- SAUTS (Mise à jour) ----
    "CMJ 2JB": ["cmj 2jb", "cmj"], 
    "Drop jump": ["drop jump"],
    "Peak Force CMJ": ["peak force cmj", "force max cmj", "pic de force max (n)"],
    "RFD CMJ": ["rfd cmj", "pic de rfd max (n/s)"],
    "RSI CMJ": ["rsi cmj", "mrsi", "mrsi (jh/ct) (m/s)"],
    # -----------------------------
    
    "Wattbike (6s)": ["wattbike"], "Squat belt (N)": ["squat belt", "squat"],
    "VMA": ["vma"], "SV1": ["sv1"], "SV2": ["sv2"], "FC": ["fc"],
    "Temps sur 10m": ["temps sur 10m", "chrono 10m", "10m"],
    "Distance Totale": ["distance totale", "total dist"], "Distance HSR": ["distance hsr", "hsr"],
    "Distance Sprint (92% Vimax)" : ["distance sprint", "sprint"],
    "Nb Accélérations": ["nb acc"], "Nb Décélérations": ["nb dec"],
    "Vmax": ["vmax"], "Amax": ["amax"], "Dmax": ["dmax"]
}

TARGET_MEDIAN_TESTS = {
    "Wattbike (6s)": "Wattbike 6s (W)",
    "Peak Force CMJ": "Peak Force CMJ",
    "RFD CMJ": "RFD CMJ",
    "RSI CMJ": "RSI",
    "SV1": "SV1",
    "SV2": "SV2",
}

@st.cache_data
def load_injury_data():
    import os
    import pandas as pd
    import unicodedata
    try:
        if os.path.exists("Blessures.xlsx"):
            df = pd.read_excel("Blessures.xlsx")
        elif os.path.exists("Blessures.csv"):
            df = pd.read_csv("Blessures.csv", sep=None, engine="python")
        else:
            return pd.DataFrame(columns=["Joueur", "Localisation", "Detail", "Date", "Duree"])
        
        col_map = {}
        for c in df.columns:
            c_str = unicodedata.normalize('NFKD', str(c)).encode('ASCII', 'ignore').decode('utf-8').upper().strip()
            
            if c_str == '@' or c_str == 'JOUEUR': col_map[c] = 'Joueur'
            elif 'DATE' in c_str: col_map[c] = 'Date'
            elif 'DIAGNOSTIC' in c_str or 'DETAIL' in c_str: col_map[c] = 'Detail'
            elif 'DUREE' in c_str or 'ABS' in c_str or 'INDISPONIBILITE' in c_str: col_map[c] = 'Duree'
            elif 'LOCALISATION' in c_str: col_map[c] = 'Localisation'
        
        df = df.rename(columns=col_map)
        
        for req in ["Joueur", "Localisation", "Detail", "Date", "Duree"]:
            if req not in df.columns: df[req] = ""
        
        df["Joueur"] = df["Joueur"].astype(str).str.strip().str.lower()
        df["Localisation"] = df["Localisation"].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame(columns=["Joueur", "Localisation", "Detail", "Date", "Duree"])

@st.cache_data
def load_data_from_source(source):
    try:
        df = pd.read_excel(source, header=0)
        cols_lower = {str(c).lower().strip(): c for c in df.columns}
        target = next((cols_lower[k] for k in ['joueur', 'nom', 'name'] if k in cols_lower), None)
        if not target: return pd.DataFrame(), "Colonne 'Joueur' introuvable dans le fichier."
        df = df.dropna(subset=[target]).rename(columns={target: 'Joueur'})
        df['Joueur'] = df['Joueur'].astype(str).str.title().str.strip()
        return df, None
    except Exception as e: return pd.DataFrame(), str(e)

import unicodedata
import os
import re

def super_clean_name(name):
    """Nettoyeur extrême pour faire correspondre le nom du profilage et du CMJ"""
    if pd.isna(name): return ""
    clean = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('utf-8').lower()
    words = re.findall(r'[a-z]+', clean)
    words.sort() 
    return "".join(words)

@st.cache_data(ttl=2)
def load_cmj_master():
    if os.path.exists("CMJ20262027.csv"):
        try:
            # On lit le nouveau fichier consolidé
            df_cmj = pd.read_csv("CMJ20262027.csv", sep=";", encoding="utf-8-sig")
        except:
            try:
                df_cmj = pd.read_csv("CMJ20262027.csv", sep=";", encoding="latin1")
            except:
                return pd.DataFrame()
        df_cmj.columns = [str(c).strip() for c in df_cmj.columns]
        if 'Joueur' in df_cmj.columns:
            # On applique le nettoyeur sur la colonne Joueur
            df_cmj['Joueur_Code'] = df_cmj['Joueur'].apply(super_clean_name)
        return df_cmj
    return pd.DataFrame()

def check_has_cmj(p_name, df):
    if df.empty or 'Joueur_Code' not in df.columns: return False
    return super_clean_name(p_name) in df['Joueur_Code'].values

@st.dialog("Analyse Biomécanique du Saut (CMJ)", width="large")
def show_cmj_details(player_name, df_cmj):
    import plotly.graph_objects as go
    import pandas as pd
    import os
    import re
    
    st.markdown("""
    <style>
        div[role="dialog"] {
            width: 75vw !important;
            max-width: 1400px !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if df_cmj.empty or 'Joueur_Code' not in df_cmj.columns:
        st.warning("Fichier de données CMJ introuvable.")
        return

    def parse_val(v):
        if pd.isna(v) or str(v).strip().lower() in ['nan', 'na', 'none', '']: return 0.0
        try: return float(str(v).replace(",", ".").replace(" ", ""))
        except: return 0.0

    target_code = super_clean_name(player_name)
    row_cmj = df_cmj[df_cmj['Joueur_Code'] == target_code]
    
    if row_cmj.empty:
        st.error(f"Aucune donnée trouvée pour {player_name}.")
        return

    rc = row_cmj.iloc[0]

    def get_cmj_pct(col, val):
        if val == 0: return 0
        s = pd.to_numeric(df_cmj[col], errors='coerce').dropna()
        if s.empty: return 0
        # Correction du calcul du percentile : on veut savoir combien sont en-dessous de lui
        return (s <= val).mean() * 100

    # --- 1. EXTRACTION DES KPIs ---
    metrics = {
        "Force Max (N)": {"col": "Pic de Force Max (N)", "val": parse_val(rc.get("Pic de Force Max (N)"))},
        "Puissance Max (W)": {"col": "Pic de Puissance Max (W)", "val": parse_val(rc.get("Pic de Puissance Max (W)"))},
        "mRSI": {"col": "mRSI (JH/CT) (m/s)", "val": parse_val(rc.get("mRSI (JH/CT) (m/s)"))},
        "RFD Poussée (N/s)": {"col": "Pic de RFD Max (N/s)", "val": parse_val(rc.get("Pic de RFD Max (N/s)"))},
        "RFD Freinage (N/s)": {"col": "Phase de Freinage - RFD Excentrique (N/s)", "val": parse_val(rc.get("Phase de Freinage - RFD Excentrique (N/s)"))},
        "Hauteur (cm)": {"col": "Hauteur de Saut TV (cm)", "val": parse_val(rc.get("Hauteur de Saut TV (cm)"))}
    }

    for k, v in metrics.items():
        v["pct"] = get_cmj_pct(v["col"], v["val"])

    st.markdown(f"<h3 style='color:#D71920; text-align:center; margin-bottom:15px; text-transform:uppercase;'>{player_name} - PROFIL CMJ</h3>", unsafe_allow_html=True)
    
    # --- 2. AFFICHAGE DES CARTES (KPIs) VIA ST.COLUMNS ---
    cols_kpi = st.columns(6) # 6 colonnes pour les 6 indicateurs
    
    for idx, (label, data) in enumerate(metrics.items()):
        val = data["val"]
        pct = data["pct"]
        # Inversion logique du classement (100% = Top 1%, 0% = Top 100%)
        rank = max(1, 100 - int(pct)) 
        
        c_bar = "#D71920" if pct < 33 else "#F39C12" if pct < 66 else "#27AE60" if pct < 95 else "#00E5FF"
        
        # Formatage intelligent
        val_str = f"{val:.1f}" if val < 100 else f"{val:.0f}"
        if label == "mRSI": val_str = f"{val:.2f}"
        
        unit = label.split('(')[-1].replace(')','') if '(' in label else ""
        title = label.split(' (')[0]

        with cols_kpi[idx]:
            st.markdown(f"""
            <div style='background:#fff; border-radius:8px; padding:12px; border:1px solid #eee; border-top:4px solid {c_bar}; box-shadow:0 2px 5px rgba(0,0,0,0.02); margin-bottom: 20px;'>
                <div style='font-size:11px; color:#555; font-weight:900; text-transform:uppercase; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{title}</div>
                <div style='font-size:18px; font-weight:900; color:#111;'>{val_str} <span style='font-size:10px; color:#888;'>{unit}</span></div>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-top:8px; border-top:1px solid #f9f9f9; padding-top:5px;'>
                    <span style='font-size:9px; color:#aaa; font-weight:bold;'>CLASS.</span>
                    <span style='font-size:11px; font-weight:900; color:{c_bar};'>Top {rank}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([1, 1.8])
    
    # --- 3. RADAR CHART COMPARATIF ---
    with col_g1:
        st.markdown("<div style='text-align:center; font-weight:bold; font-size:14px; margin-bottom:5px; color:#333;'>Profil Comparatif vs Équipe (Percentiles)</div>", unsafe_allow_html=True)
        
        labels_radar = ["Force Max", "Puissance", "mRSI", "RFD Poussée", "RFD Freinage", "Hauteur"]
        vals_radar = [metrics["Force Max (N)"]["pct"], metrics["Puissance Max (W)"]["pct"], metrics["mRSI"]["pct"], metrics["RFD Poussée (N/s)"]["pct"], metrics["RFD Freinage (N/s)"]["pct"], metrics["Hauteur (cm)"]["pct"]]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[33]*6, theta=labels_radar, mode='lines', line_color='rgba(0,0,0,0)', fill='toself', fillcolor='rgba(215, 25, 32, 0.1)', hoverinfo='skip'))
        fig_radar.add_trace(go.Scatterpolar(r=[66]*6, theta=labels_radar, mode='lines', line_color='rgba(0,0,0,0)', fill='none', hoverinfo='skip'))
        fig_radar.add_trace(go.Scatterpolar(r=[100]*6, theta=labels_radar, mode='lines', line_color='rgba(0,0,0,0)', fill='tonext', fillcolor='rgba(39, 174, 96, 0.1)', hoverinfo='skip'))
        fig_radar.add_trace(go.Scatterpolar(r=vals_radar + [vals_radar[0]], theta=labels_radar + [labels_radar[0]], fill='toself', name=player_name, line=dict(color="#423D3D", width=2), marker=dict(size=6, color="#423D3D"), fillcolor='rgba(5, 5, 5, 0.4)'))
        
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickvals=[33, 66], ticktext=["", ""], gridcolor="#ccc"), angularaxis=dict(tickfont=dict(size=11, weight="bold"))), showlegend=False, height=350, margin=dict(l=40, r=40, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

    # --- 4. COURBE FORCE-TEMPS RÉELLE (1000 HZ) ---
    with col_g2:
        st.markdown("<div style='text-align:center; font-weight:bold; font-size:14px; margin-bottom:5px; color:#333;'>Courbe Réelle Force-Temps (1000 Hz)</div>", unsafe_allow_html=True)
        
        dossier_brut = "CMJ_Brut"
        fichier_brut_trouve = None

        if os.path.exists(dossier_brut):
            for f in os.listdir(dossier_brut):
                if f.endswith('.csv') and 'mouvement' in f.lower():
                    match = re.search(r"mouvement_(.*?)__", f)
                    if match:
                        raw_name = match.group(1).replace('_', ' ')
                        if super_clean_name(raw_name) == target_code:
                            fichier_brut_trouve = os.path.join(dossier_brut, f)
                            break

        if fichier_brut_trouve:
            try:
                with open(fichier_brut_trouve, 'r', encoding='utf-8') as f: lines = f.readlines()
            except UnicodeDecodeError:
                with open(fichier_brut_trouve, 'r', encoding='latin-1') as f: lines = f.readlines()

            raw_data_start = -1
            for i, line in enumerate(lines):
                if line.strip() == "Données brutes":
                    raw_data_start = i + 2 
                    break

            parsed_data = []
            if raw_data_start != -1:
                for i in range(raw_data_start + 1, len(lines)):
                    line_clean = lines[i].strip()
                    
                    # CORRECTION DU BUG : On arrête la lecture si on rencontre la fin du tableau
                    if line_clean == "" or "Données brutes du canal" in line_clean:
                        if len(parsed_data) > 0:
                            break
                            
                    parts = line_clean.split(',')
                    if len(parts) >= 5:
                        try:
                            parsed_data.append((float(parts[0]), float(parts[2]), float(parts[3]), float(parts[4])))
                        except ValueError: continue

                if parsed_data:
                    df_curve = pd.DataFrame(parsed_data, columns=['Time', 'Force_Tot', 'Force_G', 'Force_D'])
                    
                    # --- NOUVEAU FILTRE : Ne garder que les 5 secondes avant le saut ---
                    # 1. On trouve à quel moment a lieu le saut (pic de force max)
                    t_peak = df_curve.loc[df_curve['Force_Tot'].idxmax(), 'Time']
                    # 2. On coupe tout ce qui dépasse 5 secondes avant ce pic
                    df_curve = df_curve[df_curve['Time'] >= (t_peak - 5.0)]
                    
                    fig_ft = go.Figure()
                    
                    # --- LES 3 COURBES ---
                    # Jambe Gauche (Bleu SDR)
                    fig_ft.add_trace(go.Scatter(x=df_curve['Time'], y=df_curve['Force_G'], mode='lines', name='Gauche', line=dict(color='#1E3A8A', width=1.5), opacity=0.85))
                    # Jambe Droite (Gris)
                    fig_ft.add_trace(go.Scatter(x=df_curve['Time'], y=df_curve['Force_D'], mode='lines', name='Droite', line=dict(color='#888888', width=1.5), opacity=0.85))
                    # Force Totale Cumulée (Rouge SDR, plus épais)
                    fig_ft.add_trace(go.Scatter(x=df_curve['Time'], y=df_curve['Force_Tot'], mode='lines', name='Total Cumulé', line=dict(color='#D71920', width=2.5)))
                    
                    bw = parse_val(rc.get('Poids_de_corps_N', 0))
                    if bw > 0:
                        fig_ft.add_hline(y=bw, line_dash="dash", line_color="#555", annotation_text="Poids de Corps")

                    fig_ft.update_layout(
                        height=350, 
                        margin=dict(l=10, r=10, t=10, b=10), 
                        plot_bgcolor='rgba(0,0,0,0)', 
                        xaxis_title="Temps (s)", 
                        yaxis_title="Force (N)", 
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        hovermode="x unified"
                    )
                    fig_ft.update_xaxes(showgrid=True, gridcolor='#eee')
                    fig_ft.update_yaxes(showgrid=True, gridcolor='#eee')
                    
                    st.plotly_chart(fig_ft, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Données brutes illisibles ou manquantes dans le fichier.")
        else:
            st.info(f"Courbe indisponible : Le fichier source de {player_name} doit être placé dans '{dossier_brut}' pour tracer le signal à 1000 Hz.")
@st.cache_data
def load_all_data():
    possible_files = ["Profilage 2026-2027.xlsx", "Profilage 2026-2027.csv"]
    found_file = None
    for f in possible_files:
        if os.path.exists(f):
            found_file = f
            break
    if not found_file: return pd.DataFrame(), "Fichier introuvable"
    return load_data_from_source(found_file)
    
def generate_heatmap_body_svg(injury_counts):
    img_filename = "anatomie_corps.png"
    if not os.path.exists(img_filename) and os.path.exists("anatomie_corps.jpg"):
        img_filename = "anatomie_corps.jpg"
        
    svg_w, svg_h = 600, 600 
    
    try:
        with open(img_filename, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        ext = "jpeg" if "jpg" in img_filename else "png"
        bg_html = f'<image href="data:image/{ext};base64,{img_b64}" width="{svg_w}" height="{svg_h}" x="0" y="0" preserveAspectRatio="xMidYMid meet" />'
    except Exception:
        bg_html = f'<rect width="{svg_w}" height="{svg_h}" fill="#f8f9fa" />'

    coords = {
        "Tête": (175, 45),
        "Épaule (G)": (234, 144), "Épaule (D)": (113, 144),
        "Lombaire / Dos": (420, 260), "Symphyse / Pubalgie": (175, 295),
        "Psoas (G)": (195, 290), "Psoas (D)": (150, 290),
        "Fessiers (G)": (390, 305), "Fessiers (D)": (440, 305),
        "Droit Fémoral (G)": (210, 350), "Droit Fémoral (D)": (140, 350),
        "Ischio-jambiers (G)": (385, 355), "Ischio-jambiers (D)": (446, 355),
        "Adducteurs (G)": (195, 330), "Adducteurs (D)": (155, 330),
        "LCA (G)": (202, 416), "LCA (D)": (146, 416),
        "LCP (G)": (385, 416), "LCP (D)": (446, 416),
        "LLI Genou (G)": (185, 416), "LLI Genou (D)": (165, 416),
        "LLE Genou (G)": (217, 416), "LLE Genou (D)": (131, 416),
        "Ménisque (G)": (202, 416), "Ménisque (D)": (146, 416),
        "Rotule / Cartilage (G)": (202, 416), "Rotule / Cartilage (D)": (146, 416),
        "Tendon Rotulien (G)": (202, 435), "Tendon Rotulien (D)": (146, 435),
        "Triceps Sural / Mollet (G)": (385, 480), "Triceps Sural / Mollet (D)": (446, 480),
        "Tendon d'Achille (G)": (400, 544), "Tendon d'Achille (D)": (445, 544),
        "LLE Cheville - Entorse (G)": (210, 535), "LLE Cheville - Entorse (D)": (140, 535),
        "Syndesmose (G)": (200, 530), "Syndesmose (D)": (150, 530),
        "5ème Métatarsien (G)": (210, 545), "5ème Métatarsien (D)": (140, 545),
        "Pied / Orteil (G)": (200, 539), "Pied / Orteil (D)": (150, 544),
        "Aponévrose Plantaire (G)": (400, 555), "Aponévrose Plantaire (D)": (445, 555)
    }

    markers = ""
    for inj, count in injury_counts.items():
        if inj in coords:
            x, y = coords[inj]
            markers += f'<circle cx="{x}" cy="{y}" r="16" fill="rgba(52, 152, 219, 0.4)" stroke="#3498DB" stroke-width="2"/>'
            if count > 1:
                markers += f'<circle cx="{x+10}" cy="{y-10}" r="8" fill="#D71920"/><text x="{x+10}" y="{y-6}" font-size="10" font-family="Arial" font-weight="bold" fill="white" text-anchor="middle">{count}</text>'
            else:
                markers += f'<circle cx="{x}" cy="{y}" r="4" fill="#3498DB"/>'

    svg_code = f"""
    <svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" style="background:#fff; border-radius:10px; border:1px solid #eee;">
        {bg_html}
        {markers}
    </svg>
    """
    svg_b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    return f'<div style="display:flex; justify-content:center;"><img src="data:image/svg+xml;base64,{svg_b64}" style="max-height:430px; width:auto; max-width:100%; object-fit:contain; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-radius:10px;"></div>'

def get_recommendations_v3(player_row, df_all):
    try:
        import os
        df_exos = None
        # Recherche robuste du fichier
        for f in os.listdir():
            if "Exercices_Renfo" in f and f.endswith((".csv", ".xlsx")):
                if f.endswith(".csv"): df_exos = pd.read_csv(f)
                else: df_exos = pd.read_excel(f)
                break
                
        if df_exos is None:
            return [], [], None
            
        liste_noms_exos = sorted(df_exos['Exercice'].dropna().unique().tolist())
        potential_recos = []
        
        # 1. Analyse des Déficits (Profilage Athlétique & Physiologique UNIQUEMENT)
        kpis_critiques = {
            "CMJ 2JB": "CMJ", "Vmax": "Vmax", "Squat belt (N)": "Squat",
            "Adducteurs (G)": "Adducteurs", "Nordic Ischio (G)": "Nordic"
        }
        
        for metric_ui, keyword in kpis_critiques.items():
            col = find_column_in_df(df_all, metric_ui)
            val = clean_numeric_value(player_row.get(col))
            if val is not None:
                _, pct = calculate_percentile(df_all, col, val)
                
                # Couleurs et niveaux selon priorité
                if pct < 33: 
                    niv, color = "PRIORITE FORTE", "#D71920" # Rouge
                elif pct < 66: 
                    niv, color = "PRIORITE MOYENNE", "#F39C12" # Orange
                else: 
                    niv, color = "PRIORITE FAIBLE", "#27AE60" # Vert
                
                score_priorite = 100 - pct
                matches = df_exos[df_exos['Cible (Variables du profilage)'].astype(str).str.contains(keyword, na=False, case=False)]
                
                # LIMITE À 2 EXERCICES MAX PAR TEST pour équilibrer la programmation
                for _, exo in matches.head(2).iterrows():
                    d_exo = exo.to_dict()
                    d_exo.update({'priorite_score': score_priorite, 'niveau': niv, 'couleur': color, 
                                 'pourquoi': f"Déficit sur le test {keyword} (Classé dans les {int(pct)}% les plus faibles)."})
                    potential_recos.append(d_exo)

        # La partie médicale (asymétrie, adducteurs, etc.) a été supprimée.

        if not potential_recos: return [], liste_noms_exos, df_exos

        # Tri et suppression des doublons
        df_recos = pd.DataFrame(potential_recos).sort_values('priorite_score', ascending=False)
        # On garde les 4 exercices les plus prioritaires au total
        top_recos = df_recos.drop_duplicates(subset=['Exercice']).head(4).to_dict('records')
        return top_recos, liste_noms_exos, df_exos
        
    except Exception:
        return [], [], None
    
def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

#données inversée
def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing', "Landing %"]
    return any(x in str(label).lower() for x in keywords)

def clean_numeric_value(val):
    if pd.isna(val) or val == "" or val == "-": return None
    try:
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '.')
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match: return float(match.group())
        return None
    except: return None


# calcul des percentiles (avec sécurité rajouté )
@st.cache_data
def get_column_stats(df, col_name):
    """Met en cache la série numérique et sa moyenne pour éviter de recalculer toute la colonne."""
    if col_name not in df.columns: 
        return None, 0
    valid_values = pd.to_numeric(df[col_name], errors='coerce').dropna()
    if valid_values.empty: 
        return None, 0
    return valid_values, valid_values.mean()

def calculate_percentile(df, col_name, value):
    if pd.isna(value): return 0, 0
    
    # Appel de la fonction mise en cache (instantané si déjà calculé)
    valid_values, mean_val = get_column_stats(df, col_name)
    if valid_values is None: return 0, 0
    
    if "Ratio Squeeze" in col_name:
        distances = abs(valid_values - 1.0)
        val_dist = abs(value - 1.0)
        percentile = (distances >= val_dist).mean() * 100
        return mean_val, percentile

    inverted = is_inverted(col_name)
    if inverted:
        percentile = (valid_values >= value).mean() * 100
    else:
        percentile = (valid_values <= value).mean() * 100
        
    return mean_val, percentile 

def calculate_rank_info(df, col_name, value):
    if col_name not in df.columns or pd.isna(value): return "-", "-"
    valid_data = pd.to_numeric(df[col_name], errors='coerce').dropna()
    if valid_data.empty: return "-", "-"
    inverted = is_inverted(col_name)
    ranked = valid_data.rank(method='min', ascending=inverted)
    try:
        matches = ranked[valid_data == float(value)]
        if not matches.empty:
            player_rank = int(matches.iloc[0])
            total = len(valid_data)
            return player_rank, total
        return "-", "-"
    except: return "-", "-"

# calcul des asymétries
def get_asymmetry(df_row, metric_label, df):
    if "(G)" not in metric_label: return None
    metric_label_d = metric_label.replace("(G)", "(D)")
    col_g = find_column_in_df(df, metric_label)
    col_d = find_column_in_df(df, metric_label_d)
    if not col_g or not col_d: return None
    val_g = clean_numeric_value(df_row.get(col_g))
    val_d = clean_numeric_value(df_row.get(col_d))
    if val_g is None or val_d is None: return None
    try:
        max_val = max(val_g, val_d)
        if max_val == 0: return 0
        diff = (abs(val_g - val_d) / max_val) * 100
        return diff
    except: return None

@st.cache_data
def get_cleaned_columns(columns_tuple):
    """Met en cache les noms de colonnes nettoyés pour éviter de recalculer à chaque KPI."""
    return [remove_accents(str(c)).lower().strip() for c in columns_tuple]

def find_column_in_df(df, label):
    keywords = KEYWORD_MAPPING.get(label, [])
    if not keywords: 
        return None
        
    keywords_clean = [remove_accents(k).lower().strip() for k in keywords]
    
    # On utilise un tuple car st.cache_data nécessite des arguments "hachables"
    df_cols_clean = get_cleaned_columns(tuple(df.columns))
    
    for k in keywords_clean:
        for idx, col_name in enumerate(df_cols_clean):
            if k in col_name: 
                return df.columns[idx]
    return None

# trouver le numéro (au cas ou ça change)
def find_number_column(df):
    cols_map = {remove_accents(str(c)).lower().strip(): c for c in df.columns}
    targets = ['numero', 'numéro', 'number', 'maillot', 'shirt', 'n°']
    for t in targets:
        if t in cols_map: return cols_map[t]
    for c_clean, c_original in cols_map.items():
        if c_clean.startswith("num") or c_clean == "n°": return c_original
    return None

def img_to_b64(img_path):
    try:
        with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

# ajout des photos des joueurs
def get_best_photo_path(player_name):
    folder = "Photos"
    if not os.path.exists(folder): return None
    
    files_map = {f.lower(): f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}
    
    clean_name = player_name.strip()
    parts = clean_name.split()
    
    candidates = []
    candidates.append(clean_name)
    
    if len(parts) > 1:
        inverted = f"{parts[-1]} {' '.join(parts[:-1])}"
        candidates.append(inverted)
        
        candidates.append(f"{' '.join(parts[1:])} {parts[0]}")

    extensions = [".jpg", ".png", ".jpeg"]
    
    for cand in candidates:
        for ext in extensions:
            target_key = f"{cand}{ext}".lower()
            if target_key in files_map:
                return os.path.join(folder, files_map[target_key])
            
    return None



def create_radar_chart(categories, values, text_color="white"):
    if not categories: return ""
    N = len(categories)
    values_closed = values + values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.fill_between(angles, 0, 33, color='#D71920', alpha=0.15)
    ax.fill_between(angles, 66, 95, color='#27AE60', alpha=0.15)
    ax.fill_between(angles, 95, 100, color='#00E5FF', alpha=0.15)
    
    plt.xticks(angles[:-1], categories, color=text_color, size=9, weight='bold')
    ax.set_rlabel_position(0)
    
    grid_color = "#ccc" if text_color == "black" else "#555" 
    
    plt.yticks([33, 66, 100], ["33", "66", ""], color="#888", size=8)
    plt.ylim(0, 100)
    
    ax.yaxis.grid(True, color=grid_color, linestyle='dashed')
    ax.xaxis.grid(True, color=grid_color)
    ax.spines['polar'].set_color(grid_color)
    
    ax.plot(angles, values_closed, linewidth=2, linestyle='solid', color="#423D3D", marker='o', markersize=5)
    ax.fill(angles, values_closed, color="#050505", alpha=0.4)
    
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return img_b64

def create_multi_radar_chart(categories, values_l, values_r, values_norm, max_val=5.0):
    if not categories: return ""
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    # Fermeture des boucles
    v_l = values_l + values_l[:1]
    v_r = values_r + values_r[:1]
    v_n = values_norm + values_norm[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Axes et Grille
    plt.xticks(angles[:-1], categories, color='white', size=8, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4], ["1", "2", "3", "4"], color="#888", size=7)
    plt.ylim(0, max_val)
    
    ax.yaxis.grid(True, color="#444", linestyle='dashed')
    ax.xaxis.grid(True, color="#444")
    ax.spines['polar'].set_color('#444')
    ax.set_facecolor("none")
    fig.patch.set_alpha(0.0)
    
    ax.plot(angles, v_l, linewidth=2, linestyle='solid', color='#3498DB', label='Gauche')
    ax.fill(angles, v_l, color='#3498DB', alpha=0.1)
    
    ax.plot(angles, v_r, linewidth=2, linestyle='solid', color='#E74C3C', label='Droite')
    ax.fill(angles, v_r, color='#E74C3C', alpha=0.1)
    
    ax.plot(angles, v_n, linewidth=2, linestyle='--', color='#2ECC71', label='Obj.')
    
    # Légende
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1), fontsize=8, frameon=False, labelcolor='white')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64


def smart_format(val):
    if pd.isna(val) or val is None or val == "": return "-"
    try:
        val_float = float(val)
        if val_float == 0: return "0"
        if val_float % 1 == 0: return f"{int(val_float)}"
        return f"{val_float:.2f}"
    except: return "-"

def get_clean_label(label):
    return label.replace("(G)", "").replace("(D)", "").strip()

def get_unit(label):
    return UNITS.get(get_clean_label(label), "")

def get_col_name(label):
    return COL_MAPPING.get(label, label)

def get_rel_col_name(label):
    return REL_COL_MAPPING.get(label, None)

def get_source(label):
    return SOURCES_CONFIG.get(get_clean_label(label), "Club")

def get_norm_text(label):
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    if not found_key: return "-"
    
    norm_val = REPORT_NORMES[found_key]
    suffix = f" {get_unit(label)}"
    
    if isinstance(norm_val, (list, tuple)):
        low, high = norm_val
        if is_inverted(label):
            return f"Obj: < {smart_format(low)}{suffix}"
        else:
            return f"Obj: {smart_format(low)} - {smart_format(high)}{suffix}"
    else:
        if is_inverted(label):
            return f"Obj: < {smart_format(norm_val)}{suffix}"
        else:
            return f"Obj: {smart_format(norm_val)}{suffix}"

def get_bar_color(pct):
    if pct < 33: return "#D71920"
    if pct < 66: return "#F39C12"
    if pct < 95: return "#27AE60"
    return "#2DC4F6"

def get_status_data_local(label, value):
    val = clean_numeric_value(value)
    if val is None: return "#888", "-", "#888" 
    
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    
    if "Ratio Squeeze" in col_clean:
        if 0.90 <= val <= 1.10:
            return "#27AE60", "🟢", "#27AE60"
        else:
            return "#D71920", "🔴", "#D71920"

    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    
    if not found_key: return "#444444", "-", "#111111"
    
    norm_val = REPORT_NORMES[found_key]
    c_bad, c_avg, c_good = "#D71920", "#F39C12", "#27AE60"
    
    if isinstance(norm_val, (list, tuple)):
        low, high = norm_val
        if is_inverted(label):
            if val < low: return c_good, "Bon", c_good
            elif val <= high: return c_avg, "Moyen", c_avg
            else: return c_bad, "Mauvais", c_bad
        else:
            if val < low: return c_bad, "Mauvais", c_bad
            elif val < high: return c_avg, "Moyen", c_avg
            else: return c_good, "Bon", c_good
    else:
        if is_inverted(label):
            if val <= norm_val: return c_good, "🟢", c_good
            else: return c_bad, "🔴", c_bad
        else:
            if val >= norm_val: return c_good, "🟢", c_good
            else: return c_bad, "🔴", c_bad

def get_rel_display_smart(row_data, label_name, abs_val, p_poids):
    rel_col = get_rel_col_name(label_name)
    
    if rel_col and rel_col in row_data:
        val = clean_numeric_value(row_data[rel_col])
        if val: 
             u = "W/kg" if ("W/kg" in rel_col or "Watt" in label_name or "couché (W)" in label_name) else "N/kg"
             return f"{val:.2f} {u}"
    
    if p_poids and p_poids > 0 and abs_val is not None:
        unit_abs = get_unit(label_name)
        if unit_abs == "N": return f"{(abs_val/p_poids):.2f} N/kg"
        elif unit_abs == "W" or "Watt" in label_name: return f"{(abs_val/p_poids):.2f} W/kg"
        
    return None

def get_tooltip_html(row, label):
    rel_col = get_rel_col_name(label)
    if rel_col and rel_col in row:
        val_rel = clean_numeric_value(row[rel_col])
        if val_rel is not None:
            unit_rel = "N/kg" if ("N/kg" in rel_col or "Abducteurs - Droite" == rel_col) else "W/kg" if "W/kg" in rel_col else ""
            return f"title='Relatif: {val_rel:.2f} {unit_rel}'"
    return ""

def get_asym_badge_info(val_l, val_r, df_data, col_l, col_r):
    if val_l is None or val_r is None: return None, None
    
    if "Knee" in col_l or "KTW" in col_l:
         max_l = pd.to_numeric(df_data[col_l], errors='coerce').max()
         max_r = pd.to_numeric(df_data[col_r], errors='coerce').max()
         ref = max(max_l, max_r) if (pd.notna(max_l) and pd.notna(max_r)) else 0
         if ref == 0: return 0, ""
         pct = (abs(val_l - val_r) / ref) * 100
    else:
         if max(val_l, val_r) == 0: return 0, ""
         pct = (abs(val_l - val_r) / max(val_l, val_r)) * 100
         
    side = "G" if val_l < val_r else "D"
    return pct, side


def inject_custom_css():
    st.markdown(f"""
    <style>
        /* Titres de section principaux en Rouge */
        .section-header {{ font-size: 20px; font-weight: 900; color: {SDR_RED}; margin-top: 30px; margin-bottom: 15px; padding-left: 12px; border-left: 6px solid {SDR_RED}; border-bottom: 2px solid #eee; padding-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .kpi-card {{ background-color: #ffffff; border-radius: 8px; padding: 15px; margin-bottom: 15px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eee; transition: transform 0.2s; }}
        .kpi-card:hover {{ transform: translateY(-2px); border-color: {SDR_RED}; box-shadow: 0 4px 12px rgba(215,25,32,0.15); }}
        .kpi-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }}
        .kpi-val {{ font-size: 24px; font-weight: 900; color: #111; margin: 5px 0; }}
        .progress-bg {{ background-color: #f0f0f0; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px; }}
        .progress-fill {{ height: 100%; border-radius: 3px; }}
        .kpi-footer {{ display: flex; justify-content: space-between; font-size: 10px; color: #666; margin-top: 4px; }}
        
        /* EN-TÊTE DU JOUEUR (HERO) AVEC FORT CONTRASTE ROUGE */
        .hero-container {{ background: #ffffff; border-top: 4px solid {SDR_RED}; border-bottom: 4px solid {SDR_RED}; padding: 25px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 20px rgba(215,25,32,0.08); margin-bottom: 25px; }}
        .hero-left {{ display: flex; align-items: center; gap: 25px; }}
        .hero-photo {{ width: 120px; height: 120px; border-radius: 12px; border: 4px solid {SDR_RED}; object-fit: cover; box-shadow: 0 4px 10px rgba(215,25,32,0.2); background: #fff; }}
        .hero-details {{ display: flex; flex-direction: column; }}
        
        /* Nom en rouge massif */
        .hero-name {{ font-size: 42px; font-weight: 900; color: {SDR_RED}; text-transform: uppercase; line-height: 1; margin-bottom: 6px; text-shadow: 1px 1px 0px rgba(0,0,0,0.05); }}
        /* Numéro en badge rouge */
        .hero-number {{ display: inline-block; background-color: {SDR_RED}; color: #ffffff; padding: 2px 10px; border-radius: 4px; font-size: 18px; font-weight: 900; margin-bottom: 8px; width: max-content; }}
        .hero-meta {{ font-size: 16px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px; }}
        
        /* Séparation et Infos de droite */
        .hero-right {{ display: flex; gap: 40px; padding-right: 20px; border-left: 2px dashed #eee; padding-left: 40px; }}
        .stat-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .stat-label {{ font-size: 12px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
        /* Valeurs (Âge, Taille, Poids) en Rouge */
        .stat-value {{ font-size: 32px; font-weight: 900; color: {SDR_RED}; }}
    </style>""", unsafe_allow_html=True)

def load_data_from_source(source):
    """Charge les données depuis un fichier (str path) ou un objet file uploadé."""
    try:
        df = pd.read_excel(source, header=0)
        cols_lower = {str(c).lower().strip(): c for c in df.columns}
        target = next((cols_lower[k] for k in ['joueur', 'nom', 'name'] if k in cols_lower), None)
        if not target: return pd.DataFrame(), "Colonne 'Joueur' introuvable dans le fichier."
        df = df.dropna(subset=[target]).rename(columns={target: 'Joueur'})
        df['Joueur'] = df['Joueur'].astype(str).str.title().str.strip()
        return df, None
    except Exception as e: return pd.DataFrame(), str(e)

def load_all_data():
    """Charge le fichier par défaut si aucun upload n'est fait."""
    possible_files = ["Profilage pratiquexlsx.xlsx", "Profilage.xlsx"]
    found_file = None
    for f in possible_files:
        if os.path.exists(f):
            found_file = f
            break
    if not found_file: return pd.DataFrame(), "Fichier introuvable"
    return load_data_from_source(found_file)


def format_pct_display(pct):
    import pandas as pd
    if pct is None or pd.isna(pct): return ""
    try:
        val = int(pct)
        if val >= 66: return f"Top {max(1, 100 - val)}%"
        elif val >= 33: return "Moyen"
        else: return f"Flop {max(1, val)}%"
    except:
        return ""



def show_profiling_page(df_main=None):
    inject_custom_css()
    
    st.markdown("""<div style='position:absolute; top:-50px; left:0; font-size:10px; color:#888; font-weight:bold;'>Antoine Kaczmarek - DEPARTEMENT PERFORMANCE - STADE DE REIMS</div>""", unsafe_allow_html=True)

    import base64

    logo_sdr_tag = ""
    logo_dept_tag = ""

    # --- LOGO SDR ---
    if os.path.exists("logo_sdr.png"):
        with open("logo_sdr.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # Hauteur augmentée pour le milieu
        logo_sdr_tag = "<img src='data:image/png;base64," + b64 + "' style='height:280px; object-fit:contain;'/>"

    # --- LOGO DEPARTEMENT PERF ---
    nom_fichier_perf = "Departement Perf.png" 
    if os.path.exists(nom_fichier_perf):
        with open(nom_fichier_perf, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # Hauteur augmentée pour la gauche
        logo_dept_tag = "<img src='data:image/png;base64," + b64 + "' style='height:100px; object-fit:contain;'/>"

    header_html = (
        "<div style='display:flex; align-items:center; justify-content:space-between; width:100%; padding:15px 0; border-bottom: 3px solid " + SDR_RED + "; margin-bottom: 20px;'>"
            
            # 1. GAUCHE : Logo Dept Perf
            "<div style='flex: 1; display:flex; justify-content:flex-start;'>"
                + logo_dept_tag +
            "</div>"
            
            # 2. MILIEU : Logo SDR
            "<div style='flex: 1; display:flex; justify-content:center;'>"
                + logo_sdr_tag +
            "</div>"
            
            # 3. DROITE : Profilage
            "<div style='flex: 1; display:flex; flex-direction:column; align-items:flex-end; gap:2px;'>"
                "<span style='font-size:60px; font-weight:900; color:" + SDR_RED + "; text-transform:uppercase; letter-spacing:3px; line-height:1;'>PROFILAGE</span>"
                "<span style='font-size:20px; font-weight:600; color:#555; letter-spacing:2px;'>Saison 2026-2027</span>"
            "</div>"
            
        "</div>"
    )

    st.markdown(header_html, unsafe_allow_html=True)
    # Plus besoin du st.markdown("---") car je l'ai intégré directement dans le header via border-bottom

    if df_main is not None and not df_main.empty:
        df = df_main
    else:
        df, _ = load_all_data()

    if df.empty:
        return

    # 1. Filtre Global : On ne filtre QUE l'équipe ici
    if "Equipe" in df.columns:
        equipes = sorted(df["Equipe"].dropna().astype(str).unique())
        
        # On cherche l'index de "PRO", sinon on prend 0 par défaut
        default_index = equipes.index("PRO") if "PRO" in equipes else 0
        
        sel_equipe = st.selectbox("Equipe :", equipes, index=default_index)
        df = df[df["Equipe"].astype(str) == sel_equipe]

    # 2. Création des 3 onglets
    tab_indiv, tab_team, tab_comp, tab_evol, tab_cluster, tab_classement = st.tabs(["PROFIL INDIVIDUEL", "ANALYSE COLLECTIVE", "COMPARATEUR", "ÉVOLUTION LONGITUDINALE", "MACHINE LEARNING", "CLASSEMENT"])
    
    # -- ONGLET 1 : INDIVIDUEL --
    with tab_indiv:
        col_session = next((c for c in df.columns if 'session' in str(c).lower()), None)
        df_indiv = df.copy()
        if col_session:
            sel_session = st.selectbox("Session :", sorted(df_indiv[col_session].dropna().astype(str).unique()), key="sess_indiv")
            df_indiv = df_indiv[df_indiv[col_session].astype(str) == sel_session]

        all_players = sorted(df_indiv['Joueur'].dropna().unique())
        if not all_players: 
            st.warning("Aucun joueur trouvé pour cette session.")
            st.stop() # <-- Ceci arrête le code proprement et empêche le crash
            
        p_sel = st.selectbox("Joueur :", all_players, key="choix_joueur_indiv")
        row = df_indiv[df_indiv['Joueur'] == p_sel].iloc[0]
        
        poids_col_name = find_column_in_df(df_indiv, "Poids")
        poids_joueur = clean_numeric_value(row.get(poids_col_name))
            
        col_poste = find_column_in_df(df, "Poste")
            
        
        col_poste = find_column_in_df(df, "Poste")
        
        col_poste = find_column_in_df(df, "Poste")
        col_lat = find_column_in_df(df, "Latéralité")
        col_num = find_number_column(df)
        val_num = f"#{int(float(row[col_num]))}" if (col_num and col_num in row and pd.notna(row[col_num])) else ""
        val_poste = row.get("Position", "-")
        val_lat = row[col_lat] if col_lat else "-"

        anthro_vals = {}
        for label in ["Age","Taille", "Poids", "Masse Grasse Plis (mm)"]:
            col_name = find_column_in_df(df, label)
            val = clean_numeric_value(row.get(col_name))
            if label == "Age": unit = " ans"
            elif label == "Taille": unit = " cm"
            elif label == "Poids": unit = " kg"
            else: unit = " mm"
            
            if label == "Taille" and val is not None:
                anthro_vals[label] = f"{val:.1f}{unit}"
            else:
                anthro_vals[label] = f"{smart_format(val)}{unit}" if val else "-"
        
        use_relative = st.toggle("Afficher en valeurs Relatives (N/kg, W/kg)", key="use_relative_mode")
        photo_path = get_best_photo_path(p_sel) 
        img_src = f"data:image/png;base64,{img_to_b64(photo_path)}" if photo_path else ""
        img_html = f'<img src="{img_src}" class="hero-photo">' if img_src else '<div class="hero-photo" style="display:flex;align-items:center;justify-content:center;background:#222;color:#555;font-size:10px;">PHOTO</div>'
        
        st.markdown(f"""
<style>
.stat-box {{ white-space: nowrap; font-size: 0.9em; }}
</style>
<div class="hero-container">
<div class="hero-left">{img_html}<div class="hero-details"><div class="hero-name">{p_sel}</div><div class="hero-number">{val_num}</div><div class="hero-meta">{val_poste} | {val_lat}</div></div></div>
<div class="hero-right">
<div class="stat-box"><div class="stat-label">AGE</div><div class="stat-value">{anthro_vals['Age']}</div></div>
<div class="stat-box"><div class="stat-label">TAILLE</div><div class="stat-value">{anthro_vals['Taille']}</div></div>
<div class="stat-box"><div class="stat-label">POIDS</div><div class="stat-value">{anthro_vals['Poids']}</div></div>
<div class="stat-box"><div class="stat-label">Plis cutanés</div><div class="stat-value">{anthro_vals['Masse Grasse Plis (mm)']}</div></div>
</div>
</div>
""", unsafe_allow_html=True)
        
 

        # 1. Configuration
        radar_config = [
            {"label": "Vmax", "cols": ["Vmax"]},
            {"label": "Amax", "cols": ["Amax"]},
            {"label": "Dmax", "cols": ["Dmax"]},
            {"label": "Dist. Totale", "cols": ["Distance Totale"]},
            {"label": "Dist. HSR", "cols": ["Distance HSR"]},
            {"label": "Sprint (>92%)", "cols": ["Distance Sprint (92% Vimax)"]}
        ]
        
        # 2. Préparation des données
        row_updated = df[df['Joueur'] == p_sel].iloc[0]
        radar_labels = []
        radar_values = []
        table_rows_data = []

        for item in radar_config:
            radar_labels.append(item['label'])
            sum_p = 0
            count = 0
            
            val_str = "-"
            norm_str = ""
            actual_col_key = item['cols'][0] # On garde la vraie colonne par défaut
            
            for col_key in item['cols']:
                col_name = COL_MAPPING.get(col_key, col_key)
                val = clean_numeric_value(row_updated.get(col_name))
                
                if col_name and val is not None:
                    actual_col_key = col_key # On sauvegarde le VRAI nom trouvé
                    try:
                        _, p = calculate_percentile(df, col_name, val)
                        sum_p += p
                        count += 1
                        
                        unit = UNITS.get(col_key, "")
                        if val > 100: 
                            val_str = f"{int(val)} {unit}"
                        else: 
                            val_str = f"{val:.2f} {unit}"
                        
                        raw_norm = get_norm_text(col_key)
                        if raw_norm != "-":
                            norm_str = raw_norm
                            
                    except: pass
            
            final_score = sum_p / count if count > 0 else 0
            radar_values.append(final_score)
            
            table_rows_data.append({
                "label": item['label'], 
                "actual_col": actual_col_key, 
                "value_display": val_str,
                "norm_display": norm_str,
                "score": int(final_score)
            })

        # 3. Affichage
        c_radar, c_table = st.columns([3, 2])
        
        # ==========================================

        with c_radar:
            import plotly.graph_objects as go
            
            radar_hover_texts = []
            for r_data in table_rows_data:
                lbl = r_data['label']
                actual_lbl = r_data.get('actual_col', lbl) # On utilise le vrai nom
                val_fmt = r_data['value_display']
                norm_txt = r_data['norm_display'].replace('Obj: ', '') if r_data['norm_display'] and r_data['norm_display'] != "()" else "-"
                
                score = r_data.get('score', 0)
                is_empty = score is None or pd.isna(score)
                
                if norm_txt == "-":
                    status_desc = "Pas d'objectif"
                    status_color = "#888"
                else:
                    col_abs = get_col_name(actual_lbl)
                    val_abs = clean_numeric_value(row.get(col_abs))
                    status_res = get_status_data_local(actual_lbl, val_abs)
                    c_stat = status_res[0] if len(status_res) > 0 else "#ccc"
                    if c_stat in ["#27AE60", "#00E5FF"]:
                        status_desc = "🟢"
                        status_color = "#27AE60"
                    else:
                        status_desc = "🔴"
                        status_color = "#D71920"
                
                pct_disp = format_pct_display(score) if not is_empty else "-"
                
                hover_html = (
                    f"<b>{lbl.upper()}</b><br><br>"
                    f"Valeur : <b>{val_fmt}</b><br>"
                    f"Objectif : {norm_txt}<br>"
                    f"Statut : <span style='color:{status_color}; font-weight:bold;'>{status_desc}</span><br>"
                    f"Classement : <b>{pct_disp}</b>"
                )
                radar_hover_texts.append(hover_html)
                
            if radar_labels:
                cats_closed = radar_labels + [radar_labels[0]]
                vals_closed = radar_values + [radar_values[0]]
                hover_closed = radar_hover_texts + [radar_hover_texts[0]]
                
                fig_main_radar = go.Figure()
                
                # Zone 0-33 (Rouge - Flop)
                fig_main_radar.add_trace(go.Scatterpolar(
                    r=[33] * len(cats_closed), theta=cats_closed,
                    mode='lines', line=dict(width=0),
                    fill='toself', fillcolor='rgba(215, 25, 32, 0.15)',
                    hoverinfo='skip', showlegend=False
                ))
                
                # Limite 33-66 (Moyen - Fond transparent)
                fig_main_radar.add_trace(go.Scatterpolar(
                    r=[66] * len(cats_closed), theta=cats_closed,
                    mode='lines', line=dict(width=0),
                    fill='none', hoverinfo='skip', showlegend=False
                ))
                
                # Zone 66-95 (Vert - Top)
                fig_main_radar.add_trace(go.Scatterpolar(
                    r=[95] * len(cats_closed), theta=cats_closed,
                    mode='lines', line=dict(width=0),
                    fill='tonext', fillcolor='rgba(39, 174, 96, 0.15)',
                    hoverinfo='skip', showlegend=False
                ))
                
                # Zone 95-100 (Bleu - Élite)
                fig_main_radar.add_trace(go.Scatterpolar(
                    r=[100] * len(cats_closed), theta=cats_closed,
                    mode='lines', line=dict(width=0),
                    fill='tonext', fillcolor='rgba(0, 229, 255, 0.15)',
                    hoverinfo='skip', showlegend=False
                ))

                # Données du joueur (Ligne et remplissage noir/gris)
                fig_main_radar.add_trace(go.Scatterpolar(
                    r=vals_closed,
                    theta=cats_closed,
                    fill='toself',
                    name="Profil",
                    mode='lines+markers',
                    line=dict(color="#423D3D", width=2),
                    marker=dict(size=6, color="#423D3D"),
                    fillcolor='rgba(5, 5, 5, 0.4)',
                    hoverinfo='text',
                    hovertext=hover_closed,
                    showlegend=False
                ))
                
                fig_main_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, 
                            range=[0, 100], 
                            tickvals=[33, 66, 100],
                            ticktext=["33", "66", ""],
                            tickfont=dict(color="#888", size=9),
                            gridcolor="#ccc", 
                            linecolor="#ccc",
                            layer="below traces"
                        ),
                        angularaxis=dict(
                            tickfont=dict(color="#111", size=11, weight="bold"), 
                            gridcolor="#ccc", 
                            linecolor="#ccc",
                            layer="below traces"
                        )
                    ),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=20, b=20),
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_main_radar, use_container_width=True, config={'displayModeBar': False})

        with c_table:
            st.markdown("""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding:0 5px; border-bottom:2px solid #eee; padding-bottom:5px;'>
                <span style='color:#555; font-size:12px; font-weight:bold; letter-spacing:1px;'>INDICATEURS CLÉS</span>
                <span style='color:#777; font-size:10px; display:flex; align-items:center;'>
                    SCORE (PERCENTILE) &nbsp;
                    <span title="Le score sur 100 représente le classement du joueur par rapport au reste du groupe." style="cursor:help; font-size:14px;">ℹ️</span>
                </span>
            </div>
            """, unsafe_allow_html=True)

            html_content = "<div style='display:flex; flex-direction:column; gap:10px; margin-bottom:20px; width: 100%;'>"
            
            for row_data in table_rows_data:
                label = row_data['label']
                actual_lbl = row_data.get('actual_col', label)
                score = row_data.get('score', None)
                
                if score is None or pd.isna(score):
                    pct_color = "#eee"
                    pct_html = "<div style='color:#888; font-weight:bold; font-size:12px;'>-</div>"
                else:
                    pct_color = "#00E5FF" if score >= 95 else "#27AE60" if score >= 66 else "#F39C12" if score >= 33 else "#D71920"
                    score_txt = format_pct_display(score)
                    pct_html = f"<div style='color:{pct_color}; font-weight:900; font-size:13px;'>{score_txt}</div>"
                
                val_disp = row_data.get('value_display', '-')
                norm_disp = row_data.get('norm_display', '-')
                
                if norm_disp in ["-", "()", ""]:
                    norm_color = "#eee"
                    status_text = "Pas d'objectif"
                    norm_tooltip = "Aucun objectif défini"
                else:
                    col_abs_name = get_col_name(actual_lbl)
                    val_abs_ref = clean_numeric_value(row.get(col_abs_name))
                    status_res = get_status_data_local(actual_lbl, val_abs_ref)
                    c_stat = status_res[0] if len(status_res) > 0 else "#111"
                    
                    if c_stat in ["#27AE60", "#00E5FF"]:
                        norm_color = "#27AE60"
                        status_text = "🟢"
                    else:
                        norm_color = "#D71920"
                        status_text = "🔴"
                    
                    norm_tooltip = norm_disp 

                val_color = "#111"
                

                html_content += (
                    f"<div style='width: 100%; background-color:#fff; border-radius:8px; padding:12px 15px; border:1px solid #eee; border-left:6px solid {norm_color}; border-right:6px solid {pct_color}; box-shadow: 0 2px 5px rgba(0,0,0,0.03); display:flex; align-items:center; justify-content:space-between;'>"
                    f"<div style='flex:1.2;'>"
                    f"<div style='color:#333; font-weight:900; font-size:13px; text-transform:uppercase;'>{label}</div>"
                    f"</div>"
                    f"<div style='flex:1; text-align:center;'>"
                    f"<div style='font-size:22px; font-weight:900; color:{val_color}; line-height:1;'>{val_disp}</div>"
                    f"</div>"
                    f"<div style='flex:1.8; display:flex; justify-content:space-between; border-left:1px solid #f0f0f0; padding-left:15px;'>"
                    f"<div style='text-align:left;'>"
                    f"<div style='font-size:9px; color:#aaa; font-weight:bold; text-transform:uppercase;'>Statut</div>"
                    f"<div style='font-size:11px; font-weight:bold; color:{norm_color}; cursor:help;' title='{norm_tooltip}'>{status_text} <span style='font-size:9px;'>ℹ️</span></div>"
                    f"</div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-size:9px; color:#aaa; font-weight:bold; text-transform:uppercase;'>Class.</div>"
                    f"{pct_html}"
                    f"</div>"
                    f"</div>"
                    f"</div>"
                )
            
            html_content += "</div>"
            st.markdown(html_content, unsafe_allow_html=True)

        use_relative = st.session_state.get("use_relative_mode", False)

        st.markdown("""
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #eee; margin-top: 20px; margin-bottom: 30px; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
            <div>
                <div style="font-weight: 900; color: #555; font-size: 11px; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px;"> Par rapport à l'Objectif</div>
                <div style="display: flex; gap: 15px; font-size: 13px; font-weight: bold;">
                    <span style="color: #27AE60;">🟢 Objectif Atteint</span>
                    <span style="color: #D71920;">🔴 Sous l'objectif</span>
                </div>
            </div>
            <div style="border-left: 2px dashed #ddd; padding-left: 20px;">
                <div style="font-weight: 900; color: #555; font-size: 11px; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px;"> Par rapport au Groupe (Classement)</div>
                <div style="display: flex; gap: 15px; font-size: 13px; font-weight: bold;">
                    <span style="color: #00E5FF;">🔵 Élite (Top 5%)</span>
                    <span style="color: #27AE60;">🟢 Bon (Top 34%)</span>
                    <span style="color: #F39C12;">🟠 Moyen (33-66%)</span>
                    <span style="color: #D71920;">🔴 Flop (< 33%)</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        def get_data_smart(label, use_rel_mode):
            """
            Récupère intelligemment les données (Absolues ou Relatives) pour un indicateur.
            Retourne : (Valeur, Colonne_utilisée_pour_percentile, Unité, Label_Secondaire, Mode)
            """
            col_abs = get_col_name(label)
            val_abs = clean_numeric_value(row.get(col_abs))
            unit_abs = get_unit(label)
            is_force_or_power = any(u in unit_abs for u in ["N", "W", "kg"]) and "cm" not in unit_abs and "s" not in unit_abs

            # MODE ABSOLU : Si le mode relatif est désactivé ou non applicable
            if not use_rel_mode or not is_force_or_power or val_abs is None:
                _, pct = calculate_percentile(df, col_abs, val_abs)
                rel_txt = get_rel_display_smart(row, label, val_abs, poids_joueur)
                return val_abs, pct, unit_abs, rel_txt, "abs"

            # MODE RELATIF : Recherche de colonne dédiée ou calcul manuel
            potential_suffixes = [" (N/kg)", " (W/kg)", " N/kg", " W/kg", " (Relatif)", " Relatif"]
            col_rel = None
            
            # 1. Tentative de recherche de colonne pré-calculée
            for suff in potential_suffixes:
                candidate = col_abs + suff
                if candidate in df.columns:
                    col_rel = candidate
                    break
            
            if not col_rel and "(" in col_abs:
                base = col_abs.split("(")[0].strip()
                for suff in potential_suffixes:
                    candidate = base + suff
                    if candidate in df.columns:
                        col_rel = candidate
                        break

            # 2. Utilisation de la colonne relative trouvée
            if col_rel:
                val_rel = clean_numeric_value(row.get(col_rel))
                _, pct_rel = calculate_percentile(df, col_rel, val_rel)
                unit_rel = "N/kg" if "N" in unit_abs else "W/kg" if "W" in unit_abs else "ratio"
                sub_txt = f"{smart_format(val_abs)} {unit_abs}"
                return val_rel, pct_rel, unit_rel, sub_txt, "rel"

            # 3. Calcul manuel si aucune colonne relative n'est trouvée
            elif poids_joueur and poids_joueur > 0 and val_abs is not None:
                val_rel = val_abs / poids_joueur
                unit_rel = "N/kg" if "N" in unit_abs else "W/kg" if "W" in unit_abs else "ratio"
                col_poids_name = find_column_in_df(df, "Poids")
                
                if col_poids_name:
                    try:
                        # SÉCURITÉ : Forcer la conversion numérique pour éviter TypeError
                        series_perf = pd.to_numeric(df[col_abs], errors='coerce')
                        series_poids = pd.to_numeric(df[col_poids_name], errors='coerce')
                        
                        serie_rel = series_perf / series_poids.replace(0, np.nan)
                        
                        clean_series = serie_rel.dropna()
                        pct_rel = stats.percentileofscore(clean_series, val_rel, kind='weak')
                        
                        sub_txt = f"{smart_format(val_abs)} {unit_abs}"
                        return val_rel, pct_rel, unit_rel, sub_txt, "rel"
                    except Exception:
                        pass 

            # Repli sur le mode absolu si le calcul relatif échoue
            _, pct = calculate_percentile(df, col_abs, val_abs)
            return val_abs, pct, unit_abs, None, "abs"


        def render_single_kpi(label, subtitle=None):
            # 1. Extraction des données
            val, pct, unit, sub_text, mode = get_data_smart(label, use_relative)
            is_empty = val is None or pd.isna(val) or val == "" or str(val).strip() == "-"
            
            # 2. Initialisation des variables d'affichage
            unit_display = unit if not is_empty else ""
            pct_color = "#eee"
            pct_html = '<div style="font-size:13px; font-weight:900; color:#888;">-</div>'
            
            # 3. Logique de statut (Médiane vs Normes classiques)
            if is_empty:
                norm_color, status_text, norm_tooltip = "#eee", "Pas d'objectif", "Aucune donnée disponible"
            elif label in TARGET_MEDIAN_TESTS:
                col_name = TARGET_MEDIAN_TESTS[label]
                median_val = pd.to_numeric(df[col_name], errors='coerce').median()
                
                if not is_empty and val >= median_val:
                    # Pastille verte
                    norm_color = "#27AE60" 
                    status_text = "🟢"
                    norm_tooltip = f"Valeur: {val:.2f} | Médiane: {median_val:.2f}"
                else:
                    # Pastille rouge
                    norm_color = "#D71920" 
                    status_text = "🔴"
                    norm_tooltip = f"Valeur: {val:.2f} | Médiane: {median_val:.2f}"
            else:
                norm_txt_raw = get_norm_text(label).replace('Obj: ', '')
                status_res = get_status_data_local(label, clean_numeric_value(row.get(get_col_name(label))))
                norm_color = status_res[0] if len(status_res) > 0 else "#eee"
                status_text = "🟢" if norm_color == "#27AE60" else "🔴"
                norm_tooltip = f"Objectif : {norm_txt_raw}".strip()

            # 4. Calcul du percentile (barre de progression)
            if not is_empty and pct is not None and not pd.isna(pct):
                pct_color = get_bar_color(pct)
                pct_text = format_pct_display(pct)
                pct_html = f'<div style="font-size:13px; font-weight:900; color:{pct_color};">{pct_text}</div>'

            # 5. Préparation de l'affichage final
            val_display = f"{smart_format(val)}" if not is_empty else "-"
            sub_title_html = f" <span style='font-size:11px; color:#aaa; font-style:italic; text-transform:none;'>{subtitle}</span>" if subtitle else ""
            tip = get_tooltip_html(row, label)

            # 6. Génération HTML unique
            html_str = get_kpi_card_html(
                label=label, 
                val_display=val_display, 
                unit_display=unit_display, 
                norm_color=norm_color, 
                pct_color=pct_color, 
                pct_html=pct_html, 
                status_text=status_text, 
                norm_tooltip=norm_tooltip, 
                tip=tip, 
                subtitle_html=sub_title_html
            )
            st.markdown(html_str, unsafe_allow_html=True)

        def render_pair_kpi(l_label, r_label):
            clean_lbl = get_clean_label(l_label)
            found_key = next((k for k in REPORT_NORMES.keys() if k in clean_lbl), None)
            norm_val = REPORT_NORMES.get(found_key) if found_key else None
            
            force_relative = use_relative
            if norm_val is not None and isinstance(norm_val, (int, float)) and norm_val < 30:
                force_relative = True

            val_l, pct_l, unit_l, sub_l, _ = get_data_smart(l_label, force_relative)
            val_r, pct_r, unit_r, sub_r, _ = get_data_smart(r_label, force_relative)
            
            col_l_abs, col_r_abs = get_col_name(l_label), get_col_name(r_label)
            val_l_abs, val_r_abs = clean_numeric_value(row.get(col_l_abs)), clean_numeric_value(row.get(col_r_abs))
            asym_pct, weak_side = get_asym_badge_info(val_l_abs, val_r_abs, df, col_l_abs, col_r_abs)
            
            asym_html = ""
            if asym_pct is not None:
                if asym_pct < 10:
                    asym_html = f"<div style='background:rgba(39, 174, 96, 0.1); border:1px solid #27AE60; color:#27AE60; padding:4px 10px; border-radius:4px; font-size:11px; font-weight:bold;'>Équilibré ({asym_pct:.0f}%)</div>"
                elif 10 <= asym_pct < 15:
                    asym_html = f"<div style='background:rgba(243, 156, 18, 0.1); border:1px solid #F39C12; color:#F39C12; padding:4px 10px; border-radius:4px; font-size:11px; font-weight:bold;'>⚠ Déficit {weak_side} ({asym_pct:.0f}%)</div>"
                else:
                    asym_html = f"<div style='background:rgba(215, 25, 32, 0.1); border:1px solid #D71920; color:#D71920; padding:4px 10px; border-radius:4px; font-size:11px; font-weight:bold;'>🔴 Déficit {weak_side} ({asym_pct:.0f}%)</div>"

            def get_side_html(label, val, pct, unit, side_name, side_color):
                is_empty = val is None or pd.isna(val) or val == "" or str(val).strip() == "-"
                
                display_val = f"{smart_format(val)}" if not is_empty else "-"
                display_unit = unit if not is_empty else ""
                
                norm_txt_raw = "-"
                status_color = "#eee"
                
                if not is_empty:
                    norm_txt_raw = get_norm_text(label).replace('Obj: ', '')
                    status_res = get_status_data_local(label, val)
                    status_color = status_res[0] if len(status_res) > 0 else "#eee"
                        
                pct_color = get_bar_color(pct) if not is_empty and pct is not None else "#eee"
                pct_text = format_pct_display(pct) if not is_empty and pct is not None else "-"
                
                return (
                    f"<div style='flex:1; padding:10px; border-radius:8px; border:1px solid #eee; border-top:4px solid {side_color}; background:#fafafa; margin:0 5px;'>"
                    f"<div style='text-align:center; font-weight:900; color:{side_color}; margin-bottom:10px; font-size:14px;'>{side_name}</div>"
                    f"<div style='text-align:center; margin-bottom:15px;'>"
                    f"<div style='font-size:26px; font-weight:900; color:#111; line-height:1;'>{display_val} <span style='font-size:12px; color:#888;'>{display_unit}</span></div>"
                    f"</div>"
                    f"<div style='display:flex; justify-content:space-between; align-items:flex-end; border-top:1px solid #eee; padding-top:8px;'>"
                    f"<div style='text-align:left;'>"
                    f"<div style='font-size:9px; color:#aaa; text-transform:uppercase; font-weight:bold;'>Objectif</div>"
                    f"<div style='width:12px; height:12px; border-radius:50%; background:{status_color}; margin-top:2px;' title='{norm_txt_raw}'></div>"
                    f"</div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-size:9px; color:#aaa; text-transform:uppercase; font-weight:bold;'>Class.</div>"
                    f"<div style='font-size:12px; font-weight:900; color:{pct_color};'>{pct_text}</div>"
                    f"</div>"
                    f"</div>"
                    f"</div>"
                )

            clean_title = get_clean_label(l_label)
            html_str = (
                f"<div class='kpi-card' style='width: 100%; padding: 15px; margin-bottom: 20px; background: white; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:8px;'>"
                f"<div style='font-size:16px; font-weight:900; color:black; text-transform:uppercase;'>{clean_title}</div>"
                f"{asym_html}"
                f"</div>"
                f"<div style='display:flex; justify-content:space-between; margin:0 -5px;'>"
                f"{get_side_html(l_label, val_l, pct_l, unit_l, 'GAUCHE', '#3498db')}"
                f"{get_side_html(r_label, val_r, pct_r, unit_r, 'DROITE', '#e74c3c')}"
                f"</div>"
                f"</div>"
            )
            st.markdown(html_str, unsafe_allow_html=True)

        def render_muscle_group_card(title_main, l_label, r_label, sum_label):
            # 1. On récupère les données intelligentes une seule fois
            val_l, pct_l, unit_l, sub_l, _ = get_data_smart(l_label, use_relative)
            val_r, pct_r, unit_r, sub_r, _ = get_data_smart(r_label, use_relative)
            val_s, pct_s, unit_s, sub_s, _ = get_data_smart(sum_label, use_relative)

            # 2. On isole les noms de colonnes et les valeurs brutes (absolues) une seule fois
            col_l_abs = get_col_name(l_label)
            col_r_abs = get_col_name(r_label)
            val_l_abs = clean_numeric_value(row.get(col_l_abs))
            val_r_abs = clean_numeric_value(row.get(col_r_abs))
            val_s_abs = clean_numeric_value(row.get(get_col_name(sum_label)))

            # 3. Évaluation des statuts locaux (Couleurs)
            status_l = get_status_data_local(l_label, val_l_abs)
            status_r = get_status_data_local(r_label, val_r_abs)
            status_s = get_status_data_local(sum_label, val_s_abs)
            
            txt_l = status_l[2] if len(status_l) == 3 else "#111"
            txt_r = status_r[2] if len(status_r) == 3 else "#111"
            txt_s = status_s[2] if len(status_s) == 3 else "#111"
            
            # 4. Calcul de l'asymétrie
            norm_s = get_norm_text(sum_label).replace('Obj: ', '')
            asym_pct, weak_side = get_asym_badge_info(val_l_abs, val_r_abs, df, col_l_abs, col_r_abs)
            
            asym_html = ""
            if asym_pct is not None:
                if asym_pct < 10: 
                    asym_html = f"<div style='background:rgba(39, 174, 96, 0.1); border:1px solid #27AE60; color:#27AE60; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>Équilibré ({asym_pct:.0f}%)</div>"
                elif 10 <= asym_pct < 15: 
                    asym_html = f"<div style='background:rgba(243, 156, 18, 0.1); border:1px solid #F39C12; color:#F39C12; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>⚠ Attention {weak_side} ({asym_pct:.0f}%)</div>"
                else: 
                    asym_html = f"<div style='background:rgba(215, 25, 32, 0.1); border:1px solid #D71920; color:#D71920; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>Déficit {weak_side} ({asym_pct:.0f}%)</div>"

            # 5. Affichage HTML
            st.markdown(f"""
            <div class="kpi-card">
            <div class="kpi-lbl" style="font-size:16px; font-weight:900; color:{SDR_RED}; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:5px;">{title_main}</div>
            {asym_html}
            <div style="background:#f9f9f9; padding:10px; border-radius:8px; margin-bottom:12px; border:1px solid #eee;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <span style="color:#3498db; font-weight:900;">G</span>
            <span style="font-size:16px; font-weight:bold; color:{txt_l}">{smart_format(val_l)} <span style="font-size:10px; color:#888;">{unit_l}</span></span>
            <span style="font-size:10px; background:#fff; color:#555; border:1px solid #ddd; padding:2px 6px; border-radius:3px;">{sub_l if sub_l else '-'}</span>
            </div>
            <div class="progress-bg" style="margin-top:0; margin-bottom:8px;">
            <div style="width:{max(5, int(pct_l if pd.notna(pct_l) else 0))}%; height:100%; background:{get_bar_color(pct_l if pd.notna(pct_l) else 0)}; border-radius:3px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <span style="color:#e74c3c; font-weight:900;">D</span>
            <span style="font-size:16px; font-weight:bold; color:{txt_r}">{smart_format(val_r)} <span style="font-size:10px; color:#888;">{unit_r}</span></span>
            <span style="font-size:10px; background:#fff; color:#555; border:1px solid #ddd; padding:2px 6px; border-radius:3px;">{sub_r if sub_r else '-'}</span>
            </div>
            <div class="progress-bg" style="margin-top:0;">
            <div style="width:{max(5, int(pct_r if pd.notna(pct_r) else 0))}%; height:100%; background:{get_bar_color(pct_r if pd.notna(pct_r) else 0)}; border-radius:3px;"></div>
            </div>
            </div>
            <div style="margin-top:5px; border-top:1px dashed #ccc; padding-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:end; margin-bottom:5px;">
            <span style="font-size:12px; font-weight:bold; color:#555;">FORCE TOTALE</span>
            <div style="text-align:right; line-height:1.2;">
            <div style="font-size:20px; font-weight:900; color:{txt_s};">{smart_format(val_s)} <span style="font-size:12px; color:#888;">{unit_s}</span></div>
            <div style="font-size:11px; color:#777; font-weight:bold;">{sub_s if sub_s else '-'}</div>
            </div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
            <span style="font-size:11px; color:#666; font-weight:bold;">OBJECTIF: <span style="color:#111;">{norm_s}</span></span>
            <span style="font-size:11px; color:{get_bar_color(pct_s if pd.notna(pct_s) else 0)}; font-weight:bold;">Top {int(pct_s if pd.notna(pct_s) else 0)}%</span>
            </div>
            <div class="progress-bg" style="margin-top:0;">
            <div style="width:{max(5, int(pct_s if pd.notna(pct_s) else 0))}%; height:100%; background:{get_bar_color(pct_s if pd.notna(pct_s) else 0)}; border-radius:4px;"></div>
            </div>
            </div>
            </div>""", unsafe_allow_html=True)

        def render_wellness_combined():
            val_s = clean_numeric_value(row.get("Score Sommeil"))
            _, pct_s = calculate_percentile(df, "Score Sommeil", val_s)
            col_s = get_bar_color(pct_s)
            
            val_n = clean_numeric_value(row.get("Score Nutrition"))
            _, pct_n = calculate_percentile(df, "Score Nutrition", val_n)
            col_n = get_bar_color(pct_n)

            st.markdown(f"""
<div class="kpi-card" style="padding:20px; background:#fff; border-radius:10px; border:1px solid #eee; margin-bottom:20px;">
<div class="kpi-lbl" style="font-size:18px; font-weight:900; color:{SDR_RED}; text-transform:uppercase; margin-bottom:15px; border-bottom:2px solid #eee; padding-bottom:10px;">BIEN-ÊTRE & RÉCUPÉRATION</div>
<div style="display:flex; gap:30px;">
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">💤</span>
<div>
<div style="font-size:14px; color:#666; font-weight:bold;">SOMMEIL</div>
<div style="font-size:32px; font-weight:bold; color:#111; line-height:1;">{smart_format(val_s)}<span style="font-size:16px; color:#888;">/10</span></div>
</div>
</div>
<div class="progress-bg" style="height:12px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_s))}%; height:100%; background:{col_s}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_s};">Meilleur que {int(pct_s)}% de l'équipe</div>
</div>
<div style="width:1px; background:#eee;"></div>
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">🥦</span>
<div>
<div style="font-size:14px; color:#666; font-weight:bold;">NUTRITION</div>
<div style="font-size:32px; font-weight:bold; color:#111; line-height:1;">{smart_format(val_n)}<span style="font-size:16px; color:#888;">/12</span></div>
</div>
</div>
<div class="progress-bg" style="height:12px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_n))}%; height:100%; background:{col_n}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_n};">Meilleur que {int(pct_n)}% de l'équipe</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_subheader(title):
            st.markdown(f"<div style='color:{SDR_RED}; font-size:15px; font-weight:900; margin-top:20px; margin-bottom:10px; border-left:4px solid {SDR_RED}; padding-left:10px; text-transform:uppercase;'>{title}</div>", unsafe_allow_html=True)

        def render_muscle_group_card(title_main, l_label, r_label, sum_label):
            val_l, pct_l, unit_l, sub_l, _ = get_data_smart(l_label, use_relative)
            val_r, pct_r, unit_r, sub_r, _ = get_data_smart(r_label, use_relative)
            val_s, pct_s, unit_s, sub_s, _ = get_data_smart(sum_label, use_relative)

            txt_l = get_status_data_local(l_label, clean_numeric_value(row.get(get_col_name(l_label))))[2] if len(get_status_data_local(l_label, 0))==3 else "#111"
            txt_r = get_status_data_local(r_label, clean_numeric_value(row.get(get_col_name(r_label))))[2] if len(get_status_data_local(r_label, 0))==3 else "#111"
            txt_s = get_status_data_local(sum_label, clean_numeric_value(row.get(get_col_name(sum_label))))[2] if len(get_status_data_local(sum_label, 0))==3 else "#111"
            
            norm_s = get_norm_text(sum_label).replace('Obj: ', '')
            asym_pct, weak_side = get_asym_badge_info(clean_numeric_value(row.get(get_col_name(l_label))), clean_numeric_value(row.get(get_col_name(r_label))), df, get_col_name(l_label), get_col_name(r_label))
            
            asym_html = ""
            if asym_pct is not None:
                if asym_pct < 10: asym_html = f"<div style='background:rgba(39, 174, 96, 0.1); border:1px solid #27AE60; color:#27AE60; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>Équilibré ({asym_pct:.0f}%)</div>"
                elif 10 <= asym_pct < 15: asym_html = f"<div style='background:rgba(243, 156, 18, 0.1); border:1px solid #F39C12; color:#F39C12; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>⚠ Attention {weak_side} ({asym_pct:.0f}%)</div>"
                else: asym_html = f"<div style='background:rgba(215, 25, 32, 0.1); border:1px solid #D71920; color:#D71920; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>Déficit {weak_side} ({asym_pct:.0f}%)</div>"

            st.markdown(f"""
<div class="kpi-card">
<div class="kpi-lbl" style="font-size:16px; font-weight:bold; color:#333; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:5px;">{title_main}</div>
{asym_html}
<div style="background:#f9f9f9; padding:10px; border-radius:8px; margin-bottom:12px; border:1px solid #eee;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
<span style="color:#3498db; font-weight:900;">G</span>
<span style="font-size:16px; font-weight:bold; color:{txt_l}">{smart_format(val_l)} <span style="font-size:10px; color:#888;">{unit_l}</span></span>
<span style="font-size:10px; background:#fff; color:#555; border:1px solid #ddd; padding:2px 6px; border-radius:3px;">{sub_l if sub_l else '-'}</span>
</div>
<div class="progress-bg" style="margin-top:0; margin-bottom:8px;">
<div style="width:{max(5, int(pct_l))}%; height:100%; background:{get_bar_color(pct_l)}; border-radius:3px;"></div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
<span style="color:#e74c3c; font-weight:900;">D</span>
<span style="font-size:16px; font-weight:bold; color:{txt_r}">{smart_format(val_r)} <span style="font-size:10px; color:#888;">{unit_r}</span></span>
<span style="font-size:10px; background:#fff; color:#555; border:1px solid #ddd; padding:2px 6px; border-radius:3px;">{sub_r if sub_r else '-'}</span>
</div>
<div class="progress-bg" style="margin-top:0;">
<div style="width:{max(5, int(pct_r))}%; height:100%; background:{get_bar_color(pct_r)}; border-radius:3px;"></div>
</div>
</div>
<div style="margin-top:5px; border-top:1px dashed #ccc; padding-top:10px;">
<div style="display:flex; justify-content:space-between; align-items:end; margin-bottom:5px;">
<span style="font-size:12px; font-weight:bold; color:#555;">FORCE TOTALE</span>
<div style="text-align:right; line-height:1.2;">
<div style="font-size:20px; font-weight:900; color:{txt_s};">{smart_format(val_s)} <span style="font-size:12px; color:#888;">{unit_s}</span></div>
<div style="font-size:11px; color:#777; font-weight:bold;">{sub_s if sub_s else '-'}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:2px;">
<span style="font-size:11px; color:#666; font-weight:bold;">NORME: <span style="color:#111;">{norm_s}</span></span>
<span style="font-size:11px; color:{get_bar_color(pct_s)}; font-weight:bold;">Top {int(pct_s)}%</span>
</div>
<div class="progress-bg" style="margin-top:0;">
<div style="width:{max(5, int(pct_s))}%; height:100%; background:{get_bar_color(pct_s)}; border-radius:4px;"></div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_wellness_combined():
            val_s = clean_numeric_value(row.get("Score Sommeil"))
            _, pct_s = calculate_percentile(df, "Score Sommeil", val_s)
            col_s = get_bar_color(pct_s)
            
            val_n = clean_numeric_value(row.get("Score Nutrition"))
            _, pct_n = calculate_percentile(df, "Score Nutrition", val_n)
            col_n = get_bar_color(pct_n)

            st.markdown(f"""
<div class="kpi-card" style="padding:20px; background:#fff; border-radius:10px; border:1px solid #eee; margin-bottom:20px;">
<div class="kpi-lbl" style="font-size:18px; font-weight:bold; color:#111; text-transform:uppercase; margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:10px;">BIEN-ÊTRE & RÉCUPÉRATION</div>
<div style="display:flex; gap:30px;">
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">💤</span>
<div>
<div style="font-size:14px; color:#666; font-weight:bold;">SOMMEIL</div>
<div style="font-size:32px; font-weight:bold; color:#111; line-height:1;">{smart_format(val_s)}<span style="font-size:16px; color:#888;">/10</span></div>
</div>
</div>
<div class="progress-bg" style="height:12px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_s))}%; height:100%; background:{col_s}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_s};">Meilleur que {int(pct_s)}% de l'équipe</div>
</div>
<div style="width:1px; background:#eee;"></div>
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">🥦</span>
<div>
<div style="font-size:14px; color:#666; font-weight:bold;">NUTRITION</div>
<div style="font-size:32px; font-weight:bold; color:#111; line-height:1;">{smart_format(val_n)}<span style="font-size:16px; color:#888;">/12</span></div>
</div>
</div>
<div class="progress-bg" style="height:12px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_n))}%; height:100%; background:{col_n}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_n};">Meilleur que {int(pct_n)}% de l'équipe</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_subheader(title):
            st.markdown(f"<div style='color:#555; font-size:14px; font-weight:bold; margin-top:20px; margin-bottom:10px; border-left:3px solid #E74C3C; padding-left:10px;'>{title}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:30px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>HISTORIQUE & CARTOGRAPHIE MÉDICALE</div>", unsafe_allow_html=True)
        
        c_inj_sel, c_inj_vis = st.columns([1, 1])
        
        df_injuries = load_injury_data()
        p_sel_clean = str(p_sel).strip().lower()
        player_injuries = df_injuries[df_injuries['Joueur'] == p_sel_clean]
        
        if not player_injuries.empty:
            injury_counts = player_injuries['Localisation'].value_counts().to_dict()
            details_list = []
            html_injuries = ""
            for _, r in player_injuries.iterrows():
                date_str = str(r['Date'])[:10] if pd.notna(r['Date']) and str(r['Date']).strip() else '?'
                
                duree_val = str(r['Duree']).replace('.0', '').strip() if pd.notna(r['Duree']) else ''
                duree_html = ""
                duree_txt = ""
                
                if duree_val and duree_val.lower() not in ['nan', 'nat', 'none', '', '-']:
                    try:
                        d = float(duree_val)
                        if d <= 14: c_dur = "#27AE60"
                        elif d <= 30: c_dur = "#F39C12"
                        else: c_dur = "#D71920"
                        duree_html = f" <span style='color:{c_dur}; font-weight:900;'>({int(d)}j)</span>"
                    except:
                        duree_html = f" ({duree_val}j)"
                    duree_txt = f" ({duree_val}j)"
                    
                loc = str(r['Localisation']).strip()
                diag = str(r['Detail']).strip()
                
                details_list.append(f"📅 {date_str} | {loc}{duree_txt}\n↳ {diag}")
                html_injuries += f"<div style='margin-bottom:12px; border-bottom:1px dashed #eee; padding-bottom:8px;'><div style='font-size:13px;'><span style='color:#D71920; font-weight:bold;'>📅 {date_str}</span> | <span style='font-weight:bold; color:#333;'>{loc}</span>{duree_html}</div><div style='font-size:11px; color:#666; font-style:italic; margin-top:3px; padding-left:20px;'>↳ {diag}</div></div>"
                
            antecedents_auto = "\n\n".join(details_list)
        else:
            injury_counts = {}
            antecedents_auto = "Aucun antécédent répertorié."
            html_injuries = "<div style='color:#888; font-style:italic; text-align:center; padding-top:20px;'>Aucun antécédent répertorié.</div>"
            
        key_injuries = f"injuries_{p_sel}"
        key_ante = f"ante_{p_sel}"
        
        st.session_state[key_injuries] = injury_counts
        st.session_state[key_ante] = antecedents_auto

        with c_inj_sel:
            st.markdown("<div style='font-weight:bold; color:#444; margin-bottom:5px; text-transform:uppercase;'>Compte-rendu Clinique :</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='height:400px; overflow-y:auto; background:#fff; padding:15px; border-radius:8px; border:1px solid #eee; box-shadow:inset 0 2px 4px rgba(0,0,0,0.02);'>{html_injuries}</div>", unsafe_allow_html=True)

        
        with c_inj_vis:
            body_svg_code = generate_heatmap_body_svg(injury_counts)
            st.components.v1.html(body_svg_code, height=450)

        # PROFILAGE MOTEUR 
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:30px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>KINÉ</div>", unsafe_allow_html=True)

        render_subheader("MOBILITÉ")
        c_mob1, c_mob2 = st.columns(2)
        with c_mob1: render_single_kpi("Sit And Reach")
        with c_mob2: render_single_kpi("Knee To Wall (D)")

        render_subheader("ADDUCTEURS & ABDUCTEURS")
        c_add, c_sq, c_abd = st.columns([1.3, 0.7, 1.3])
        with c_add: render_muscle_group_card("ADDUCTEURS", "Adducteurs (G)", "Adducteurs (D)", "Somme ADD")
        with c_sq: 
            st.markdown("<br><br>", unsafe_allow_html=True)
            render_single_kpi("Ratio Squeeze")
        with c_abd: render_muscle_group_card("ABDUCTEURS", "Abducteurs (G)", "Abducteurs (D)", "Somme ABD")

        render_subheader("ISCHIO-JAMBIERS")
        render_pair_kpi("Nordic Ischio (G)", "Nordic Ischio (D)")
        
        render_subheader("MOLLETS")
        render_pair_kpi("Endurance Heel Raise (G)", "Endurance Heel Raise (D)")


        render_subheader("PIEDS")
        c_ped1, c_ped2 = st.columns(2)
        with c_ped1 : render_pair_kpi("Inverseur (G)", "Inverseur (D)")
        with c_ped2: render_pair_kpi("Everseur (G)", "Everseur (D)")
         

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom:15px; font-size:18px; font-weight:900; color:{SDR_RED}; border-bottom:2px solid {SDR_RED}; padding-bottom:5px; text-transform:uppercase;'>RADAR BIODEX (VALEURS RELATIVES)</div>", unsafe_allow_html=True)
        
        targets = {
            "Q 60°": 3.1,
            "Q 240°": 2.2,
            "IJ 60°": 1.8,
            "IJ 240°": 1.5,
            "IJ Exc 30°": 2.4
        }
        
        biodex_full_config = [
            {"label": "Q 60°", "g_rel": "Q G conc 60°/s (N/kg)", "d_rel": "Q Dt conc 60°/s (N/kg)", "g_raw": "Q G conc 60°/s", "d_raw": "Q Dt conc 60°/s"},
            {"label": "Q 240°", "g_rel": "Q G conc 240°/s (N/kg)", "d_rel": "Q Dt conc 240°/s (N/kg)", "g_raw": "Q G conc 240°/s", "d_raw": "Q Dt conc 240°/s"},
            {"label": "IJ 60°", "g_rel": "IJ G conc 60°/s (N/kg)", "d_rel": "IJ Dt conc 60°/s (N/kg)", "g_raw": "IJ G conc 60°/s", "d_raw": "IJ Dt conc 60°/s"},
            {"label": "IJ 240°", "g_rel": "IJ G conc 240°/s (N/kg)", "d_rel": "IJ Dt conc 240°/s (N/kg)", "g_raw": "IJ G conc 240°/s", "d_raw": "IJ Dt conc 240°/s"},
            {"label": "IJ Exc 30°", "g_rel": "IJ G Exc 30°/s (N/kg)", "d_rel": "IJ Dt exc 30°/s (N/kg)", "g_raw": "IJ G Exc 30°/s", "d_raw": "IJ Dt exc 30°/s"}
        ]

        radar_cats, vals_l_rel, vals_r_rel, vals_norm, table_data = [], [], [], [], []

        for item in biodex_full_config:
            lbl = item["label"]
            radar_cats.append(lbl)
            val_norm_rel = targets.get(lbl, 0)
            vals_norm.append(val_norm_rel)
            
            real_col_g_rel = find_column_in_df(df, item["g_rel"]) or item["g_rel"]
            real_col_d_rel = find_column_in_df(df, item["d_rel"]) or item["d_rel"]
            v_g_rel = clean_numeric_value(row.get(real_col_g_rel))
            v_d_rel = clean_numeric_value(row.get(real_col_d_rel))
            vals_l_rel.append(v_g_rel if v_g_rel is not None else 0)
            vals_r_rel.append(v_d_rel if v_d_rel is not None else 0)
            
            real_col_g_raw = find_column_in_df(df, item["g_raw"]) or item["g_raw"]
            real_col_d_raw = find_column_in_df(df, item["d_raw"]) or item["d_raw"]
            v_g_raw = clean_numeric_value(row.get(real_col_g_raw))
            v_d_raw = clean_numeric_value(row.get(real_col_d_raw))

            s_lsi, c_lsi = "-", "#888"
            if v_g_raw is not None and v_d_raw is not None:
                mx = max(v_g_raw, v_d_raw)
                if mx > 0:
                    lsi = ((v_d_raw - v_g_raw) / mx) * 100
                    s_lsi = f"{lsi:.0f}%"
                    c_lsi = "#D71920" if abs(lsi) > 10 else ("#F39C12" if abs(lsi) > 5 else "#27AE60")
            
            target_abs = f"{val_norm_rel * poids_joueur:.0f}" if poids_joueur and poids_joueur > 0 else "-"
            table_data.append({"label": lbl, "target": target_abs, "v_g": f"{v_g_raw:.0f}" if v_g_raw is not None else "-", "v_d": f"{v_d_raw:.0f}" if v_d_raw is not None else "-", "lsi": s_lsi, "c_lsi": c_lsi})

        col_radar, col_table = st.columns([1.2, 1]) 
        with col_radar:
            if not radar_cats:
                st.warning("Aucune donnée Biodex configurée trouvée.")
            else:
                import plotly.graph_objects as go
                max_data = max(max(vals_l_rel), max(vals_r_rel), max(vals_norm))
                limit_scale = max(4.0, max_data * 1.1)
                cats_closed = radar_cats + [radar_cats[0]]
                l_closed = vals_l_rel + [vals_l_rel[0]]
                r_closed = vals_r_rel + [vals_r_rel[0]]
                n_closed = vals_norm + [vals_norm[0]]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=n_closed, theta=cats_closed, fill='toself', name='Objectif', mode='lines', line=dict(color='#2ECC71', dash='dash', width=2), fillcolor='rgba(46, 204, 113, 0.1)', hoverinfo='skip'))
                fig.add_trace(go.Scatterpolar(r=l_closed, theta=cats_closed, name='Gauche', mode='lines+markers', fill='toself', line=dict(color='#1ABC9C', width=3), marker=dict(size=8, color='#1ABC9C', symbol='circle'), fillcolor='rgba(26, 188, 156, 0.15)', hoveron='points', hovertemplate='<b>Gauche</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'))
                fig.add_trace(go.Scatterpolar(r=r_closed, theta=cats_closed, name='Droite', mode='lines+markers', fill='toself', line=dict(color='#9B59B6', width=3), marker=dict(size=8, color='#9B59B6', symbol='circle'), fillcolor='rgba(155, 89, 182, 0.15)', hoveron='points', hovertemplate='<b>Droite</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, limit_scale], showticklabels=True, tickfont=dict(color="#555", size=9), gridcolor="#eee", linecolor="#eee", layer="below traces"), angularaxis=dict(tickfont=dict(color="#111", size=12, weight="bold"), gridcolor="#eee", linecolor="#eee", layer="below traces"), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=20, b=20), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(color="#111", size=12)), height=350, hovermode="closest")
                st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

        with col_table:
            st.markdown(f"<br><div style='text-align:center; font-size:15px; font-weight:900; color:{SDR_RED}; margin-bottom:10px; text-transform:uppercase;'>Résultats Détaillés (Nm)</div>", unsafe_allow_html=True)
            html_rows = ""
            for item in table_data:
                html_rows += f"<tr style='border-bottom:1px solid #eee;'><td style='padding:6px; color:#555;'>{item['label']}</td><td style='text-align:center; color:#888; font-weight:bold;'>{item['target']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_g']}</td><td style='text-align:center; color:#111; font-weight:bold;'>{item['v_d']}</td><td style='text-align:center; color:{item['c_lsi']}; font-weight:bold;'>{item['lsi']}</td></tr>"
            col_rm_g, col_rm_d = find_column_in_df(df, "Ratio Mixte G") or "Ratio Mixte G", find_column_in_df(df, "Ratio Mixte D") or "Ratio Mixte D"
            val_rm_g, val_rm_d = clean_numeric_value(row.get(col_rm_g)), clean_numeric_value(row.get(col_rm_d))

            def get_ratio_color(val):
                if val is None: return "#888"
                return "#D71920" if val < 0.8 else ("#F39C12" if val <= 1.0 else "#27AE60")

            s_rm_g = f"{val_rm_g:.2f}" if val_rm_g is not None else "-"
            s_rm_d = f"{val_rm_d:.2f}" if val_rm_d is not None else "-"
            html_rows += f"<tr style='border-top:2px solid #ccc; background-color:#f9f9f9;'><td style='padding:6px; font-weight:bold; color:#111;'>Ratio Mixte</td><td style='text-align:center;'>-</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_g)};'>{s_rm_g}</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_d)};'>{s_rm_d}</td><td style='text-align:center;'>-</td></tr>"
            st.markdown(f"<table style='width:100%; border-collapse:collapse; font-size:12px; font-family:sans-serif;'><tr style='background-color:#f0f0f0; color:#333; text-transform:uppercase; font-size:10px;'><th style='padding:8px; text-align:left;'>Test</th><th style='padding:8px; text-align:center;'>Obj. (Nm)</th><th style='padding:8px; text-align:center;'>G (Nm)</th><th style='padding:8px; text-align:center;'>D (Nm)</th><th style='padding:8px; text-align:center;'>LSI</th></tr>{html_rows}</table>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px; color:#666; font-style:italic; margin-top:5px;'>* L'objectif brut (Nm) est calculé en multipliant la norme relative (N/kg) par le poids du joueur.</div>", unsafe_allow_html=True)

        # ==========================================
        # SALLE
        # ==========================================
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:40px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>SALLE</div>", unsafe_allow_html=True)

        render_subheader("Counter Movement Jump")
        
        df_cmj_master = load_cmj_master()
        has_details = check_has_cmj(p_sel, df_cmj_master)
        
        c_cmj1, c_cmj2, c_cmj3, c_cmj4 = st.columns(4)
        with c_cmj1: render_single_kpi("CMJ 2JB")
        with c_cmj2: render_single_kpi("RSI CMJ")
        with c_cmj3: render_single_kpi("Peak Force CMJ")
        with c_cmj4: render_single_kpi("RFD CMJ")
        
        if has_details:
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                st.markdown("""
                <style>
                div.stButton > button:first-child {
                    background-color: #f9f9f9;
                    color: #D71920;
                    border: 2px solid #D71920;
                    border-radius: 8px;
                    font-weight: 900;
                }
                div.stButton > button:first-child:hover {
                    background-color: #D71920;
                    color: #ffffff;
                }
                </style>""", unsafe_allow_html=True)
                
                if st.button("📊 ANALYSE DÉTAILLÉE", key="btn_details_cmj", use_container_width=True):
                    show_cmj_details(p_sel, df_cmj_master)

        st.markdown("<hr style='border:1px dashed #eee; margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
        
        render_subheader("PUISSANCE & FORCE")
        c_sal5, c_sal6, c_sal7 = st.columns(3)
        with c_sal5: render_single_kpi("Drop jump")
        with c_sal6: render_single_kpi("Wattbike (6s)")
        with c_sal7: render_single_kpi("Squat belt (N)")
        # ==========================================
        # TERRAIN
        # ==========================================
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:40px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>TERRAIN</div>", unsafe_allow_html=True)

        render_subheader("PHYSIOLOGIE ET CARDIO")
        c_phy1, c_phy2 = st.columns(2)
        with c_phy1: render_single_kpi("VMA")
        with c_phy2: render_single_kpi("FC")
        
        c_phy3, c_phy4 = st.columns(2)
        with c_phy3: render_single_kpi("SV1")
        with c_phy4: render_single_kpi("SV2")
        
        parts = p_sel.split()
        if len(parts) >= 2:
            nom = parts[0].lower()
            prenom = " ".join(parts[1:]).lower()
        else:
            nom = p_sel.lower()
            prenom = ""

        dossier_cible_lower = f"{prenom} {nom}".strip()
        
        if prenom:
            prefixe_fichier_lower = f"sdr_{prenom.replace(' ', '_')}_{nom.replace(' ', '_')}"
        else:
            prefixe_fichier_lower = f"sdr_{nom.replace(' ', '_')}"

        dossier_racine = os.path.join(os.getcwd(), "TestsMetamax")
        pdf_path = None

        if os.path.exists(dossier_racine):
            for dossier in os.listdir(dossier_racine):
                if dossier.lower() == dossier_cible_lower:
                    chemin_dossier_joueur = os.path.join(dossier_racine, dossier)
                    if os.path.isdir(chemin_dossier_joueur):
                        for fichier in os.listdir(chemin_dossier_joueur):
                            f_lower = fichier.lower()
                            if f_lower.startswith(prefixe_fichier_lower) and "cap" in f_lower and f_lower.endswith(".pdf"):
                                pdf_path = os.path.join(chemin_dossier_joueur, fichier)
                                break
                    break

        if pdf_path:
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
            <style>
            .btn-metamax > button:first-child {
                background-color: #f0f8ff;
                color: #1E3A8A;
                border: 2px solid #1E3A8A;
                border-radius: 8px;
                font-weight: 900;
            }
            .btn-metamax > button:first-child:hover {
                background-color: #1E3A8A;
                color: #ffffff;
            }
            </style>""", unsafe_allow_html=True)
            
            st.markdown('<div class="btn-metamax">', unsafe_allow_html=True)
            
            # 1. On lit le fichier PDF en premier, de manière inconditionnelle
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            # 2. On place le bouton de téléchargement en dehors du "if st.button"
            # Ainsi, il est toujours visible, il connaît "pdf_bytes", et il ne plantera pas
            st.download_button(
                label="📥 Télécharger le PDF (Recommandé si l'affichage bug)", 
                data=pdf_bytes, 
                file_name=f"Rapport_Metamax_{p_sel.replace(' ', '_')}.pdf", 
                mime="application/pdf",
                use_container_width=True  # Tu peux mettre width="stretch" ici si tu veux enlever le message d'avertissement jaune dans tes logs
            )

            # 3. Le bouton d'affichage avec iframe au lieu de embed (mieux pour le Cloud)
            if st.button("🫁 AFFICHER LE RAPPORT PHYSIOLOGIQUE COMPLET (PACELAB)", key="btn_pdf_metamax", use_container_width=True):
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border:1px solid #ccc; border-radius:10px; margin-top:15px;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        render_subheader("ACCÉLÉRATION")
        render_single_kpi("Temps sur 10m")

        render_subheader("GPS")
        c_gps1, c_gps2, c_gps3 = st.columns(3)
        with c_gps1: render_single_kpi("Amax")
        with c_gps2: render_single_kpi("Dmax")
        with c_gps3: render_single_kpi("Vmax")
        
        c_gps4, c_gps5 = st.columns(2)
        with c_gps4: render_single_kpi("Nb Accélérations")
        with c_gps5: render_single_kpi("Nb Décélérations")

        c_gps6, c_gps7, c_gps8 = st.columns(3)
        with c_gps6: render_single_kpi("Distance HSR")
        with c_gps7: render_single_kpi("Distance Totale")
        with c_gps8: render_single_kpi("Distance Sprint (92% Vimax)")

        st.markdown("<br>", unsafe_allow_html=True) 


        def get_smart_recos(player_row, df_all):
            try:
                import os
                df_exos = None
                for f in os.listdir():
                    if "Exercices_Renfo" in f and f.endswith((".csv", ".xlsx")):
                        if f.endswith(".csv"): df_exos = pd.read_csv(f)
                        else: df_exos = pd.read_excel(f)
                        break
                        
                if df_exos is None:
                    return [], [], None
                    
                all_exos_list = df_exos['Exercice'].dropna().unique().tolist()
                potential_recos = []
                
                kpis_critiques = {
                    "CMJ (cm)": "CMJ", "Vmax": "Vmax", "Squat Keiser": "Squat",
                    "Adducteurs (G)": "Adducteurs", "Nordic Ischio (G)": "Nordic"
                }
                
                for metric_ui, keyword in kpis_critiques.items():
                    col = find_column_in_df(df_all, metric_ui)
                    val = clean_numeric_value(player_row.get(col))
                    if val is not None:
                        _, pct = calculate_percentile(df_all, col, val)
                        
                        # Attribution de la priorité et de la couleur
                        if pct < 33: 
                            niv_texte = "PRIORITE FORTE"
                            couleur = "#D71920" # Rouge
                        elif pct < 66: 
                            niv_texte = "PRIORITE MOYENNE"
                            couleur = "#F39C12" # Orange
                        else: 
                            niv_texte = "PRIORITE FAIBLE"
                            couleur = "#27AE60" # Vert
                        
                        score_priorite = 100 - pct
                        matches = df_exos[df_exos['Cible (Variables du profilage)'].astype(str).str.contains(keyword, na=False, case=False)]
                        for _, exo in matches.iterrows():
                            d_exo = exo.to_dict()
                            d_exo['priorite_score'] = score_priorite
                            d_exo['niveau'] = niv_texte
                            d_exo['couleur'] = couleur
                            d_exo['pourquoi'] = f"Manque de performance sur le test {keyword} (Le joueur est classé dans les {int(pct)}% les plus faibles de l'équipe)."
                            potential_recos.append(d_exo)

                paires_lsi = [("Adducteurs (G)", "Adducteurs (D)", "Adducteurs"), 
                              ("Nordic Ischio (G)", "Nordic Ischio (D)", "Ischios")]
                
                for g, d, label in paires_lsi:
                    asym = get_asymmetry(player_row, g, df_all)
                    if asym and asym > 10:
                        niv_texte = "URGENCE ABSOLUE" if asym > 15 else "PRIORITE FORTE"
                        couleur = "#D71920" # Toujours rouge pour une asymétrie
                        score_asym = (200 + asym) if asym > 15 else (150 + asym)
                        matches = df_exos[df_exos['Catégorie (Couleur)'].astype(str).str.contains("Jaune", na=False)]
                        for _, exo in matches.iterrows():
                            d_exo = exo.to_dict()
                            d_exo['priorite_score'] = score_asym
                            d_exo['niveau'] = niv_texte
                            d_exo['couleur'] = couleur
                            d_exo['pourquoi'] = f"Asymétrie importante détectée ({int(asym)}%) entre les {label} gauche et droit. Risque de blessure élevé."
                            potential_recos.append(d_exo)

                if not potential_recos: 
                    return [], all_exos_list, df_exos

                recos_finales = pd.DataFrame(potential_recos).sort_values('priorite_score', ascending=False)
                top_recos = recos_finales.drop_duplicates(subset=['Exercice']).head(4).to_dict('records')
                
                return top_recos, all_exos_list, df_exos
                
            except Exception as e:
                return [], [], None

        # Exécution de la fonction
        # --- SYSTÈME DE PROGRAMMATION CONSEILLÉE ---
        recos_auto, liste_tous_exos, df_exos_ref = get_recommendations_v3(row, df)
        
        st.markdown("<div class='section-header'>Programmation Conseillée</div>", unsafe_allow_html=True)
        
        # Sélection multiple d'exercices bonus
        if df_exos_ref is not None and liste_tous_exos:
            exos_bonus = st.multiselect("Ajouter des exercices additionnels (Bonus) :", liste_tous_exos, key=f"bonus_multi_{p_sel}")
            
            for eb in exos_bonus:
                if not any(r['Exercice'] == eb for r in recos_auto):
                    det = df_exos_ref[df_exos_ref['Exercice'] == eb].iloc[0].to_dict()
                    det.update({
                        'niveau': "AJOUT MANUEL", 
                        'couleur': "#1E3A8A", # Bleu SDR
                        'pourquoi': "Exercice sélectionné manuellement par le préparateur physique."
                    })
                    recos_auto.append(det)


        # Affichage des cartes d'exercices
        if recos_auto:
            cols = st.columns(len(recos_auto))
            for i, exo in enumerate(recos_auto):
                with cols[i]:
                    bg = exo.get('couleur', '#555555')
                    # Nettoyage des dates Excel (ex: 03-avr -> 3-4)
                    ser = str(exo.get('Séries', '3')).replace('03-avr', '3-4').replace('02-mars', '2-3')
                    rep = str(exo.get('Reps', '10')).replace('05-oct', '5-10')
                    
                    st.markdown(f"""
                        <div style="background:{bg}; color:white; padding:15px; border-radius:10px; min-height:250px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                            <div style="font-size:10px; font-weight:bold; background:rgba(0,0,0,0.2); display:inline-block; padding:3px 8px; border-radius:4px; margin-bottom:10px;">{exo.get('niveau', 'INFO')}</div>
                            <div style="font-size:16px; font-weight:900; margin-bottom:10px; line-height:1.2;">{exo.get('Exercice', '-')}</div>
                            <div style="font-size:12px; margin-bottom:4px;"><b>Séries :</b> {ser}</div>
                            <div style="font-size:12px; margin-bottom:10px;"><b>Reps :</b> {rep}</div>
                            <div style="font-size:11px; margin-bottom:10px; font-style:italic; opacity:0.9;">{exo.get('Focus', '-')}</div>
                            <div style="font-size:10px; border-top:1px solid rgba(255,255,255,0.2); padding-top:8px;">
                                <b>Pourquoi ?</b><br>{exo.get('pourquoi', '')}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        
        key_dom, key_weak, key_strat, key_ante = f"str_dom_{p_sel}", f"str_weak_{p_sel}", f"str_strat_{p_sel}", f"str_ante_{p_sel}"

        if key_dom not in st.session_state: st.session_state[key_dom] = ""
        if key_weak not in st.session_state: st.session_state[key_weak] = ""
        if key_strat not in st.session_state: st.session_state[key_strat] = ""
        if key_ante not in st.session_state: st.session_state[key_ante] = ""

        c_txt1, c_txt2 = st.columns(2)
        with c_txt1:
            st.markdown(f"<div style='color:{SDR_RED}; font-weight:bold; margin-bottom:5px;'>POINT(S) FORT(S)</div>", unsafe_allow_html=True)
            st.session_state[key_dom] = st.text_area("Fort", st.session_state[key_dom], height=150, label_visibility="collapsed", key=f"ad_{p_sel}")
        with c_txt2:
            st.markdown(f"<div style='color:#888; font-weight:bold; margin-bottom:5px;'>AXES D'AMÉLIORATION</div>", unsafe_allow_html=True)
            st.session_state[key_weak] = st.text_area("Faible", st.session_state[key_weak], height=150, label_visibility="collapsed", key=f"aw_{p_sel}")
        
        c_txt3, c_txt4 = st.columns(2)
        with c_txt3:
            st.markdown(f"<div style='color:#27AE60; font-weight:bold; margin-bottom:5px;'>STRATÉGIE</div>", unsafe_allow_html=True)
            st.session_state[key_strat] = st.text_area("Strat", st.session_state[key_strat], height=150, label_visibility="collapsed", key=f"as_{p_sel}")
        with c_txt4:
            st.markdown(f"<div style='color:#F39C12; font-weight:bold; margin-bottom:5px;'>ANTÉCÉDENTS BLESSURE</div>", unsafe_allow_html=True)
            st.session_state[key_ante] = st.text_area("Antéced", st.session_state[key_ante], height=150, label_visibility="collapsed", key=f"aa_{p_sel}")


        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("ℹ️ Détail des Objectifs & Sources", expanded=False):
            data_norms = []
            seen_metrics = set()
            for cat, variables in OFFICIAL_STRUCTURE.items():
                for var in variables:
                    clean_name = get_clean_label(var)
                    if clean_name in seen_metrics: continue
                    seen_metrics.add(clean_name)
                    norm_val = get_norm_text(var).replace("Obj: ", "")
                    source = get_source(var)
                    data_norms.append({"Catégorie": cat, "Indicateur": clean_name, "Objectif": norm_val, "Source": source})
            st.dataframe(pd.DataFrame(data_norms), use_container_width=True, hide_index=True)

        with tab_team:
            df_team_view = df.copy()
            if col_session:
                sel_session_team = st.selectbox("Session :", sorted(df_team_view[col_session].dropna().astype(str).unique()), key="sess_team")
                df_team_view = df_team_view[df_team_view[col_session].astype(str) == sel_session_team]
        
            show_team_page(df_team_view, TEAM_STRUCTURE)

        with tab_evol:
            show_evolution_page(df)

        with tab_comp:
            df_comp = load_data() # On recharge les données pures pour éviter le filtre d'équipe "PRO/U17" du haut
            show_comparateur_page(df_comp)

        with tab_cluster:
            show_clustering_page(df)

        with tab_classement:
             show_classement_page(df)
    

        key_dom, key_weak, key_strat, key_ante = f"str_dom_{p_sel}", f"str_weak_{p_sel}", f"str_strat_{p_sel}", f"str_ante_{p_sel}"
            
        #données en-tête
        
        t_val = clean_numeric_value(row.get('Taille (cm)'))
        anthro_vals = {
            "Age": row.get('Age', '-'),
            "Taille": f"{t_val:.1f}" if t_val is not None else "-",
            "Poids": row.get('Poids (kg)', '-'), # Attention au 'k' minuscule ici !
            "Masse Grasse": row.get('Masse grasse', '-'),
            "Date de Naissance": row.get('Date de Naissance', '-') # On ajoute la nouveauté !
        }
        
      # 1. Récupérationdes notes ET des blessures
        safe_dom = st.session_state.get(key_dom, "")
        safe_weak = st.session_state.get(key_weak, "")
        safe_strat = st.session_state.get(key_strat, "")
        safe_antecedents = st.session_state.get(f"ante_{p_sel}", "")
        safe_selected_injuries = st.session_state.get(f"injuries_{p_sel}", [])

        html_rep = generate_report(
            p_sel, row, df, val_poste, val_lat, val_num, 
            safe_dom, safe_weak, safe_strat, safe_antecedents, 
            safe_selected_injuries, anthro_vals
        )

        b64 = base64.b64encode(html_rep.encode('utf-8')).decode('utf-8')
        
        download_btn = f'''
        <a href="data:text/html;base64,{b64}" download="Profilage_{p_sel}.html" style="text-decoration:none;">
            <button style="background-color:#D71920; color:white; padding:12px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">
                TÉLÉCHARGER LE RAPPORT PDF
            </button>
        </a>
        '''
        st.markdown(download_btn, unsafe_allow_html=True)