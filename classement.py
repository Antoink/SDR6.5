import streamlit as st
import pandas as pd
from config_rapport import COL_MAPPING, TEAM_STRUCTURE, UNITS
from comparateur import get_best_photo_path, img_to_b64

SDR_RED = "#D71920"

# --- UTILITAIRES ---
def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '5-0-5', '505', 'agilité', 'masse grasse', 'landing %']
    return any(x in str(label).lower() for x in keywords)

def get_unit(label):
    return UNITS.get(label, "")

def clean_val(val):
    try:
        if pd.isna(val) or str(val).strip() == "" or str(val) == "#VALEUR!": return None
        return float(str(val).replace(',', '.'))
    except: return None

def find_col(df, label):
    if label in COL_MAPPING and COL_MAPPING[label] in df.columns: return COL_MAPPING[label]
    label_clean = "".join(c for c in label.lower() if c.isalnum())
    for col in df.columns:
        if label_clean == "".join(c for c in str(col).lower() if c.isalnum()): return col
    return None

# --- AFFICHAGE PODIUM (HORIZONTAL) ---
def render_podium(top3):
    st.markdown("<br>", unsafe_allow_html=True)
    # Force les 3 colonnes pour l'alignement horizontal
    cols = st.columns(3)
    
    # Couleurs médailles
    medal_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
    
    # Ordre visuel : 2ème (col 0), 1er (col 1), 3ème (col 2)
    # On ajuste pour que le 1er soit bien au milieu (index 1)
    order = [1, 0, 2] 
    
    for i, idx in enumerate(order):
        if idx < len(top3):
            with cols[i]:
                player = top3.iloc[idx]
                rank = idx + 1
                photo_path = get_best_photo_path(player['Joueur'])
                
                # Taille 70px et positionnement centré sur le haut (visage)
                img_style = (
                    "width:70px; height:70px; border-radius:50%; "
                    f"border:4px solid {medal_colors[rank]}; "
                    "object-fit: cover; object-position: 50% 20%; "
                    "display: block; margin: 0 auto;"
                )
                
                img_html = f"<img src='data:image/png;base64,{img_to_b64(photo_path)}' style='{img_style}'>" if photo_path else "<div style='width:70px; height:70px; border-radius:50%; background:#ccc; margin: 0 auto;'></div>"
                
                st.markdown(f"""
                <div style='text-align:center; display:flex; flex-direction:column; align-items:center;'>
                    {img_html}
                    <div style='background:{medal_colors[rank]}; color:white; border-radius:50%; width:22px; height:22px; margin-top:-15px; font-weight:bold; font-size:11px; display:flex; align-items:center; justify-content:center; box-shadow: 0 2px 4px rgba(0,0,0,0.3); z-index:2;'>{rank}</div>
                    <div style='font-weight:bold; font-size:13px; margin-top:8px;'>{player['Joueur']}</div>
                    <div style='color:{SDR_RED}; font-weight:900; font-size:14px;'>{player['Valeur_Display']}</div>
                </div>
                """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- PAGE PRINCIPALE ---
def show_classement_page(df):
    st.markdown(f"<h2 style='text-align: center; color: {SDR_RED}; margin-bottom: 20px;'>CLASSEMENT GÉNÉRAL</h2>", unsafe_allow_html=True)
    
    COL_SESSION = "Session"
    if COL_SESSION not in df.columns:
        st.error(f"Erreur : La colonne '{COL_SESSION}' est introuvable.")
        return

    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        sessions = sorted(df[COL_SESSION].dropna().astype(str).unique())
        sel_session = st.selectbox("Session :", sessions)
    
    df_filtered = df[df[COL_SESSION].astype(str) == sel_session].copy()
    
    with col2:
        equipes = sorted(df_filtered["Equipe"].dropna().astype(str).unique())
        choix_equipes = st.multiselect("Catégorie :", equipes, default=equipes)
        if choix_equipes: df_filtered = df_filtered[df_filtered["Equipe"].astype(str).isin(choix_equipes)]

    with col3:
        all_kpis = list(UNITS.keys())
        choix_kpi = st.selectbox("Indicateur (KPI) :", all_kpis)

    st.markdown("---")

    col_name = find_col(df_filtered, choix_kpi)
    if not col_name: return

    df_filtered['Valeur_Clean'] = df_filtered[col_name].apply(clean_val)
    df_clean = df_filtered.dropna(subset=['Valeur_Clean', 'Joueur']).copy()
    if df_clean.empty: return

    inverted = is_inverted(choix_kpi)
    df_clean = df_clean.sort_values(by='Valeur_Clean', ascending=inverted)
    unit = get_unit(choix_kpi)
    df_clean['Valeur_Display'] = df_clean['Valeur_Clean'].apply(lambda x: f"{x:.2f} {unit}")
    df_clean['Rang'] = range(1, len(df_clean) + 1)

    # 1. Rendu Podium Horizontal
    render_podium(df_clean.head(3))
    
    # 2. Tableau stylisé
    st.markdown("### Classement complet", unsafe_allow_html=True)
    
    table_html = f"""
    <style>
        .custom-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .custom-table th {{ background-color: {SDR_RED}; color: white; padding: 12px; text-align: left; font-weight: bold; border: 1px solid #ddd; }}
        .custom-table td {{ padding: 10px; border-bottom: 1px solid #ddd; border-right: 1px solid #eee; color: black; }}
        .custom-table tr:nth-child(even) {{ background-color: #f0f0f0; }}
        .custom-table tr:nth-child(odd) {{ background-color: #ffffff; }}
    </style>
    <table class='custom-table'>
        <thead><tr><th>Rang</th><th>Joueur</th><th>Catégorie</th><th>Valeur</th></tr></thead>
        <tbody>
    """
    for _, row in df_clean.iterrows():
        table_html += f"<tr><td>{row['Rang']}</td><td>{row['Joueur']}</td><td>{row['Equipe']}</td><td>{row['Valeur_Display']}</td></tr>"
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)