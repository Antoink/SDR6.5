import streamlit as st
import pandas as pd
import plotly.graph_objects as go

SDR_RED = "#D71920"
SDR_DARK = "#2B2B2B"

def show_evolution_page(df_unfiltered):
    # On force la date exacte pour l'axe chronologique de l'évolution
    time_col = "Session exact" if "Session exact" in df_unfiltered.columns else "Session"
    
    if not time_col:
        st.error("Erreur : La colonne 'Session exact' ou 'Session' est introuvable dans votre fichier.")
        return
        
    # On s'assure que Pandas trie bien par ordre chronologique (et pas alphabétique)
    if time_col == "Session exact" and not pd.api.types.is_datetime64_any_dtype(df_unfiltered[time_col]):
        df_unfiltered[time_col] = pd.to_datetime(df_unfiltered[time_col], errors='coerce', dayfirst=True)
        # On remet en format texte lisible JJ/MM/AAAA pour l'affichage propre
        df_unfiltered[time_col] = df_unfiltered[time_col].dt.strftime('%d/%m/%Y')

    st.markdown(f"""
    <style>
    .stSelectbox label {{ font-weight: bold; color: {SDR_DARK}; }}
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

    # 1. Nettoyage des colonnes pour les KPIs
    cols_exclues = ["Player ID", "Age", "Numero", "N° GPS", "Date de Naissance", "Taille (cm)", "Poids (kg)", "Masse grasse", time_col, "Session exact"]
    numeric_cols = [c for c in df_unfiltered.columns if c not in cols_exclues and pd.api.types.is_numeric_dtype(df_unfiltered[c])]

    # 2. Interface Utilisateur simplifiée
    st.markdown("<div style='background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    col_joueur, col_var = st.columns(2)
    
    all_players = sorted(df_unfiltered['Joueur'].dropna().unique())
    with col_joueur:
        selected_player = st.selectbox("Sélectionnez un joueur :", all_players)
        
    with col_var:
        selected_var = st.selectbox("Indicateur :", sorted(numeric_cols) if numeric_cols else ["Aucun indicateur"])
        
    st.markdown("</div>", unsafe_allow_html=True)

    if not selected_player or selected_var == "Aucun indicateur":
        return

    # 3. Filtrage et calculs
    df_player = df_unfiltered[df_unfiltered['Joueur'] == selected_player].sort_values(by=time_col).dropna(subset=[selected_var])
    df_mean = df_unfiltered.groupby(time_col)[selected_var].mean().reset_index().sort_values(by=time_col)

    if df_player.empty:
        st.info(f"Pas de données valides pour {selected_player} sur cet indicateur ({selected_var}).")
        return

    st.markdown(f"<h3 class='section-title' style='color:{SDR_DARK};'>Évolution de {selected_player} : {selected_var}</h3>", unsafe_allow_html=True)

    # 4. En-tête : Métriques rapides
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
        
        ecart_moyenne = val_fin_j - df_mean.iloc[-1][selected_var] if not df_mean.empty else 0
        c3.metric(f"Écart / Moy. Équipe actuelle", f"{ecart_moyenne:.2f}")
        
        c4.metric("Valeur Max Atteinte", f"{val_max_j:.2f}")
        c4.caption(f"**Session exact :** {session_max_j}")

    # 5. Graphique d'évolution
    # 5. Graphique d'évolution
    fig_indiv = go.Figure()
    
    # --- CALCUL DU PADDING POUR "DÉZOOMER" L'AXE Y ---
    min_val = df_player[selected_var].min()
    max_val = df_player[selected_var].max()
    
    if not df_mean.empty:
        min_val = min(min_val, df_mean[selected_var].min())
        max_val = max(max_val, df_mean[selected_var].max())
        
    delta = max_val - min_val
    padding = delta * 0.15 if delta > 0 else (max_val * 0.1 if max_val != 0 else 1)
    # ------------------------------------------------

    if not df_mean.empty:
        fig_indiv.add_trace(go.Scatter(
            x=df_mean[time_col], y=df_mean[selected_var], 
            mode='lines', name='Moyenne Équipe', 
            line=dict(color='#adb5bd', width=3, dash='dash'),
            hoverinfo='text',
            hovertext=[f"Moyenne Équipe : {val:.2f}" for val in df_mean[selected_var]]
        ))

    fig_indiv.add_trace(go.Scatter(
        x=df_player[time_col], y=df_player[selected_var], 
        mode='lines+markers+text', name=selected_player, 
        line=dict(color=SDR_DARK, width=4), 
        marker=dict(size=12, color=SDR_RED, line=dict(color='white', width=2)), 
        text=df_player[selected_var].round(1), textposition='top center', textfont=dict(weight='bold', size=13)
    ))

    fig_indiv.update_layout(
        height=450, 
        margin=dict(t=30, b=20, l=10, r=10), 
        plot_bgcolor='rgba(0,0,0,0)', 
        xaxis=dict(showgrid=True, gridcolor='#e9ecef', tickfont=dict(weight="bold"), title="Sessions"), 
        yaxis=dict(showgrid=True, gridcolor='#e9ecef', title=selected_var, range=[min_val - padding, max_val + padding]), 
        legend=dict(orientation="h", y=1.05, x=0),
        hovermode="x unified"
    )
    st.plotly_chart(fig_indiv, use_container_width=True)

    # 6. Tableau Historique Détaillé
    st.markdown("<hr style='margin: 30px 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color:{SDR_DARK};'>Historique des données</h4>", unsafe_allow_html=True)
    
    df_history = df_player[[time_col, selected_var]].copy()
    df_history['Évolution (vs Session Précédente)'] = df_history[selected_var].diff()
    
    if not df_mean.empty:
        df_history = pd.merge(df_history, df_mean[[time_col, selected_var]], on=time_col, how='left', suffixes=('', '_moy')).rename(columns={f"{selected_var}_moy": 'Moyenne Équipe'})
        df_history['Écart vs Moyenne'] = df_history[selected_var] - df_history['Moyenne Équipe']
        df_history['Moyenne Équipe'] = df_history['Moyenne Équipe'].round(2)
        
    df_history[selected_var] = df_history[selected_var].round(2)
    
    styled_df = df_history.style.bar(
        subset=['Évolution (vs Session Précédente)', 'Écart vs Moyenne'] if 'Écart vs Moyenne' in df_history.columns else ['Évolution (vs Session Précédente)'], 
        align='mid', 
        color=['#D71920', '#28a745']
    ).format(precision=2, na_rep="-")
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)