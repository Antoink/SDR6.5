import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

SDR_RED = "#D71920"
SDR_DARK = "#2B2B2B"

def show_evolution_page(df_unfiltered):
    # FORCE LE NOM DE LA COLONNE
    time_col = "Session"

    st.markdown(f"""
    <style>
    .stSelectbox label, .stSlider label {{ font-weight: bold; color: {SDR_DARK}; }}
    .css-1r6slb0, .css-1n76uvr {{ border-radius: 10px !important; }}
    div[data-testid="metric-container"] {{
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        border-left: 5px solid {SDR_RED};
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align: center; color: {SDR_RED}; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 30px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>Suivi Longitudinal</h2>", unsafe_allow_html=True)
    
    # VÉRIFICATION STRICTE
    if time_col not in df_unfiltered.columns:
        st.error(f"Erreur : La colonne '{time_col}' est introuvable dans votre fichier. Vérifiez le nom dans Excel.")
        return

    cols_exclues = ["Player ID", "Age", "Numero", "N° GPS", "Date de Naissance", "Taille (cm)", "Poids (kg)", "Masse grasse", "Session"]
    numeric_cols = [c for c in df_unfiltered.columns if c not in cols_exclues and pd.api.types.is_numeric_dtype(df_unfiltered[c])]
        
    groupes_kpi = {
        "Profilage Moteur (Force, Mobilité)": [c for c in numeric_cols if any(x in c.lower() for x in ['force', 'adducteur', 'abducteur', 'nordic', 'ratio', 'squeeze', 'sit', 'reach', 'knee', 'wall', 'biodex', 'lsi', 'ij', 'q 60', 'q 240', 'inverseur', 'everseur', 'heel'])],
        "Profilage Athlétique (Explosivité, Puissance, CMJ)": [c for c in numeric_cols if any(x in c.lower() for x in ['cmj', 'squat', 'wattbike', 'jump'])],
        "Profilage Physiologique (GPS, Terrain)": [c for c in numeric_cols if any(x in c.lower() for x in ['amax', 'dmax', 'vmax', 'acc', 'dec', 'hsr', 'distance', 'sprint', 'vma', '10m', 'temps', 'sv1', 'sv2', 'fc'])]
    }
    
    st.markdown("<div style='background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    
    col_grp, col_var = st.columns(2)
    with col_grp:
        selected_group = st.selectbox("Type de profilage:", list(groupes_kpi.keys()))
    
    kpi_choices = groupes_kpi[selected_group] if groupes_kpi[selected_group] else numeric_cols
    
    with col_var:
        selected_var = st.selectbox("Indicateur :", sorted(kpi_choices) if kpi_choices else ["Aucun indicateur"])
        
    sessions_dispos = sorted(df_unfiltered[time_col].dropna().unique().tolist())
    
    if len(sessions_dispos) < 2:
        st.warning("Pas assez de sessions disponibles pour une analyse d'évolution.")
        return
        
    st.markdown("<br>", unsafe_allow_html=True)
    session_start, session_end = st.select_slider("Plage de sessions à analyser :", options=sessions_dispos, value=(sessions_dispos[0], sessions_dispos[-1]))
    st.markdown("</div>", unsafe_allow_html=True)

    if selected_var == "Aucun indicateur" or session_start == session_end:
        st.info("Veuillez sélectionner un indicateur et une plage d'au moins 2 sessions distinctes.")
        return

    idx_start = sessions_dispos.index(session_start)
    idx_end = sessions_dispos.index(session_end)
    selected_sessions = sessions_dispos[idx_start:idx_end+1]

    df_target = df_unfiltered[df_unfiltered[time_col].isin(selected_sessions)].copy()

    tab_equipe, tab_individuel = st.tabs(["Vision Équipe", " Vision Individuelle"])

    with tab_equipe:
        st.markdown(f"<h3 class='section-title' style='color:{SDR_DARK};'>Situation de l'équipe à la session : {session_end}</h3>", unsafe_allow_html=True)
        df_end_snap = df_target[df_target[time_col] == session_end].dropna(subset=[selected_var]).sort_values(by=selected_var, ascending=True)
        
        if not df_end_snap.empty:
            fig_snap = px.bar(df_end_snap, x=selected_var, y='Joueur', orientation='h', text_auto='.1f', color_discrete_sequence=[SDR_DARK])
            fig_snap.update_layout(height=max(350, len(df_end_snap)*40), margin=dict(t=20, b=20, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#e9ecef', title=selected_var), yaxis=dict(title="", tickfont=dict(weight="bold")))
            st.plotly_chart(fig_snap, use_container_width=True)
        else:
            st.info(f"Aucune donnée disponible pour la session {session_end}.")

        st.markdown("<hr style='margin: 40px 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 class='section-title' style='color:{SDR_DARK};'>Évolution globale : {selected_var}</h3>", unsafe_allow_html=True)
        
        df_mean = df_target.groupby(time_col)[selected_var].agg(['mean', 'std']).reset_index().sort_values(by=time_col)
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        if len(df_mean) >= 2:
            val_debut = df_mean.iloc[0]['mean']
            val_fin = df_mean.iloc[-1]['mean']
            pct_change = ((val_fin - val_debut) / val_debut) * 100 if val_debut != 0 else 0
            
            col_stat1.metric("Moyenne Initiale", f"{val_debut:.2f}")
            col_stat2.metric("Moyenne Finale", f"{val_fin:.2f}", f"{pct_change:.1f}%")
            col_stat3.metric("Écart-type Moyen", f"{df_mean['std'].mean():.2f}")
        
        fig_trend = go.Figure()
        
        min_y, max_y = 0, 0
        if not df_mean['std'].isna().all():
            std_filled = df_mean['std'].fillna(0)
            upper_bound = df_mean['mean'] + std_filled
            lower_bound = df_mean['mean'] - std_filled
            
            min_y = lower_bound.min()
            max_y = upper_bound.max()
            
            fig_trend.add_trace(go.Scatter(
                x=df_mean[time_col].tolist() + df_mean[time_col].tolist()[::-1],
                y=upper_bound.tolist() + lower_bound.tolist()[::-1],
                fill='toself', fillcolor='rgba(215, 25, 32, 0.15)', line=dict(color='rgba(255,255,255,0)'),
                name='Zone ±1 Écart Type', hoverinfo="skip"
            ))
        else:
            min_y = df_mean['mean'].min()
            max_y = df_mean['mean'].max()
        
        y_padding = max(max_y - min_y, max_y * 0.1) * 1.5
        if y_padding == 0: y_padding = 10
        
        fig_trend.add_trace(go.Scatter(
            x=df_mean[time_col], y=df_mean['mean'],
            mode='lines+markers', name='Moyenne',
            line=dict(color=SDR_RED, width=4), marker=dict(size=10, symbol='circle', line=dict(color='white', width=2))
        ))

        fig_trend.update_layout(
            height=450, 
            margin=dict(t=20, b=20, l=10, r=10), 
            plot_bgcolor='rgba(0,0,0,0)', 
            yaxis=dict(showgrid=True, gridcolor='#e9ecef', title=selected_var, range=[min_y - y_padding, max_y + y_padding]), 
            xaxis=dict(showgrid=True, gridcolor='#e9ecef', title="Sessions"), 
            legend=dict(orientation="h", y=1.05, x=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("<hr style='margin: 40px 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 class='section-title' style='color:{SDR_DARK};'>Palmarès de progression ({session_start} ➡️ {session_end})</h3>", unsafe_allow_html=True)
        
        df_start = df_target[df_target[time_col] == session_start][['Joueur', selected_var]].drop_duplicates('Joueur').set_index('Joueur')
        df_end = df_target[df_target[time_col] == session_end][['Joueur', selected_var]].drop_duplicates('Joueur').set_index('Joueur')
        
        all_players = df_target['Joueur'].dropna().unique()
        df_prog = pd.DataFrame(index=all_players)
        df_prog['start'] = df_start[selected_var]
        df_prog['end'] = df_end[selected_var]
        
        df_prog['Delta'] = df_prog['end'] - df_prog['start']
        df_prog['Delta'] = df_prog['Delta'].fillna(0.0)
        
        df_prog = df_prog.reset_index().rename(columns={'index': 'Joueur'}).sort_values(by='Delta', ascending=True)
        df_prog['Color'] = df_prog['Delta'].apply(lambda x: '#28a745' if x > 0 else (SDR_RED if x < 0 else '#6c757d'))
        
        fig_bar_delta = px.bar(df_prog, x='Delta', y='Joueur', orientation='h', text_auto='.1f', color='Color', color_discrete_map="identity")
        fig_bar_delta.update_layout(
            height=max(400, len(df_prog)*35), 
            margin=dict(t=20, b=20, l=10, r=10), 
            plot_bgcolor='rgba(0,0,0,0)', 
            xaxis=dict(showgrid=True, gridcolor='#e9ecef', title="Différence absolue (zéro = aucune donnée ou aucune évolution)"), 
            yaxis=dict(title="", tickfont=dict(weight="bold"))
        )
        st.plotly_chart(fig_bar_delta, use_container_width=True)

    with tab_individuel:
        joueurs_eq = sorted(df_target['Joueur'].dropna().unique())
        if not joueurs_eq:
            return
            
        st.markdown("<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        selected_player = st.selectbox("Sélectionnez un joueur :", joueurs_eq)
        st.markdown("</div>", unsafe_allow_html=True)
        
        df_player = df_target[df_target['Joueur'] == selected_player].sort_values(by=time_col).dropna(subset=[selected_var])
        
        if df_player.empty:
            st.info(f"Pas de données valides pour {selected_player} sur cet indicateur.")
            return

        st.markdown(f"<h3 class='section-title' style='color:{SDR_DARK};'>Évolution de {selected_player}</h3>", unsafe_allow_html=True)

        if len(df_player) >= 2:
            val_debut_j = df_player.iloc[0][selected_var]
            val_fin_j = df_player.iloc[-1][selected_var]
            pct_change_j = ((val_fin_j - val_debut_j) / val_debut_j) * 100 if val_debut_j != 0 else 0
            
            max_idx = df_player[selected_var].idxmax()
            val_max_j = df_player.loc[max_idx, selected_var]
            session_max_j = df_player.loc[max_idx, time_col]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Initiale ({df_player.iloc[0][time_col]})", f"{val_debut_j:.2f}")
            c2.metric(f"Finale ({df_player.iloc[-1][time_col]})", f"{val_fin_j:.2f}", f"{pct_change_j:.1f}%")
            
            ecart_moyenne = val_fin_j - df_mean.iloc[-1]['mean'] if len(df_mean) else 0
            c3.metric(f"Écart / Moy. Équipe", f"{ecart_moyenne:.2f}")
            
            c4.metric("Valeur Max Atteinte", f"{val_max_j:.2f}")
            c4.caption(f"**Session max:** {session_max_j}")

        fig_indiv = go.Figure()
        
        if 'mean' in df_mean.columns:
            fig_indiv.add_trace(go.Scatter(
                x=df_mean[time_col], y=df_mean['mean'], 
                mode='lines', name='Moyenne Équipe', 
                line=dict(color='#adb5bd', width=3, dash='dash')
            ))

        fig_indiv.add_trace(go.Scatter(
            x=df_player[time_col], y=df_player[selected_var], 
            mode='lines+markers+text', name=selected_player, 
            line=dict(color=SDR_DARK, width=4), 
            marker=dict(size=12, color='white', line=dict(color=SDR_DARK, width=3)), 
            text=df_player[selected_var].round(1), textposition='top center', textfont=dict(weight='bold', size=13)
        ))

        fig_indiv.update_layout(
            height=450, 
            margin=dict(t=20, b=20, l=10, r=10), 
            plot_bgcolor='rgba(0,0,0,0)', 
            xaxis=dict(showgrid=True, gridcolor='#e9ecef', tickfont=dict(weight="bold"), title="Sessions"), 
            yaxis=dict(showgrid=True, gridcolor='#e9ecef', title=selected_var), 
            legend=dict(orientation="h", y=1.05, x=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig_indiv, use_container_width=True)

        st.markdown("<hr style='margin: 30px 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:{SDR_DARK};'>Historique d'évolution </h4>", unsafe_allow_html=True)
        
        df_history = df_player[[time_col, selected_var]].copy()
        df_history['Évolution (vs Session Précédente)'] = df_history[selected_var].diff()
        
        if 'mean' in df_mean.columns:
            df_history = pd.merge(df_history, df_mean[[time_col, 'mean']], on=time_col, how='left').rename(columns={'mean': 'Moyenne Équipe'})
            df_history['Écart vs Moyenne'] = df_history[selected_var] - df_history['Moyenne Équipe']
            df_history['Moyenne Équipe'] = df_history['Moyenne Équipe'].round(2)
            
        df_history[selected_var] = df_history[selected_var].round(2)
        
        styled_df = df_history.style.bar(
            subset=['Évolution (vs Session Précédente)', 'Écart vs Moyenne'] if 'Écart vs Moyenne' in df_history.columns else ['Évolution (vs Session Précédente)'], 
            align='mid', 
            color=['#D71920', '#28a745']
        ).format(precision=2, na_rep="-")
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)