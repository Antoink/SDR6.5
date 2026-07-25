import streamlit as st
import pandas as pd
from config_rapport import COL_MAPPING, TEAM_STRUCTURE, UNITS
from comparateur import get_best_photo_path, img_to_b64, get_best_season_record_paired # Ajout de l'import ici
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
    # Conserve ta fonction de podium actuelle intacte ici...
    pass

# --- PAGE PRINCIPALE UNIQUE ---
def show_classement_page(df_dummy):
    # On force le rechargement propre des données globales
    df = load_data()
    
    st.markdown(f"<h2 style='text-align: center; color: {SDR_RED};'>CLASSEMENT GÉNÉRAL</h2>", unsafe_allow_html=True)
    
    if "Session" not in df.columns: 
        st.error("Colonne 'Session' introuvable dans le fichier.")
        return

    # 1. Sélection de la session avec intégration du Record de Saison
    sessions_dispos = ["🏆 Record de Saison"] + sorted(df["Session"].dropna().unique().astype(str))
    sel_session = st.selectbox("Session :", sessions_dispos, key="sess_classement")
    
    # 2. Application de la logique de Record Synchronisé ou de session fixe
    if sel_session == "🏆 Record de Saison":
        records = []
        for j in df['Joueur'].dropna().unique():
            df_j = df[df['Joueur'] == j]
            if not df_j.empty:
                row_j = get_best_season_record_paired(df_j)
                row_j['Joueur'] = j
                row_j['Equipe'] = df_j.iloc[-1].get('Equipe', 'N/A')
                records.append(row_j)
        df_session = pd.DataFrame(records)
    else:
        df_session = df[df["Session"].astype(str) == sel_session].copy()
    
    # 3. Choix des catégories (Equipes)
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

    # Tri selon l'indicateur (temps vs. force)
    df_clean = df_clean.sort_values(by='Valeur_Clean', ascending=is_inverted(choix_kpi))
    df_clean['Valeur_Display'] = df_clean['Valeur_Clean'].apply(lambda x: f"{x:.2f} {get_unit(choix_kpi)}")
    df_clean['Rang'] = range(1, len(df_clean) + 1)
    
    # Rendu du Podium
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