import streamlit as st
import pandas as pd
from config_rapport import COL_MAPPING, TEAM_STRUCTURE, UNITS
from comparateur import get_best_photo_path, img_to_b64
from utils import load_data

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

# --- AFFICHAGE PODIUM ---
def render_podium(top3):
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(3)
    medal_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
    order = [1, 0, 2] 
    
    for i, idx in enumerate(order):
        if idx < len(top3):
            with cols[i]:
                player = top3.iloc[idx]
                rank = idx + 1
                photo_path = get_best_photo_path(player['Joueur'])
                
                img_style = "width:70px; height:70px; border-radius:50%; border:4px solid {}; object-fit: cover; object-position: 50% 20%; display: block; margin: 0 auto;".format(medal_colors[rank])
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

# --- PAGE PRINCIPALE UNIQUE ---
def show_classement_page(df_dummy):
    # On charge les données complètes ici, en ignorant le df_dummy passé par le main
    df = load_data()
    
    st.markdown(f"<h2 style='text-align: center; color: {SDR_RED};'>CLASSEMENT GÉNÉRAL</h2>", unsafe_allow_html=True)
    
    if "Session" not in df.columns: 
        st.error("Colonne 'Session' introuvable dans le fichier.")
        return

    sel_session = st.selectbox("Session :", sorted(df["Session"].dropna().unique().astype(str)))
    df_session = df[df["Session"].astype(str) == sel_session].copy()
    
    toutes_equipes = sorted(df_session["Equipe"].dropna().unique().astype(str))
    choix_equipes = st.multiselect("Catégories à inclure dans le classement :", toutes_equipes, default=toutes_equipes)
    choix_kpi = st.selectbox("Indicateur :", list(UNITS.keys()))

    df_filtered = df_session[df_session["Equipe"].astype(str).isin(choix_equipes)] if choix_equipes else df_session

    col_name = find_col(df_filtered, choix_kpi)
    if not col_name: 
        st.warning(f"Indicateur '{choix_kpi}' non trouvé.")
        return

    df_filtered['Valeur_Clean'] = df_filtered[col_name].apply(clean_val)
    df_clean = df_filtered.dropna(subset=['Valeur_Clean', 'Joueur']).copy()
    
    if df_clean.empty: 
        st.info("Aucune donnée disponible.")
        return

    df_clean = df_clean.sort_values(by='Valeur_Clean', ascending=is_inverted(choix_kpi))
    df_clean['Valeur_Display'] = df_clean['Valeur_Clean'].apply(lambda x: f"{x:.2f} {get_unit(choix_kpi)}")
    df_clean['Rang'] = range(1, len(df_clean) + 1)
    
    render_podium(df_clean.head(3))
    
    st.markdown("### Classement complet", unsafe_allow_html=True)
    table_html = f"""
    <style>
        .custom-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .custom-table th {{ background-color: {SDR_RED}; color: white; padding: 12px; text-align: left; font-weight: bold; border: 1px solid #ddd; }}
        .custom-table td {{ padding: 10px; border-bottom: 1px solid #ddd; border-right: 1px solid #eee; color: black; }}
        .custom-table tr:nth-child(even) {{ background-color: #f8f8f8; }}
    </style>
    <table class='custom-table'>
        <thead><tr><th>Rang</th><th>Joueur</th><th>Catégorie</th><th>Valeur</th></tr></thead>
        <tbody>
    """
    for _, row in df_clean.iterrows():
        table_html += f"<tr><td>{row['Rang']}</td><td>{row['Joueur']}</td><td>{row['Equipe']}</td><td>{row['Valeur_Display']}</td></tr>"
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)