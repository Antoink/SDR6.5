import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.metrics import silhouette_score
from scipy.spatial import ConvexHull, QhullError
from sklearn.impute import SimpleImputer

SDR_RED = "#D71920"

def show_clustering_page(df_raw):
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: #f4f6f9;
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #111 !important;
            font-weight: 900 !important;
            letter-spacing: -0.02em;
            text-transform: uppercase;
        }}

        div.stButton > button:first-child {{
            background-color: {SDR_RED};
            color: white;
            border-radius: 8px;
            font-weight: 900;
            padding: 0.6rem 1.2rem;
            border: none;
            box-shadow: 0 4px 10px rgba(215, 25, 32, 0.2);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        div.stButton > button:first-child:hover {{
            background-color: #b0141a;
            transform: translateY(-3px);
            box-shadow: 0 8px 15px rgba(215, 25, 32, 0.3);
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
            border-bottom: 2px solid #ddd;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            background-color: transparent;
            border: none;
            padding: 10px 24px;
            color: #777;
            font-size: 1.05rem;
            font-weight: bold;
            transition: all 0.3s ease;
            border-radius: 8px 8px 0 0;
            text-transform: uppercase;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {SDR_RED};
            background-color: #fef5f5;
        }}
        .stTabs [aria-selected="true"] {{
            border-bottom: 4px solid {SDR_RED} !important;
            color: {SDR_RED} !important;
            font-weight: 900;
            background-color: transparent;
        }}

        .info-box {{
            background-color: #ffffff;
            padding: 20px;
            border-left: 5px solid {SDR_RED};
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            border: 1px solid #eee;
            color: #444;
            line-height: 1.6;
            font-size: 1rem;
            transition: transform 0.2s;
        }}
        .info-box:hover {{
            transform: translateY(-2px);
        }}
        
        .metric-card {{
            background-color: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            text-align: center;
            border: 1px solid #f0f0f0;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(215, 25, 32, 0.15);
            border-color: {SDR_RED};
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 900;
            color: {SDR_RED};
            margin: 0 0 5px 0;
        }}
        .metric-label {{
            font-size: 0.85rem;
            font-weight: bold;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
        }}
        .metric-title {{
            font-size: 1.3rem;
            font-weight: 900;
            color: #111;
            margin-top: 15px;
            text-transform: uppercase;
        }}

        .stMultiSelect > div > div, .stSelectbox > div > div {{
            border-radius: 6px !important;
            border-color: #ddd !important;
            background-color: #ffffff !important;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.02);
        }}
        .stMultiSelect > div > div:hover, .stSelectbox > div > div:hover {{
            border-color: {SDR_RED} !important;
        }}
        .stMultiSelect > div > div:focus-within, .stSelectbox > div > div:focus-within {{
            border-color: {SDR_RED} !important;
            box-shadow: 0 0 0 1px {SDR_RED} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    if df_raw.empty or "Joueur" not in df_raw.columns:
        st.warning("Données insuffisantes ou colonne 'Joueur' manquante.")
        return

    df_raw = df_raw.dropna(subset=['Joueur']).copy()

    vars_kine_sol = [
        "Knee to wall D", "Sit and reach",
        "Nordic G", "Nordic D",
        "Inverseur G", "Inverseur D", "Everseur G", "Everseur D",
        "Endurance Heel Raise G", "Endurance Heel Raise D"
    ]
    
    vars_iso = [
        "Somme ADD", "Adducteur G", "Adducteur D", 
        "Somme ABD", "Abducteur G", "Abducteur D", "Ratio Squeeze (ADD/ABD)"
    ]
    
    vars_biodex = [
        "Q G conc 60°/s", "Q G conc 60°/s (N/kg)", "Q Dt conc 60°/s", "Q Dt conc 60°/s (N/kg)", 
        "Q G conc 240°/s", "Q G conc 240°/s (N/kg)", "Q Dt conc 240°/s", "Q Dt conc 240°/s (N/kg)", 
        "IJ G conc 60°/s", "IJ G conc 60°/s (N/kg)", "IJ Dt conc 60°/s", "IJ Dt conc 60°/s (N/kg)", 
        "IJ G conc 240°/s", "IJ G conc 240°/s (N/kg)", "IJ Dt conc 240°/s", "IJ Dt conc 240°/s (N/kg)", 
        "IJ G Exc 30°/s", "IJ G Exc 30°/s (N/kg)", "IJ Dt exc 30°/s", "IJ Dt exc 30°/s (N/kg)", 
        "Ratio Mixte G", "Ratio Mixte D"
    ]
    
    vars_sauts_puissance = [
        "CMJ 2JB", "CMJ 1JB G", "CMJ 1JB D", "Drop jump",
        "Wattbike 6s (W)", "Squat belt (N)"
    ]
    
    vars_tests_terrain = [
        "VMA", "SV1", "SV2", "FC", "Temps sur 10m"
    ]
    
    vars_gps = [
        "Distance totale", "Distance HSR", "Distance Sprint (92% Vimax)", 
        "Nb Acc", "Nb Dec", "Amax", "Dmax", "Vmax"
    ]

    tab1, tab2 = st.tabs(["1. Paramétrages & Résultats", "2. Paramètres Avancés"])

    # --- FILTRAGE DE BASE (Calculé en amont pour être disponible partout) ---
    equipes_uniques = list(df_raw["Equipe"].dropna().unique()) if "Equipe" in df_raw.columns else []
    postes_uniques = list(df_raw["Position"].dropna().unique()) if "Position" in df_raw.columns else []
    sessions_uniques = list(df_raw["Session"].dropna().unique()) if "Session" in df_raw.columns else []

    with tab1:
        st.markdown(f"<h2 style='color:{SDR_RED};'>1. Ciblage de la population</h2>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: choix_equipe = st.multiselect("Équipe(s)", equipes_uniques, default=equipes_uniques)
        with col_f2: choix_poste = st.multiselect("Position(s)", postes_uniques, default=postes_uniques)
        with col_f3: choix_session = st.multiselect("Session(s)", sessions_uniques, default=sessions_uniques)

        df_filtered = df_raw.copy()
        if "Equipe" in df_filtered.columns and choix_equipe: df_filtered = df_filtered[df_filtered["Equipe"].isin(choix_equipe)]
        if "Position" in df_filtered.columns and choix_poste: df_filtered = df_filtered[df_filtered["Position"].isin(choix_poste)]
        if "Session" in df_filtered.columns and choix_session: df_filtered = df_filtered[df_filtered["Session"].isin(choix_session)]

        st.markdown("---")
        st.markdown(f"<h2 style='color:{SDR_RED};'>2. Configuration des Tests</h2>", unsafe_allow_html=True)
        
        types_profilage = [
            "Tests Kiné & Mobilité", "Force Isométrique", "Biodex (Isocinétisme)", 
            "Sauts & Puissance (Salle)", "Tests Terrain", "Données GPS"
        ]
        
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            choix_profilage = st.multiselect("Sélectionnez les batteries de tests (Sélection rapide) :", types_profilage, default=["Sauts & Puissance (Salle)", "Données GPS"])

        target_vars = []
        if "Tests Kiné & Mobilité" in choix_profilage: target_vars.extend(vars_kine_sol)
        if "Force Isométrique" in choix_profilage: target_vars.extend(vars_iso)
        if "Biodex (Isocinétisme)" in choix_profilage: target_vars.extend(vars_biodex)
        if "Sauts & Puissance (Salle)" in choix_profilage: target_vars.extend(vars_sauts_puissance)
        if "Tests Terrain" in choix_profilage: target_vars.extend(vars_tests_terrain)
        if "Données GPS" in choix_profilage: target_vars.extend(vars_gps)
        target_vars = list(dict.fromkeys(target_vars))

    with tab2:
        st.markdown(f"<h3 style='color:{SDR_RED};'>Nettoyage et Algorithmique</h3>", unsafe_allow_html=True)
        
        seuil_na = st.slider("Tolérance aux données manquantes par test (%)", 10, 90, 50, help="Si un test possède plus de X% de cases vides, il est automatiquement exclu du calcul.")
        imputation_method = st.selectbox("Méthode d'estimation des valeurs manquantes", ["KNN (Plus proches voisins)", "Moyenne de l'effectif"], help="Comment l'algorithme doit-il combler les trous pour un joueur qui a manqué un test ? Le KNN est plus précis car il s'inspire des joueurs au profil similaire.")
        
        st.markdown("---")
        st.markdown("#### Ajustement des variables")
        available_vars = [v for v in df_filtered.columns if pd.api.types.is_numeric_dtype(df_filtered[v]) and (df_filtered[v].isna().mean() * 100) <= seuil_na and v not in ['Player ID', 'Age', 'Numero', 'N° GPS', 'Date de Naissance']]
        default_actives = [v for v in target_vars if v in available_vars]

        vars_pca_actives = st.multiselect(
            "Ajoutez ou retirez manuellement des variables de la sélection :", available_vars, default=default_actives
        )

    with tab1: # Retour au tab 1 pour le calcul final et le bouton
        best_k = 3
        if len(vars_pca_actives) >= 2 and len(df_filtered) >= 4:
            try:
                temp_df = df_filtered[vars_pca_actives].apply(pd.to_numeric, errors='coerce').dropna(how='all')
                if len(temp_df) >= 4:
                    # Imputation rapide pour l'estimation du K
                    X_temp = KNNImputer(n_neighbors=min(3, len(temp_df))).fit_transform(temp_df)
                    X_temp_scaled = StandardScaler().fit_transform(X_temp)
                    
                    best_score = -1
                    for k in range(2, min(6, len(X_temp_scaled))):
                        score = silhouette_score(X_temp_scaled, KMeans(n_clusters=k, n_init='auto', random_state=42).fit_predict(X_temp_scaled))
                        if score > best_score:
                            best_k, best_score = k, score
            except:
                pass

        with col_p2:
            n_clusters = st.number_input("Nombre de groupes à créer :", min_value=2, max_value=8, value=best_k, help="Calculé automatiquement pour maximiser la pertinence statistique, mais modifiable.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LANCER L'ANALYSE", use_container_width=True):
            if len(vars_pca_actives) < 2:
                st.error("Sélectionnez au minimum 2 tests ou variables.")
            else:
                with st.spinner('Entraînement de l\'algorithme en cours...'):
                    cols_to_keep = ['Joueur']
                    if 'Session' in df_filtered.columns: cols_to_keep.append('Session')
                    if 'Position' in df_filtered.columns: cols_to_keep.append('Position')
                    cols_to_keep.extend(vars_pca_actives)
                    
                    df_analyse = df_filtered[cols_to_keep].copy().replace(r'^\s*$', np.nan, regex=True)
                    for col in vars_pca_actives: 
                        df_analyse[col] = pd.to_numeric(df_analyse[col], errors='coerce')
                    df_analyse = df_analyse.dropna(subset=vars_pca_actives, how='all').reset_index(drop=True)
                    
                    if len(df_analyse) >= n_clusters:
                        X = df_analyse[vars_pca_actives]
                        
                        # Application du paramètre avancé d'imputation
                        if imputation_method == "Moyenne de l'effectif":
                            imputed_data = SimpleImputer(strategy='mean').fit_transform(X)
                        else:
                            imputed_data = KNNImputer(n_neighbors=min(3, len(X))).fit_transform(X)
                            
                        # Standardisation indispensable avant le K-Means et la PCA
                        X_imputed_scaled = StandardScaler().fit_transform(imputed_data)

                        df_analyse['Cluster'] = KMeans(n_clusters=n_clusters, n_init='auto', random_state=42).fit_predict(X_imputed_scaled) + 1
                        df_analyse['Cluster'] = df_analyse['Cluster'].astype(str)
                        
                        pca = PCA()
                        pca_result = pca.fit_transform(X_imputed_scaled)
                        
                        st.session_state.update({
                            'df_analyse_complet': df_filtered, 'df_analyse': df_analyse, 'X_scaled': X_imputed_scaled,
                            'vars_pca_actives': vars_pca_actives,
                            'pca_model': pca, 'pca_result': pca_result, 'analyse_terminee': True
                        })
                    else:
                        st.error("Volume de données insuffisant : le nombre de joueurs valides est inférieur au nombre de groupes demandé.")

        if st.session_state.get('analyse_terminee', False):
            st.markdown("---")
            df_analyse, pca = st.session_state['df_analyse'], st.session_state['pca_model']
            vars_pca_actives, pca_result = st.session_state['vars_pca_actives'], st.session_state['pca_result']
            
            if hasattr(pca, 'n_components_'):
                n_comp = pca.n_components_

                def get_symbol(poste):
                    p = str(poste).lower()
                    if 'def' in p or 'déf' in p: return 'circle'
                    elif 'att' in p: return 'triangle-up'
                    elif 'mil' in p: return 'square'
                    elif 'gar' in p: return 'diamond'
                    return 'circle'
                
                def get_poste_category(poste):
                    p = str(poste).lower()
                    if 'def' in p or 'déf' in p: return 'Défenseur'
                    elif 'att' in p: return 'Attaquant'
                    elif 'mil' in p: return 'Milieu'
                    elif 'gar' in p: return 'Gardien'
                    return 'Non défini'

                st.markdown(f"<h3 style='color:{SDR_RED};'>Projection des individus (Espace multidimensionnel ACP)</h3>", unsafe_allow_html=True)

                st.markdown("""
                <div style='background-color: #ffffff; padding: 12px 18px; border-radius: 8px; border: 1px solid #e2e8f0; display: inline-block; margin-bottom: 24px;'>
                    <strong style='color: #111;'>Légende des postes :</strong>&nbsp;&nbsp;&nbsp;
                    <span style='font-size: 1.2em; color: #888;'>●</span> Défenseurs &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style='font-size: 1.2em; color: #888;'>▲</span> Attaquants &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style='font-size: 1.2em; color: #888;'>■</span> Milieux &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style='font-size: 1.2em; color: #888;'>◆</span> Gardiens
                </div>
                """, unsafe_allow_html=True)

                if n_comp >= 2:
                    col_x, col_y, col_vide = st.columns([1, 1, 2])
                    with col_x: dim_x = st.selectbox("Composante X", range(1, n_comp + 1), index=0, key="dimx")
                    with col_y: dim_y = st.selectbox("Composante Y", range(1, n_comp + 1), index=1, key="dimy")

                    df_analyse['PCA_X'], df_analyse['PCA_Y'] = pca_result[:, dim_x - 1], pca_result[:, dim_y - 1]
                    df_analyse['Catégorie Poste'] = df_analyse['Position'].apply(get_poste_category) if 'Position' in df_analyse.columns else 'Non défini'

                    fig_pca_map = go.Figure()
                    colors = [SDR_RED, "#111111", "#888888", "#F39C12", "#27AE60", "#3498DB", "#9B59B6", "#34495E"]
                    
                    for idx, c in enumerate(sorted(df_analyse['Cluster'].unique())):
                        df_c = df_analyse[df_analyse['Cluster'] == c]
                        color = colors[idx % len(colors)]
                        
                        if len(df_c) >= 3:
                            try:
                                pts = df_c[['PCA_X', 'PCA_Y']].values
                                hull = ConvexHull(pts)
                                hull_pts = np.append(pts[hull.vertices], [pts[hull.vertices][0]], axis=0)
                                fig_pca_map.add_trace(go.Scatter(x=hull_pts[:, 0], y=hull_pts[:, 1], mode='lines', fill='toself', fillcolor=color, opacity=0.15, line=dict(color=color, width=1, dash='dot'), showlegend=False, hoverinfo='skip'))
                            except QhullError: pass
                        
                        symbols = df_c['Position'].apply(get_symbol).tolist() if 'Position' in df_c.columns else 'circle'
                        fig_pca_map.add_trace(go.Scatter(
                            x=df_c['PCA_X'], y=df_c['PCA_Y'], mode='markers+text', name=f"Classe {c}", 
                            text=df_c['Joueur'], textposition="top center", 
                            marker=dict(size=14, color=color, symbol=symbols, line=dict(width=1.5, color='white')), 
                            hovertemplate='<b>%{text}</b><br>Classe: '+str(c)+'<br>Poste: %{customdata}<extra></extra>', customdata=df_c['Catégorie Poste']
                        ))

                    fig_pca_map.update_layout(
                        xaxis_title=f'Composante {dim_x} ({pca.explained_variance_ratio_[dim_x-1]:.1%} de la variance)', 
                        yaxis_title=f'Composante {dim_y} ({pca.explained_variance_ratio_[dim_y-1]:.1%} de la variance)', 
                        height=550, template="plotly_white", hovermode="closest", 
                        legend=dict(title="Classes (K-Means)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_pca_map, use_container_width=True)

                    st.markdown("---")
                    
                    st.markdown(f"<h3 style='color:{SDR_RED};'>Analyse des Vecteurs Propres (Cercle des Corrélations)</h3>", unsafe_allow_html=True)
                    
                    fig_circle = go.Figure()
                    fig_circle.add_shape(type="circle", xref="x", yref="y", x0=-1, y0=-1, x1=1, y1=1, line_color="#cbd5e1", line_width=2)
                    fig_circle.add_hline(y=0, line_dash="dash", line_color="#94a3b8", opacity=0.8)
                    fig_circle.add_vline(x=0, line_dash="dash", line_color="#94a3b8", opacity=0.8)

                    loadings_x = pca.components_[dim_x-1] * np.sqrt(pca.explained_variance_[dim_x-1])
                    loadings_y = pca.components_[dim_y-1] * np.sqrt(pca.explained_variance_[dim_y-1])
                    
                    for i in range(len(vars_pca_actives)): 
                        fig_circle.add_shape(type='line', x0=0, y0=0, x1=loadings_x[i], y1=loadings_y[i], line=dict(color='rgba(17, 17, 17, 0.4)', width=2))
                    
                    fig_circle.add_trace(go.Scatter(
                        x=loadings_x, y=loadings_y, mode='markers+text', text=vars_pca_actives, textposition="top center", 
                        marker=dict(size=10, color=SDR_RED, symbol='diamond', line=dict(width=1, color='white')), name='Variables', 
                        hovertemplate='<b>%{text}</b><br>Coeff CP X: %{x:.2f}<br>Coeff CP Y: %{y:.2f}<extra></extra>'
                    ))
                    
                    fig_circle.update_layout(
                        xaxis=dict(range=[-1.2, 1.2], scaleanchor="y", scaleratio=1, zeroline=False, showgrid=False), 
                        yaxis=dict(range=[-1.2, 1.2], zeroline=False, showgrid=False), 
                        height=600, template="plotly_white", showlegend=False, margin=dict(t=30, b=30, l=30, r=30)
                    )
                    st.plotly_chart(fig_circle, use_container_width=True)
                    
                    st.markdown("---")
                    
                    st.markdown(f"<h3 style='color:{SDR_RED};'>Histogramme des Valeurs Propres</h3>", unsafe_allow_html=True)
                    
                    var_exp = pd.DataFrame({'Composante': [f"CP {i+1}" for i in range(n_comp)], 'Variance (%)': pca.explained_variance_ratio_ * 100})
                    fig_var = px.bar(var_exp, x='Composante', y='Variance (%)', text_auto='.1f', color='Variance (%)', color_continuous_scale=['#D71920', '#111111'])
                    fig_var.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False)
                    fig_var.update_layout(coloraxis_showscale=False, template="plotly_white", height=350, xaxis_title="", yaxis_title="Variance expliquée (%)")
                    st.plotly_chart(fig_var, use_container_width=True)

                st.markdown("---")
                st.markdown(f"<h3 style='color:{SDR_RED};'>Analyse détaillée par Classe</h3>", unsafe_allow_html=True)
                diff_pct = ((df_analyse.groupby('Cluster')[vars_pca_actives].mean() - df_analyse[vars_pca_actives].mean()) / df_analyse[vars_pca_actives].mean() * 100)
                
                tabs_clusters = st.tabs([f"Classe {c}" for c in sorted(df_analyse['Cluster'].unique())])
                for i, c in enumerate(sorted(df_analyse['Cluster'].unique())):
                    with tabs_clusters[i]:
                        c_diff = diff_pct.loc[c].sort_values(ascending=True)
                        
                        st.markdown(f"#### Bilan de la Classe {c}")
                        
                        fig_bar = px.bar(
                            c_diff, orientation='h', color=c_diff.values, color_continuous_scale=['#D71920', '#eeeeee', '#27AE60'], 
                            range_color=[-max(abs(c_diff.min()), abs(c_diff.max())), max(abs(c_diff.min()), abs(c_diff.max()))], 
                            text=c_diff.apply(lambda x: f"{x:+.1f}%")
                        )
                        fig_bar.add_vline(x=0, line_width=2, line_color="#111", line_dash="dash")
                        fig_bar.update_traces(textposition='outside')
                        fig_bar.update_layout(
                            title="Distance relative au barycentre global (%)",
                            xaxis_title="", yaxis_title="", coloraxis_showscale=False, template="plotly_white", 
                            height=max(350, len(c_diff)*30), margin=dict(l=0, r=0, t=40, b=30)
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)

                        forts_series = c_diff[c_diff > 0]
                        faibles_series = c_diff[c_diff < 0]
                        
                        if len(forts_series) > 0:
                            forts_text = f"Cette classe présente des valeurs significativement supérieures à la moyenne globale sur les variables : **{', '.join(forts_series.tail(min(3, len(forts_series))).index.tolist())}**."
                        else:
                            forts_text = "Aucune valeur significativement supérieure à la moyenne."
                            
                        if len(faibles_series) > 0:
                            faibles_text = f"Cette classe est caractérisée par des valeurs inférieures à la moyenne sur les axes : **{', '.join(faibles_series.head(min(3, len(faibles_series))).index.tolist())}**."
                        else:
                            faibles_text = "Aucun déficit significatif identifié."
                        
                        col_fort, col_faible = st.columns(2)
                        with col_fort: st.info(f"**Valeurs > Moyenne :**\n\n{forts_text}")
                        with col_faible: st.error(f"**Valeurs < Moyenne :**\n\n{faibles_text}")
                            
                        joueurs_du_groupe = df_analyse[df_analyse['Cluster'] == c]['Joueur'].unique().tolist()
                        st.markdown(f"**Individus constituant la classe ({len(joueurs_du_groupe)}) :**")
                        st.markdown(", ".join(sorted(joueurs_du_groupe)))

            st.markdown("---")
            st.markdown(f"<h3 style='color:{SDR_RED};'>Recherche de Similarités (Distance Euclidienne via ACP)</h3>", unsafe_allow_html=True)
            
            joueurs_dispos = df_analyse['Joueur'].unique()
            col_in1, col_in2 = st.columns([1, 2])
            with col_in1: joueur_cible = st.selectbox("Individu de référence :", joueurs_dispos)

            if joueur_cible:
                idx_cible = df_analyse.index[df_analyse['Joueur'] == joueur_cible].tolist()[-1]
                target_pca = pca_result[idx_cible]
                distances = np.linalg.norm(pca_result - target_pca, axis=1)
                max_dist = distances.max()
                similarites = 100 * (1 - (distances / max_dist)) if max_dist > 0 else np.full(len(distances), 100)
                
                df_sim_calc = df_analyse[['Joueur']].copy()
                df_sim_calc['Distance'], df_sim_calc['Indice de similarité (%)'] = distances, np.round(similarites, 1)
                
                df_top = df_sim_calc[df_sim_calc['Joueur'] != joueur_cible].sort_values('Distance').drop_duplicates(subset=['Joueur']).head(3)
                
                st.markdown(f"#### Voisins les plus proches (Basé sur les {len(vars_pca_actives)} variables)")
                cols_m = st.columns(3)
                for i, (idx, row) in enumerate(df_top.iterrows()): 
                    with cols_m[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 class="metric-value">{row['Indice de similarité (%)']}%</h3>
                            <p class="metric-label">Rang {i+1}</p>
                            <h4 class="metric-title">{row['Joueur']}</h4>
                        </div>
                        """, unsafe_allow_html=True)

                if not df_top.empty:
                    st.markdown("---")
                    st.markdown("#### Représentation multidimensionnelle radiale")
                    col_sel_comp, col_vide2 = st.columns([1, 2])
                    with col_sel_comp: joueur_comp = st.selectbox("Sélection de l'individu à comparer :", df_top['Joueur'].tolist())
                        
                    idx_comp = df_top.index[df_top['Joueur'] == joueur_comp][0]
                    X_raw = df_analyse[vars_pca_actives]
                    X_radar_visuel = MinMaxScaler(feature_range=(0.1, 1)).fit_transform(X_raw.fillna(X_raw.mean()))
                    
                    df_radar = pd.DataFrame(dict(Métrique=vars_pca_actives, Cible=X_radar_visuel[idx_cible], Comparaison=X_radar_visuel[idx_comp]))
                    
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(r=df_radar['Cible'], theta=df_radar['Métrique'], fill='toself', name=joueur_cible, fillcolor=f'rgba(215, 25, 32, 0.4)', line=dict(color=SDR_RED, width=2), marker=dict(size=8)))
                    fig_radar.add_trace(go.Scatterpolar(r=df_radar['Comparaison'], theta=df_radar['Métrique'], fill='toself', name=joueur_comp, fillcolor='rgba(17, 17, 17, 0.4)', line=dict(color='#111', width=2), marker=dict(size=8)))
                    
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=False, range=[0, 1]), angularaxis=dict(gridcolor='#eee', linecolor='#eee')), 
                        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5), 
                        height=600, template="plotly_white", margin=dict(t=80, b=40)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)