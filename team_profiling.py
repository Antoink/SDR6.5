import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
import unicodedata
import numpy as np
from config_rapport import COL_MAPPING

SDR_RED = "#D71920"

def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_column_in_df(df, label):
    if label in COL_MAPPING and COL_MAPPING[label] in df.columns:
        return COL_MAPPING[label]
        
    keywords = [remove_accents(label).lower()]
    df_cols_clean = [remove_accents(str(c)).lower().strip() for c in df.columns]
    
    for k in keywords:
        for idx, col_name in enumerate(df_cols_clean):
            if k in col_name: return df.columns[idx]
            
    parts = label.split(" ")
    if len(parts) > 1:
        main_key = parts[0].lower()
        for idx, col_name in enumerate(df_cols_clean):
            if main_key in col_name: return df.columns[idx]
    return None

def clean_numeric_series(series):
    if series.dtype == 'object':
        series = series.astype(str).str.replace(',', '.').str.replace(' ', '')
    return pd.to_numeric(series, errors='coerce')

def is_inverted_metric(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing']
    return any(x in str(label).lower() for x in keywords)

def get_unit(label):
    l = label.lower()
    if "ratio" in l or "nb " in l: return ""
    if "n/kg" in l: return "N/kg"
    if "w/kg" in l: return "W/kg"
    if "m/s2" in l or "m/s²" in l: return "m/s²"
    if "%" in l or "img" in l: return "%"
    if "amax" in l or "dmax" in l: return "m/s²"
    if "conc" in l or "exc" in l or "nm" in l: return "Nm"
    if "1rm" in l or "poids" in l: return "kg"
    if "watt" in l or "keiser" in l or "tirage" in l or "couché" in l: return "W"
    if "add" in l or "abd" in l or "nordic" in l or "force" in l or "landing" in l: return "N"
    if "vma" in l or "vmax" in l or "vitesse" in l: return "km/h"
    if "cmj" in l or "saut" in l or "taille" in l or "reach" in l or "knee" in l: return "cm"
    if "temps" in l or "chrono" in l or "10m" in l or "505" in l: return "s"
    if "distance" in l or "landmine" in l: return "m"
    if "score" in l: return "pts"
    if "rfd" in l: return "N/s"
    if "rpd" in l: return "W/s"
    return ""

def get_poste_large(position):
    pos = str(position).upper().strip()
    if "GB" in pos: return "GARDIEN"
    if "DC" in pos or "DL" in pos: return "DÉFENSEUR"
    if "MD" in pos or "MC" in pos or "MO" in pos: return "MILIEU"
    if "EXC" in pos or "AT" in pos: return "ATTAQUANT"
    return "AUTRE"

def show_team_page(df, structure_dict):
    df = df.copy()
    col_position = find_column_in_df(df, "Position")
    
    if col_position:
        df['Poste_Groupe'] = df[col_position].apply(get_poste_large)
    else:
        col_poste_excel = find_column_in_df(df, "Poste")
        if col_poste_excel:
            df['Poste_Groupe'] = df[col_poste_excel].astype(str).str.upper()
        else:
            df['Poste_Groupe'] = "AUTRE"

    st.markdown(f"<h2 style='color:{SDR_RED}; border-bottom:1px solid {SDR_RED}; padding-bottom:5px;'>ANALYSE COLLECTIVE</h2>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    if 'selected_player_profiling' not in st.session_state:
        st.session_state.selected_player_profiling = None

    st.markdown("   ")
  
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        cat_sel = st.selectbox("Catégorie : ", list(structure_dict.keys()))
    with c2:
        metric_sel = st.selectbox("Indicateur : ", structure_dict[cat_sel])
    
    col_name = find_column_in_df(df, metric_sel)
    
    with c3:
        filter_type = st.radio("Filtre d'effectif :", ["Groupe entier", "Par Poste (Général)", "Par Position (Détaillée)"], horizontal=True)
        col_filter = None
        sel_options = []
        
        if filter_type == "Par Poste (Général)":
            col_filter = "Poste_Groupe"
        elif filter_type == "Par Position (Détaillée)":
            col_filter = col_position

        if col_filter and col_filter in df.columns:
            all_options = sorted(df[col_filter].dropna().unique())
            sel_options = st.multiselect("Sélectionnez :", all_options, default=all_options)

    if not col_name:
        st.error("Données introuvables.")
        return

    df_main = df.copy()
    if col_filter and sel_options:
        df_main = df_main[df_main[col_filter].isin(sel_options)]

    df_main['Valeur_Clean'] = clean_numeric_series(df_main[col_name])
    df_main = df_main.dropna(subset=['Valeur_Clean', 'Joueur'])
    
    inverted = is_inverted_metric(metric_sel)
    avg_val = df_main['Valeur_Clean'].mean()
    unit = get_unit(metric_sel)

    st.markdown("---")

    st.subheader(f"Classement Équipe : {metric_sel}")

    if inverted:
        df_sorted = df_main.sort_values('Valeur_Clean', ascending=True)
    else:
        df_sorted = df_main.sort_values('Valeur_Clean', ascending=False)

    color_col = "Poste_Groupe" if filter_type != "Groupe entier" else None
    
    fig_all = px.bar(
        df_sorted, 
        x='Joueur', 
        y='Valeur_Clean',
        color=color_col, 
        text='Valeur_Clean',
        color_discrete_sequence=[SDR_RED, 'black', '#555', '#888'] if color_col else [SDR_RED]
    )
    
    fig_all.add_hline(y=avg_val, line_dash="dash", line_color="#333", annotation_text=f"Moyenne : {avg_val:.2f}")
    fig_all.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    # 1. Calculer le maximum pour donner de l'air en haut
    y_max = df_sorted['Valeur_Clean'].max()
    
    fig_all.update_layout(
        xaxis_title="", 
        yaxis_title=f"{metric_sel} ({unit})",
        template="simple_white",
        height=600,
        margin=dict(t=80, b=100, l=50, r=50),
        xaxis=dict(tickangle=-45),
        # FORÇAGE DE LA HAUTEUR : On ajoute 15% de marge en haut du max
        yaxis=dict(range=[0, y_max * 1.15]) 
    )
    
    st.plotly_chart(fig_all, use_container_width=True)

    st.markdown("---")
    st.markdown("---")
    st.markdown(f"<h4 style='color:{SDR_RED};'>Analyse croisée (Nuage de points)</h4>", unsafe_allow_html=True)
    
    # --- CRÉATION DE LA LISTE DE TOUTES LES VARIABLES DISPONIBLES ---
    # On ajoute 'Poste_Groupe' ici pour qu'il ne soit pas supprimé lors du nettoyage !
    colonnes_interdites = [
        'Joueur', 'N° GPS', 'Latéralité', 'Poste', 'Position', 'Poste_Groupe',
        'Date de Naissance', 'DT exact', 'Session exact', 'Session', 'Equipe', 'Player ID', 'Numero'
    ]

    df_viz_base = df.copy()
    if col_filter and sel_options:
        df_viz_base = df_viz_base[df_viz_base[col_filter].isin(sel_options)]

    # Nettoyage systématique pour capter Poids, Taille, etc.
    for col in df_viz_base.columns:
        if col not in colonnes_interdites:
            df_viz_base[col] = clean_numeric_series(df_viz_base[col])

    # On ne garde que les colonnes numériques qui ont au moins 1 donnée non vide
    available_vars = [
        v for v in df_viz_base.columns 
        if pd.api.types.is_numeric_dtype(df_viz_base[v]) 
        and v not in colonnes_interdites
        and df_viz_base[v].notna().any()
    ]
    available_vars = sorted(available_vars)

    if len(available_vars) < 2:
        st.warning("Pas assez de données numériques disponibles pour cette sélection.")
    else:
        c_sc1, c_sc2 = st.columns(2)
        with c_sc1:
            def_x = 0
            for i, k in enumerate(available_vars):
                if "vmax" in k.lower(): 
                    def_x = i
                    break
            scat_x = st.selectbox("Axe X (Horizontal)", available_vars, index=def_x, key="scat_x")
            
        with c_sc2:
            def_y = 1 if len(available_vars) > 1 else 0
            for i, k in enumerate(available_vars):
                if "cmj" in k.lower() or "saut" in k.lower(): 
                    def_y = i
                    break
            scat_y = st.selectbox("Axe Y (Vertical)", available_vars, index=def_y, key="scat_y")

        df_scatter = df_viz_base.dropna(subset=[scat_x, scat_y, 'Joueur']).copy()
        
        if not df_scatter.empty and len(df_scatter) > 1:
            mean_x = df_scatter[scat_x].mean()
            mean_y = df_scatter[scat_y].mean()
            
            # --- CALCUL DE LA CORRÉLATION ---
            corr_matrix = np.corrcoef(df_scatter[scat_x], df_scatter[scat_y])
            r = corr_matrix[0, 1]
            r_squared = r**2
            
            # --- AFFICHAGE DU GRAPHIQUE ---
            fig_scatter = px.scatter(
                df_scatter,
                x=scat_x, y=scat_y,
                color='Poste_Groupe',   # Sépare les couleurs par poste
                symbol='Poste_Groupe',  # Sépare les formes géométriques par poste
                text='Joueur',
                hover_data=['Joueur', 'Poste_Groupe'],
                color_discrete_sequence=[SDR_RED, '#111111', '#888888', '#F39C12', '#3498DB'] 
            )
            fig_scatter.add_vline(x=mean_x, line_width=1, line_dash="dash", line_color=SDR_RED)
            fig_scatter.add_hline(y=mean_y, line_width=1, line_dash="dash", line_color=SDR_RED)
            
            # Ajustement visuel pour que le texte et les formes soient bien visibles
            fig_scatter.update_traces(textposition='top center', marker=dict(size=14, line=dict(width=1.5, color='white')))
            
            fig_scatter.update_layout(
                title=f"{scat_x} vs {scat_y}",
                xaxis_title=scat_x, yaxis_title=scat_y,
                template="simple_white", height=550,
                legend_title_text="Postes"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            # --- AFFICHAGE DU R ET R² ---
            if abs(r) > 0.7: strength = "Forte"
            elif abs(r) > 0.4: strength = "Modérée"
            else: strength = "Faible"
            
            st.markdown(f"""
            <div style='background-color:#f0f2f6; padding:15px; border-radius:8px; border-left:5px solid {SDR_RED};'>
                <div style='font-weight:bold; color:{SDR_RED};'>Analyse statistique :</div>
                Corrélation de Pearson (r) : <b>{r:.3f}</b> | Coefficient de détermination (R²) : <b>{r_squared:.3f}</b>
                <br><span style='font-size:0.9em; color:#555;'>La corrélation est considérée comme <b>{strength}</b>.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Pas assez de données pour calculer une corrélation (il faut au moins 2 joueurs).")

    st.markdown("---")

    st.subheader("Distribution des joueurs")
    
    if len(available_vars) > 0:
        dist_kpi = st.selectbox("Indicateur à analyser :", available_vars, index=0, key="dist_kpi_interactive")
        
        # Filtrage strict sur la variable choisie
        df_viz = df_viz_base.dropna(subset=[dist_kpi, 'Joueur']).copy()

        if not df_viz.empty:
            unit_d = get_unit(dist_kpi)
            mean_val = df_viz[dist_kpi].mean()
            
            all_p_list = sorted(df_viz['Joueur'].unique())
            
            col_sel_manual, _ = st.columns([1, 2])
            with col_sel_manual:
                curr_idx = 0
                if st.session_state.selected_player_profiling in all_p_list:
                    curr_idx = all_p_list.index(st.session_state.selected_player_profiling)
                
                def update_from_select():
                    st.session_state.selected_player_profiling = st.session_state.manual_player_picker
                
                manual_sel = st.selectbox(
                    "Sélectionner un joueur (ou cliquer sur le graphique) :", 
                    all_p_list, 
                    index=curr_idx,
                    key="manual_player_picker",
                    on_change=update_from_select
                )

            np.random.seed(42) 
            df_viz['Y_Jitter'] = np.random.uniform(-0.15, 0.15, size=len(df_viz))

            current_selection = st.session_state.selected_player_profiling
            if not current_selection:
                 current_selection = manual_sel
                 st.session_state.selected_player_profiling = manual_sel

            df_viz['SortOrder'] = df_viz['Joueur'].apply(lambda x: 1 if x == current_selection else 0)
            df_viz = df_viz.sort_values('SortOrder', ascending=True)

            colors = []
            sizes = []
            opacities = []
            lines_width = []
            lines_color = []

            for p in df_viz['Joueur']:
                if p == current_selection:
                    colors.append(SDR_RED)
                    sizes.append(25)
                    opacities.append(1.0)
                    lines_width.append(2)
                    lines_color.append('black')
                else:
                    colors.append("#888888")
                    sizes.append(12)
                    opacities.append(0.6)
                    lines_width.append(1)
                    lines_color.append('white')

            df_viz['Color'] = colors
            df_viz['Size'] = sizes
            df_viz['Opacity'] = opacities
            
            fig_interactive = go.Figure()

            fig_interactive.add_trace(go.Scatter(
                x=df_viz[dist_kpi],
                y=df_viz['Y_Jitter'], 
                mode='markers',
                text=df_viz['Joueur'],
                customdata=df_viz['Joueur'].values,
                marker=dict(
                    color=colors,
                    size=sizes,
                    opacity=opacities,
                    line=dict(width=lines_width, color=lines_color),
                    symbol='circle'
                ),
                hovertemplate="<b>%{text}</b><br>Valeur: %{x:.2f}<extra></extra>",
                showlegend=False
            ))

            fig_interactive.add_vline(x=mean_val, line_width=2, line_dash="dash", line_color=SDR_RED, 
                                      annotation_text="Moy", annotation_position="top right")

            fig_interactive.update_layout(
                title=f"Distribution : {dist_kpi}",
                xaxis_title=f"Valeur ({unit_d})",
                yaxis=dict(showticklabels=False, range=[-0.5, 0.5], showgrid=False),
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                template="simple_white",
                clickmode='event+select',
                dragmode='zoom'
            )

            event = st.plotly_chart(
                fig_interactive, 
                on_select="rerun", 
                selection_mode="points", 
                use_container_width=True,
                key="dist_chart_interactive"
            )

            if event and event.get("selection") and event["selection"]["points"]:
                clicked_point = event["selection"]["points"][0]
                clicked_name = clicked_point.get("customdata")
                if clicked_name and clicked_name != st.session_state.selected_player_profiling:
                    st.session_state.selected_player_profiling = clicked_name
                    st.rerun()

            st.markdown("---")

            sel_p = st.session_state.selected_player_profiling
            if sel_p:
                player_row = df_viz[df_viz['Joueur'] == sel_p]
                if not player_row.empty:
                    val_p = player_row[dist_kpi].iloc[0]
                    diff = val_p - mean_val
                    
                    st.markdown(f"<h3 style='text-align: center; color:{SDR_RED};'>{sel_p}</h3>", unsafe_allow_html=True)
                    
                    col_metrics = st.columns(3)
                    col_metrics[0].metric("Valeur", f"{val_p:.2f} {unit_d}")
                    col_metrics[1].metric("Moyenne", f"{mean_val:.2f} {unit_d}")
                    
                    is_good = (diff < 0) if is_inverted_metric(dist_kpi) else (diff > 0)
                    col_metrics[2].metric("Écart", f"{diff:+.2f} {unit_d}", 
                                          delta_color="normal" if is_good else "inverse")
            else:
                st.info("Sélectionnez un joueur pour voir les détails.")
        else:
            st.warning("Aucune donnée disponible pour cet indicateur.")
    else:
        st.warning("Aucune variable numérique n'est disponible dans les données.")