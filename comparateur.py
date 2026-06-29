import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64
import numpy as np
from config_rapport import COL_MAPPING, OFFICIAL_STRUCTURE, UNITS

SDR_RED = "#D71920"
SDR_BLUE = "#1E3A8A"

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def img_to_b64(img_path):
    try:
        with open(img_path, "rb") as f: 
            return base64.b64encode(f.read()).decode()
    except: 
        return ""

def get_best_photo_path(player_name):
    """Cherche la photo au format NOM Prénom ou Prénom NOM"""
    folder = None
    for f_name in ["Photo", "Photos"]:
        if os.path.exists(f_name):
            folder = f_name
            break
            
    if not folder: return None
        
    files_map = {f.lower(): f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}
    clean_name = player_name.strip()
    parts = clean_name.split()
    
    name_formats = [clean_name.lower()] 
    if len(parts) >= 2:
        nom = parts[-1].lower() 
        prenom = " ".join(parts[:-1]).lower() 
        name_formats.append(f"{nom} {prenom}") 
        name_formats.append(nom) 
        
    for fmt in name_formats:
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            if (fmt + ext) in files_map:
                return os.path.join(folder, files_map[fmt + ext])
    return None

def find_col(df, label):
    if label in COL_MAPPING and COL_MAPPING[label] in df.columns:
        return COL_MAPPING[label]
    for c in df.columns:
        if label.lower() in str(c).lower():
            return c
    return None

def clean_val(val):
    try:
        if pd.isna(val) or str(val).strip() == "" or str(val) == "#VALEUR!": return None
        return float(str(val).replace(',', '.'))
    except:
        return None

def format_number(val):
    if pd.isna(val) or str(val).strip() == "-" or str(val).strip() == "": return "-"
    try:
        f_val = float(str(val).replace(',', '.'))
        if f_val.is_integer(): return str(int(f_val))
        return str(f_val)
    except:
        return str(val)

def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '5-0-5', '505', 'agilité', 'masse grasse', 'landing %']
    return any(x in str(label).lower() for x in keywords)

def calculate_percentile(df, col_name, value):
    if col_name not in df.columns or value is None: return 0
    clean_col = df[col_name].astype(str).str.replace(',', '.').replace(['#VALEUR!', '#DIV/0!', 'nan', 'None', ''], None)
    valid_values = pd.to_numeric(clean_col, errors='coerce').dropna()
    
    if valid_values.empty: return 0
    
    inverted = is_inverted(col_name)
    if inverted:
        percentile = (valid_values >= value).mean() * 100
    else:
        percentile = (valid_values <= value).mean() * 100
    return percentile

def clean_val_display(val, unit):
    return f"{val} {unit}" if val and val != "-" and val != "" else "N/A"
# ==========================================
# PAGE PRINCIPALE
# ==========================================

def show_comparateur_page(df):
    vs_html = ""
    st.markdown(f"<h2 style='text-align: center; color: {SDR_RED}; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 25px;'>Comparateur de Profils</h2>", unsafe_allow_html=True)
    
    col_session = next((c for c in df.columns if 'session' in str(c).lower()), None)
    if not col_session:
        st.warning("Aucune colonne Session/Date trouvée dans les données.")
        return

    equipes_dispos = sorted(df['Equipe'].dropna().astype(str).unique()) if 'Equipe' in df.columns else ["N/A"]
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        st.markdown(f"<div style='border-left: 4px solid {SDR_RED}; padding-left: 8px; margin-bottom: 10px;'><b style='color:{SDR_RED}; font-size:14px;'>PROFIL 1</b></div>", unsafe_allow_html=True)
        eq1 = st.selectbox("Équipe", equipes_dispos, key="eq1", label_visibility="collapsed")
        joueurs_eq1 = sorted(df[df['Equipe'] == eq1]['Joueur'].dropna().unique()) if 'Equipe' in df.columns else sorted(df['Joueur'].dropna().unique())
        j1 = st.selectbox("Joueur", joueurs_eq1, key="j1", label_visibility="collapsed") if joueurs_eq1 else None
        if j1:
            sessions_j1 = sorted(df[(df['Equipe'] == eq1) & (df['Joueur'] == j1)][col_session].dropna().astype(str).unique()) if 'Equipe' in df.columns else []
            sess1 = st.selectbox("Session", sessions_j1, key="s1", label_visibility="collapsed")
        else:
            sess1 = None

    with col_sel2:
        st.markdown(f"<div style='border-left: 4px solid {SDR_BLUE}; padding-left: 8px; margin-bottom: 10px;'><b style='color:{SDR_BLUE}; font-size:14px;'>PROFIL 2</b></div>", unsafe_allow_html=True)
        eq2 = st.selectbox("Équipe", equipes_dispos, key="eq2", index=0, label_visibility="collapsed")
        joueurs_eq2 = sorted(df[df['Equipe'] == eq2]['Joueur'].dropna().unique()) if 'Equipe' in df.columns else sorted(df['Joueur'].dropna().unique())
        j2_default = 1 if len(joueurs_eq2) > 1 else 0
        j2 = st.selectbox("Joueur", joueurs_eq2, key="j2", index=j2_default, label_visibility="collapsed") if joueurs_eq2 else None
        if j2:
            sessions_j2 = sorted(df[(df['Equipe'] == eq2) & (df['Joueur'] == j2)][col_session].dropna().astype(str).unique()) if 'Equipe' in df.columns else []
            sess2 = st.selectbox("Session", sessions_j2, key="s2", label_visibility="collapsed")
        else:
            sess2 = None

    if not j1 or not j2 or not sess1 or not sess2:
        return

    if j1 == j2 and sess1 == sess2:
        st.warning("Veuillez sélectionner deux profils différents (ou le même joueur sur deux sessions différentes).")
        return
    
    # Récupération des données
    try:
        row_j1 = df[(df['Joueur'] == j1) & (df[col_session].astype(str) == sess1)].iloc[0]
        row_j2 = df[(df['Joueur'] == j2) & (df[col_session].astype(str) == sess2)].iloc[0]
    except:
        st.error("Données introuvables pour cette sélection.")
        return

    display_name1 = j1
    display_name2 = j2
    
    img1_src = f"data:image/png;base64,{img_to_b64(get_best_photo_path(display_name1))}" if get_best_photo_path(display_name1) else ""
    img2_src = f"data:image/png;base64,{img_to_b64(get_best_photo_path(display_name2))}" if get_best_photo_path(display_name2) else ""
    
    # Photos beaucoup plus grandes (130px)
    html_img1 = f'<img src="{img1_src}" style="width:130px; height:130px; object-fit:cover; object-position:top center; border-radius:50%; border:5px solid {SDR_RED}; box-shadow:0 6px 15px rgba(0,0,0,0.15); flex-shrink:0;">' if img1_src else f'<div style="width:130px; height:130px; border-radius:50%; border:5px solid {SDR_RED}; background:#eee; display:flex; align-items:center; justify-content:center; color:#888; font-size:14px; font-weight:bold; flex-shrink:0;">PHOTO</div>'
    
    html_img2 = f'<img src="{img2_src}" style="width:130px; height:130px; object-fit:cover; object-position:top center; border-radius:50%; border:5px solid {SDR_BLUE}; box-shadow:0 6px 15px rgba(0,0,0,0.15); flex-shrink:0;">' if img2_src else f'<div style="width:130px; height:130px; border-radius:50%; border:5px solid {SDR_BLUE}; background:#eee; display:flex; align-items:center; justify-content:center; color:#888; font-size:14px; font-weight:bold; flex-shrink:0;">PHOTO</div>'

    t1_clean = clean_val(row_j1.get('Taille (cm)'))
    t2_clean = clean_val(row_j2.get('Taille (cm)'))
    
    age1, taille1, poids1 = format_number(row_j1.get('Age')), f"{t1_clean:.1f}" if t1_clean is not None else "-", format_number(row_j1.get('Poids (kg)'))
    age2, taille2, poids2 = format_number(row_j2.get('Age')), f"{t2_clean:.1f}" if t2_clean is not None else "-", format_number(row_j2.get('Poids (kg)'))
    # --- CARTE VERSUS AGRANDIE ---
    meta1 = f"{clean_val_display(age1, 'ans')} | {clean_val_display(taille1, 'cm')} | {clean_val_display(poids1, 'kg')}"
    meta2 = f"{clean_val_display(age2, 'ans')} | {clean_val_display(taille2, 'cm')} | {clean_val_display(poids2, 'kg')}"

# 3. Construction du HTML avec un conteneur Flexbox Parent (flex-wrap: nowrap est la clé)
    vs_html = "<div style='display:flex; flex-direction:row; align-items:center; justify-content:center; flex-wrap:nowrap; gap:20px; width:100%; margin-bottom:30px;'>"

# --- Profil Gauche ---
    vs_html += f"<div style='flex:1; display:flex; align-items:center; gap:20px; justify-content:flex-end;'>"
    vs_html += f"{html_img1}<div style='display:flex; flex-direction:column; text-align:right;'>"
    vs_html += f"<h2 style='color:{SDR_RED}; margin:0; font-weight:900; font-size:24px; text-transform:uppercase;'>{display_name1}</h2>"
    vs_html += f"<p style='color:#555; margin:5px 0 0 0; font-size:14px; line-height:1.4;'><span style='background:#ffe8e8; color:{SDR_RED}; padding:2px 8px; border-radius:4px; font-weight:bold;'>{row_j1.get('Equipe', 'N/A')}</span><br><b>{row_j1.get('Position', 'N/A')}</b><br>{meta1}<br><span style='font-style:italic; font-size:12px; color:#888;'>({sess1})</span></p></div></div>"

# --- Bloc VS (Centre) ---
    vs_html += f"<div style='flex:0 0 60px; text-align:center;'><div style='background:#2b2b2b; color:white; display:flex; align-items:center; justify-content:center; width:55px; height:55px; border-radius:50%; font-weight:900; font-style:italic; font-size:18px; box-shadow:0 4px 10px rgba(0,0,0,0.2); margin:auto;'>VS</div></div>"

# --- Profil Droite ---
    vs_html += f"<div style='flex:1; display:flex; align-items:center; gap:20px; justify-content:flex-start;'>"
    vs_html += f"<div style='display:flex; flex-direction:column; text-align:left;'>"
    vs_html += f"<h2 style='color:{SDR_BLUE}; margin:0; font-weight:900; font-size:24px; text-transform:uppercase;'>{display_name2}</h2>"
    vs_html += f"<p style='color:#555; margin:5px 0 0 0; font-size:14px; line-height:1.4;'><span style='background:#e8eeff; color:{SDR_BLUE}; padding:2px 8px; border-radius:4px; font-weight:bold;'>{row_j2.get('Equipe', 'N/A')}</span><br><b>{row_j2.get('Position', 'N/A')}</b><br>{meta2}<br><span style='font-style:italic; font-size:12px; color:#888;'>({sess2})</span></p></div>{html_img2}</div>"

# Fermeture du conteneur
    vs_html += "</div>"

# Affichage
    st.markdown(vs_html, unsafe_allow_html=True)

    # --- GRAPHIQUES ET TABLEAUX ---
    for cat_title, items in OFFICIAL_STRUCTURE.items():
        if "isociné" in cat_title.lower() or "biodex" in cat_title.lower():
            continue 
            
        labels = []
        vals_j1_raw, vals_j2_raw = [], []
        vals_j1_norm, vals_j2_norm = [], []
        table_data = []
        
        for label in items:
            if any(b in label for b in ["Q Conc", "IJ Conc", "IJ Exc", "Ratio Mixte"]):
                continue

            col_name = find_col(df, label)
            if col_name:
                v1 = clean_val(row_j1.get(col_name))
                v2 = clean_val(row_j2.get(col_name))
                
                unit = UNITS.get(label, "")
                unit_str = f" {unit}" if unit else ""
                
                mean_val = None
                clean_team_col = df[col_name].astype(str).str.replace(',', '.').replace(['#VALEUR!', '#DIV/0!', 'nan', 'None', ''], None)
                valid_team_vals = pd.to_numeric(clean_team_col, errors='coerce').dropna()
                if not valid_team_vals.empty:
                     mean_val = valid_team_vals.mean()
                     
                if v1 is not None or v2 is not None:
                    labels.append(label)
                    
                    v1_str = f"{v1:.1f}{unit_str}" if v1 is not None else "-"
                    v2_str = f"{v2:.1f}{unit_str}" if v2 is not None else "-"
                    mean_str = f"{float(mean_val):.1f}{unit_str}" if pd.notna(mean_val) else "-"
                    
                    vals_j1_raw.append(v1_str)
                    vals_j2_raw.append(v2_str)
                    
                    p1 = calculate_percentile(df, col_name, v1) if v1 is not None else 0
                    p2 = calculate_percentile(df, col_name, v2) if v2 is not None else 0
                    
                    vals_j1_norm.append(p1)
                    vals_j2_norm.append(p2)
                    
                    vainqueur = "-"
                    ecart_txt = "-"
                    color_v = "#888"
                    v1_color = "#333"
                    v2_color = "#333"
                    
                    if v1 is not None and v2 is not None:
                        inverted = is_inverted(col_name)
                        diff = abs(v1 - v2)
                        
                        if (not inverted and v1 > v2) or (inverted and v1 < v2):
                            vainqueur = display_name1
                            color_v = SDR_RED
                            v1_color = SDR_RED
                            pct_diff = (diff / v2 * 100) if v2 != 0 else 0
                            ecart_txt = f"+ {diff:.1f}{unit_str} ({pct_diff:.0f}%)"
                        elif (not inverted and v2 > v1) or (inverted and v2 < v1):
                            vainqueur = display_name2
                            color_v = SDR_BLUE
                            v2_color = SDR_BLUE
                            pct_diff = (diff / v1 * 100) if v1 != 0 else 0
                            ecart_txt = f"+ {diff:.1f}{unit_str} ({pct_diff:.0f}%)"
                        else:
                            vainqueur = "Égalité"
                            ecart_txt = "0"
                            
                    table_data.append({
                        "Test": f"{label}",
                        "J1": f"<span style='color:{v1_color}; font-weight:bold;'>{v1_str}</span>",
                        "J2": f"<span style='color:{v2_color}; font-weight:bold;'>{v2_str}</span>",
                        "Moy_Equipe": mean_str,
                        "Vainqueur": f"<span style='color:{color_v}; font-weight:bold;'>{vainqueur}</span>",
                        "Avantage": ecart_txt
                    })
                    
        if labels:
            # TITRE DE LA CATÉGORIE ÉPURÉ (Grand, Rouge, souligné, SANS boîte)
            st.markdown(f"<h3 style='color:{SDR_RED}; margin-top:40px; text-transform:uppercase; font-weight:900; border-bottom:3px solid {SDR_RED}; padding-bottom:10px; margin-bottom:30px; font-size:24px; letter-spacing:1px;'>{cat_title}</h3>", unsafe_allow_html=True)
            
            col_radar, col_bars = st.columns(2)
            
            with col_radar:
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_j1_norm + [vals_j1_norm[0]], theta=labels + [labels[0]],
                    customdata=vals_j1_raw + [vals_j1_raw[0]],
                    hovertemplate="%{theta}<br>Valeur : <b>%{customdata}</b><br>Score : %{r:.0f}%<extra></extra>",
                    fill='toself', name=display_name1, line=dict(color=SDR_RED, width=3),
                    marker=dict(size=8), fillcolor=f'rgba(215, 25, 32, 0.15)'
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_j2_norm + [vals_j2_norm[0]], theta=labels + [labels[0]],
                    customdata=vals_j2_raw + [vals_j2_raw[0]],
                    hovertemplate="%{theta}<br>Valeur : <b>%{customdata}</b><br>Score : %{r:.0f}%<extra></extra>",
                    fill='toself', name=display_name2, line=dict(color=SDR_BLUE, width=3),
                    marker=dict(size=8), fillcolor=f'rgba(30, 58, 138, 0.15)'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)', 
                        radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor="#e5e7eb", linecolor="#e5e7eb"), 
                        angularaxis=dict(gridcolor="#e5e7eb", linecolor="#e5e7eb", tickfont=dict(size=12, color="#444", weight="bold"))
                    ),
                    showlegend=True, legend=dict(orientation="h", y=-0.15, font=dict(size=13, color="#111", weight="bold")),
                    margin=dict(l=60, r=60, t=40, b=10), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with col_bars:
                fig_bars = go.Figure()
                fig_bars.add_trace(go.Bar(
                    y=labels, x=vals_j1_norm,
                    orientation='h', name=display_name1, marker_color=SDR_RED,
                    text=vals_j1_raw, textposition='auto', insidetextanchor='end', 
                    textfont=dict(color='white', weight='bold', size=13), hoverinfo='skip'
                ))
                fig_bars.add_trace(go.Bar(
                    y=labels, x=vals_j2_norm,
                    orientation='h', name=display_name2, marker_color=SDR_BLUE,
                    text=vals_j2_raw, textposition='auto', insidetextanchor='end', 
                    textfont=dict(color='white', weight='bold', size=13), hoverinfo='skip'
                ))
                fig_bars.update_layout(
                    barmode='group', bargap=0.2, bargroupgap=0.05,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(visible=False, range=[0, 115]), 
                    yaxis=dict(showgrid=False, tickfont=dict(size=12, color="#444", weight="bold"), categoryorder='array', categoryarray=labels[::-1]),
                    margin=dict(l=10, r=20, t=30, b=10), height=450, showlegend=False
                )
                st.plotly_chart(fig_bars, use_container_width=True)
                
            # --- LE TABLEAU ---
            st.markdown("<h5 style='color:#555; margin-top:15px; font-size:14px; border-bottom:2px solid #eee; padding-bottom:5px;'> Détails</h5>", unsafe_allow_html=True)
            
            t_html = ""
            t_html += "<table style='width:100%; border-collapse:collapse; font-size:13px; text-align:center; font-family:sans-serif; margin-bottom: 20px;'>"
            t_html += f"<tr style='background-color:#f8f9fa; color:#111; border-bottom:2px solid #ccc;'>"
            t_html += f"<th style='padding:10px; text-align:left;'>Test Physique</th>"
            t_html += f"<th style='padding:10px; color:{SDR_RED}; font-size:14px;'>{display_name1}</th>"
            t_html += f"<th style='padding:10px; color:{SDR_BLUE}; font-size:14px;'>{display_name2}</th>"
            t_html += f"<th style='padding:10px; color:#888;'>Moy. Équipe</th>"
            t_html += f"<th style='padding:10px;'>Vainqueur</th>"
            t_html += f"<th style='padding:10px;'>Écart</th>"
            t_html += "</tr>"
            
            for r_data in table_data:
                t_html += "<tr style='border-bottom:1px solid #eee;'>"
                t_html += f"<td style='padding:8px; text-align:left; font-weight:bold; color:#444;'>{r_data['Test']}</td>"
                t_html += f"<td style='padding:8px; font-size:14px;'>{r_data['J1']}</td>"
                t_html += f"<td style='padding:8px; font-size:14px;'>{r_data['J2']}</td>"
                t_html += f"<td style='padding:8px; color:#888; font-style:italic;'>{r_data['Moy_Equipe']}</td>"
                t_html += f"<td style='padding:8px;'>{r_data['Vainqueur']}</td>"
                t_html += f"<td style='padding:8px; color:#555; font-size:12px; font-weight:bold;'>{r_data['Avantage']}</td>"
                t_html += "</tr>"
                
            t_html += "</table>"
            st.markdown(t_html, unsafe_allow_html=True)
            
        else:
            st.info(f"Aucune donnée disponible pour ces profils dans la catégorie {cat_title}.")