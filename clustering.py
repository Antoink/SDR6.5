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

SDR_RED = "#D71920"
SUP_BLUE = "#3498DB"

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
        .metric-card {{
            background-color: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            text-align: center;
            border: 1px solid #f0f0f0;
            transition: all 0.3s ease;
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
        </style>
    """, unsafe_allow_html=True)

    with st.expander("🎓 Guide de l'analyse et du profilage des données", expanded=True):
        st.markdown("""
        Ce module d'apprentissage non supervisé propose **deux modes d'analyse** : Profiler les joueurs ou regrouper les tests physiques.

        **1. Mode : Profilage Joueurs (Lignes)**
        *   **Le principe :** Mesure les distances entre les joueurs dans l'espace des données pour les rassembler.
        *   **L'objectif :** Former des clusters de joueurs aux profils athlétiques homogènes.
        *   **L'intérêt :** Individualiser les séances, repérer des profils similaires (distance Euclidienne et radar) et anticiper les besoins d'effectif.

        **2. Mode : Analyse des Tests (Colonnes)**
        *   **Le principe :** Inverse la matrice mathématique pour mesurer la distance entre les variables elles-mêmes.
        *   **L'objectif :** Regrouper les tests physiques qui se ressemblent et évaluent les mêmes qualités athlétiques.
        *   **L'intérêt :** Faire le tri dans les batteries de tests, identifier les doublons (multicolinéarité) et comprendre quelles évaluations pèsent sur les mêmes dimensions physiques.

        **3. L'Analyse en Composantes Principales (ACP)**
        *   **L'objectif :** Passer d'un espace multidimensionnel complexe à un graphique en 2D lisible, tout en conservant un maximum d'information (variance).
        *   **Variables Supplémentaires :** Les variables quantitatives supplémentaires sont projetées en pointillés sur le cercle des corrélations. Les variables qualitatives (Poste, Equipe) servent de filtres contextuels sans fausser le calcul.
        """)

    # --- CONTOURNEMENT DU FILTRE GLOBAL ---
    try:
        df_full = pd.read_excel("Profilage 2026-2027.xlsx", sheet_name=0)
        if not df_full.empty and "Joueur" in df_full.columns:
            df_raw = df_full.copy()
    except Exception:
        pass # Si échec, on utilise le df_raw passé en paramètre

    if df_raw.empty or "Joueur" not in df_raw.columns:
        st.warning("Données insuffisantes ou colonne 'Joueur' manquante.")
        return

    df_raw = df_raw.dropna(subset=['Joueur']).copy()

    # Nettoyage des équipes pour éviter les doublons invisibles
    if "Equipe" in df_raw.columns:
        df_raw["Equipe"] = df_raw["Equipe"].astype(str).str.strip().str.upper()
        df_raw["Equipe"] = df_raw["Equipe"].replace({'NAN': np.nan, 'NONE': np.nan})
        equipes_uniques = sorted(list(df_raw["Equipe"].dropna().unique()))
    else:
        equipes_uniques = []
        
    postes_uniques = list(df_raw["Position"].dropna().unique()) if "Position" in df_raw.columns else []
    sessions_uniques = list(df_raw["Session"].dropna().unique()) if "Session" in df_raw.columns else []

    st.markdown(f"<h2 style='color:{SDR_RED};'>1. Ciblage de la population</h2>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: choix_equipe = st.multiselect("Équipe(s)", equipes_uniques, default=equipes_uniques)
    with col_f2: choix_poste = st.multiselect("Position(s)", postes_uniques, default=postes_uniques)
    with col_f3: choix_session = st.multiselect("Session(s)", sessions_uniques, default=sessions_uniques)

    df_filtered = df_raw.copy()
    if "Equipe" in df_filtered.columns and choix_equipe: df_filtered = df_filtered[df_filtered["Equipe"].isin(choix_equipe)]
    if "Position" in df_filtered.columns and choix_poste: df_filtered = df_filtered[df_filtered["Position"].isin(choix_poste)]
    if "Session" in df_filtered.columns and choix_session: df_filtered = df_filtered[df_filtered["Session"].isin(choix_session)]
    
    colonnes_texte = ['Joueur', 'N° GPS', 'Latéralité', 'Poste', 'Position', 'Date de Naissance', 'Equipe', 'Session exact', 'Session', 'Player ID']
    for col in df_filtered.columns:
        if col not in colonnes_texte:
            try:
                df_filtered[col] = df_filtered[col].astype(str).str.replace(',', '.')
            except:
                pass
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    st.markdown("---")
    st.markdown(f"<h2 style='color:{SDR_RED};'>2. Sélection des Variables</h2>", unsafe_allow_html=True)
    
    seuil_na = st.slider("Tolérance aux données manquantes par test (%)", 10, 100, 95)
    
    colonnes_interdites = [
        'Joueur', 'Player ID', 'N° GPS', 'Latéralité', 'Poste', 'Position', 
        'Date de Naissance', 'DT exact', 'Session exact', 'Session', 'Equipe', 'Numero'
    ]
    
    available_vars = [
        v for v in df_filtered.columns 
        if pd.api.types.is_numeric_dtype(df_filtered[v]) 
        and (df_filtered[v].isna().mean() * 100) <= seuil_na 
        and v not in colonnes_interdites
    ]
    
    vars_pca_actives = st.multiselect(
        "Variables quantitatives ACTIVES (Servent au calcul de l'ACP) :", 
        available_vars, 
        default=available_vars[:5] if len(available_vars)>=5 else available_vars
    )

    vars_sup_quant = st.multiselect(
        "Variables quantitatives SUPPLÉMENTAIRES (Affichées en pointillés, ignorées dans le calcul) :", 
        [v for v in available_vars if v not in vars_pca_actives]
    )

    colonnes_qualitatives = [col for col in df_filtered.columns if col in colonnes_texte and col != 'Joueur']
    vars_sup_actives = st.multiselect(
        "Variables de contexte pour l'affichage (Qualitatives) :", 
        colonnes_qualitatives, 
        default=[c for c in ['Poste', 'Position', 'Session', 'Equipe'] if c in colonnes_qualitatives]
    )

    best_k = 3
    if len(vars_pca_actives) >= 2:
        temp_df = df_filtered[vars_pca_actives].apply(pd.to_numeric, errors='coerce').dropna(how='any')
        if len(temp_df) > 0:
            corr_matrix = temp_df.corr().abs()
            np.fill_diagonal(corr_matrix.values, 0)
            if (corr_matrix > 0.85).any().any():
                st.warning("⚠️ Multicolinéarité détectée : Certaines variables ACTIVES sont fortement corrélées (> 0.85). Il peut être utile d'utiliser le mode 'Analyse des Tests' pour les identifier.")
            if len(temp_df) < len(vars_pca_actives) * 3:
                st.warning(f"⚠️ Échantillon faible : Vous analysez {len(vars_pca_actives)} variables avec seulement {len(temp_df)} joueurs complets.")

            try:
                if len(temp_df) >= 4:
                    X_temp = KNNImputer(n_neighbors=min(3, len(temp_df))).fit_transform(temp_df)
                    X_temp_scaled = StandardScaler().fit_transform(X_temp)
                    best_score = -1
                    for k in range(2, min(6, len(X_temp_scaled))):
                        score = silhouette_score(X_temp_scaled, KMeans(n_clusters=k, n_init='auto', random_state=42).fit_predict(X_temp_scaled))
                        if score > best_score:
                            best_k, best_score = k, score
            except:
                pass

    st.markdown("---")
    st.markdown(f"<h2 style='color:{SDR_RED};'>3. Paramétrage de l'Analyse</h2>", unsafe_allow_html=True)
    
    col_mode, col_clusters, col_btn = st.columns([2, 1, 1])
    with col_mode:
        mode_analyse = st.radio("Cible de l'algorithme K-Means :", ["👤 Profilage Joueurs (Regrouper les individus)", "📊 Analyse des Tests (Regrouper les variables)"])
    with col_clusters:
        n_clusters = st.number_input("Nombre de groupes", min_value=2, max_value=8, value=best_k)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_run = st.button("LANCER L'ANALYSE", use_container_width=True)

    if btn_run:
        if len(vars_pca_actives) < 2:
            st.error("Sélectionnez au minimum 2 variables actives.")
        else:
            with st.spinner('Calcul de l\'ACP et clustering en cours...'):
                cols_to_keep = ['Joueur'] + vars_sup_actives + vars_pca_actives + vars_sup_quant
                cols_to_keep = list(dict.fromkeys(cols_to_keep)) 
                
                df_analyse = df_filtered[cols_to_keep].copy().replace(r'^\s*$', np.nan, regex=True)
                
                for col in vars_pca_actives + vars_sup_quant: 
                    df_analyse[col] = pd.to_numeric(df_analyse[col], errors='coerce')
                
                df_analyse = df_analyse.dropna(subset=vars_pca_actives, how='any').reset_index(drop=True)
                
                if len(df_analyse) >= max(n_clusters, 2):
                    X = df_analyse[vars_pca_actives]
                    X_scaled = StandardScaler().fit_transform(X)
                    
                    pca = PCA(n_components=len(vars_pca_actives))
                    pca_result = pca.fit_transform(X_scaled)
                    
                    st.session_state.update({
                        'df_analyse_complet': df_filtered, 
                        'df_analyse': df_analyse, 
                        'X_scaled': X_scaled,
                        'vars_pca_actives': vars_pca_actives,
                        'vars_sup_quant': vars_sup_quant,
                        'pca_model': pca, 
                        'pca_result': pca_result, 
                        'analyse_terminee': True
                    })

                    # Différenciation de la cible du clustering
                    if mode_analyse == "👤 Profilage Joueurs (Regrouper les individus)":
                        df_analyse['Cluster'] = KMeans(n_clusters=n_clusters, n_init='auto', random_state=42).fit_predict(X_scaled) + 1
                        df_analyse['Cluster'] = df_analyse['Cluster'].astype(str)
                        st.session_state['mode_run'] = 'joueurs'
                        
                    else: # Mode variables
                        var_clusters = KMeans(n_clusters=n_clusters, n_init='auto', random_state=42).fit_predict(X_scaled.T) + 1
                        df_vars = pd.DataFrame({'Variable': vars_pca_actives, 'Cluster': var_clusters.astype(str)})
                        st.session_state['df_vars'] = df_vars
                        st.session_state['mode_run'] = 'tests'
                        
                else:
                    st.error(f"Volume de données insuffisant : {len(df_analyse)} joueur(s) valides.")

    # ================= AFFICHAGE DES RÉSULTATS =================
    if st.session_state.get('analyse_terminee', False):
        st.markdown("---")
        df_analyse, pca = st.session_state['df_analyse'], st.session_state['pca_model']
        vars_pca_actives = st.session_state['vars_pca_actives']
        vars_sup_quant = st.session_state.get('vars_sup_quant', [])
        pca_result = st.session_state['pca_result']
        mode_run = st.session_state.get('mode_run', 'joueurs')
        
        n_comp = pca.n_components_
        colors = [SDR_RED, "#111111", "#888888", "#F39C12", "#27AE60", "#3498DB", "#9B59B6", "#34495E"]

        # ----------------- MODE JOUEURS -----------------
        if mode_run == 'joueurs':
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

            st.markdown(f"<h3 style='color:{SDR_RED};'>Projection des individus (La carte des joueurs)</h3>", unsafe_allow_html=True)
            with st.expander("💡 Comment lire ce graphique ?"):
                st.markdown("""
                *   **Proximité entre joueurs :** Deux points proches représentent des joueurs aux profils physiques très semblables sur les tests sélectionnés.
                *   **Formes et Couleurs (Clusters) :** Les enveloppes colorées regroupent automatiquement les joueurs appartenant au même profil athlétique.
                *   **Formes des marqueurs :** Indique le poste terrain du joueur, ce qui permet de croiser immédiatement le profil physique avec la réalité tactique.
                """)
            
            if n_comp >= 2:
                col_x, col_y, col_vide = st.columns([1, 1, 2])
                with col_x: dim_x = st.selectbox("Composante X", range(1, n_comp + 1), index=0, key="dimx")
                with col_y: dim_y = st.selectbox("Composante Y", range(1, n_comp + 1), index=1, key="dimy")

                df_analyse['PCA_X'], df_analyse['PCA_Y'] = pca_result[:, dim_x - 1], pca_result[:, dim_y - 1]
                df_analyse['Catégorie Poste'] = df_analyse['Poste'].apply(get_poste_category) if 'Poste' in df_analyse.columns else 'Non défini'

                fig_pca_map = go.Figure()
                
                for idx, c in enumerate(sorted(df_analyse['Cluster'].unique())):
                    df_c = df_analyse[df_analyse['Cluster'] == c]
                    color = colors[int(c) % len(colors)]
                    
                    if len(df_c) >= 3:
                        try:
                            pts = df_c[['PCA_X', 'PCA_Y']].values
                            hull = ConvexHull(pts)
                            hull_pts = np.append(pts[hull.vertices], [pts[hull.vertices][0]], axis=0)
                            fig_pca_map.add_trace(go.Scatter(x=hull_pts[:, 0], y=hull_pts[:, 1], mode='lines', fill='toself', fillcolor=color, opacity=0.15, line=dict(color=color, width=1, dash='dot'), showlegend=False, hoverinfo='skip'))
                        except QhullError: pass
                    
                    symbols = df_c['Poste'].apply(get_symbol).tolist() if 'Poste' in df_c.columns else 'circle'
                    hovertemplate = '<b>%{text}</b><br>Classe: '+str(c)
                    if 'Poste' in df_c.columns: hovertemplate += '<br>Poste: %{customdata}'
                    if 'Equipe' in df_c.columns: hovertemplate += '<br>Équipe: %{customdata}' # Astuce d'affichage si nécessaire
                    
                    fig_pca_map.add_trace(go.Scatter(
                        x=df_c['PCA_X'], y=df_c['PCA_Y'], mode='markers+text', name=f"Classe {c}", 
                        text=df_c['Joueur'], textposition="top center", 
                        marker=dict(size=14, color=color, symbol=symbols, line=dict(width=1.5, color='white')), 
                        hovertemplate=hovertemplate + '<extra></extra>', customdata=df_c['Catégorie Poste']
                    ))

                fig_pca_map.update_layout(
                    xaxis_title=f'CP {dim_x} ({pca.explained_variance_ratio_[dim_x-1]:.1%})', 
                    yaxis_title=f'CP {dim_y} ({pca.explained_variance_ratio_[dim_y-1]:.1%})', 
                    height=550, template="plotly_white", hovermode="closest", 
                    legend=dict(title="Classes (K-Means)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_pca_map, use_container_width=True)

                st.markdown("---")
                st.markdown(f"<h3 style='color:{SDR_RED};'>Cercle des Corrélations</h3>", unsafe_allow_html=True)
                with st.expander("💡 Comment interpréter le cercle des corrélations ?"):
                    st.markdown("""
                    *   **Trait plein rouge :** Variables ACTIVES ayant servi au calcul.
                    *   **Traitillé bleu :** Variables SUPPLÉMENTAIRES (projetées à titre informatif).
                    *   **Longueur de la flèche :** Plus elle s'approche du bord, mieux elle est représentée.
                    *   **Flèches proches :** Corrélations positives (évoluent ensemble).
                    *   **Flèches à 90° :** Indépendance (pas de lien).
                    *   **Flèches opposées à 180° :** Anti-corrélation (évoluent en sens inverse).
                    """)
                
                fig_circle = go.Figure()
                fig_circle.add_shape(type="circle", xref="x", yref="y", x0=-1, y0=-1, x1=1, y1=1, line_color="#cbd5e1", line_width=2)
                fig_circle.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
                fig_circle.add_vline(x=0, line_dash="dash", line_color="#94a3b8")

                loadings_x = pca.components_[dim_x-1] * np.sqrt(pca.explained_variance_[dim_x-1])
                loadings_y = pca.components_[dim_y-1] * np.sqrt(pca.explained_variance_[dim_y-1])
                
                for i in range(len(vars_pca_actives)): 
                    fig_circle.add_shape(type='line', x0=0, y0=0, x1=loadings_x[i], y1=loadings_y[i], line=dict(color='rgba(17, 17, 17, 0.4)', width=2))
                
                fig_circle.add_trace(go.Scatter(
                    x=loadings_x, y=loadings_y, mode='markers+text', text=vars_pca_actives, textposition="top center", 
                    marker=dict(size=10, color=SDR_RED, symbol='diamond'), name='Variables Actives', 
                    hovertemplate='<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>'
                ))

                if vars_sup_quant:
                    sup_x, sup_y, sup_names = [], [], []
                    s_cx = pd.Series(pca_result[:, dim_x - 1])
                    s_cy = pd.Series(pca_result[:, dim_y - 1])
                    for v in vars_sup_quant:
                        s_v = df_analyse[v]
                        cx = s_v.corr(s_cx)
                        cy = s_v.corr(s_cy)
                        if pd.notna(cx) and pd.notna(cy):
                            sup_x.append(cx)
                            sup_y.append(cy)
                            sup_names.append(v)
                            fig_circle.add_shape(type='line', x0=0, y0=0, x1=cx, y1=cy, line=dict(color='rgba(52, 152, 219, 0.6)', width=2, dash='dash'))

                    if sup_x:
                        fig_circle.add_trace(go.Scatter(
                            x=sup_x, y=sup_y, mode='markers+text', text=sup_names, textposition="top center", 
                            marker=dict(size=9, color=SUP_BLUE, symbol='circle-open', line=dict(width=2)), name='Variables Supplémentaires', 
                            hovertemplate='<b>%{text} (Sup)</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>'
                        ))
                
                fig_circle.update_layout(
                    xaxis=dict(range=[-1.2, 1.2], scaleanchor="y", scaleratio=1, zeroline=False), 
                    yaxis=dict(range=[-1.2, 1.2], zeroline=False), 
                    height=600, template="plotly_white", showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_circle, use_container_width=True)

            st.markdown("---")
            st.markdown(f"<h3 style='color:{SDR_RED};'>Analyse détaillée par Classe</h3>", unsafe_allow_html=True)
            diff_pct = ((df_analyse.groupby('Cluster')[vars_pca_actives].mean() - df_analyse[vars_pca_actives].mean()) / df_analyse[vars_pca_actives].mean() * 100)
            
            tabs_clusters = st.tabs([f"Classe {c}" for c in sorted(df_analyse['Cluster'].unique())])
            for i, c in enumerate(sorted(df_analyse['Cluster'].unique())):
                with tabs_clusters[i]:
                    c_diff = diff_pct.loc[c].sort_values(ascending=True)
                    fig_bar = px.bar(
                        c_diff, orientation='h', color=c_diff.values, color_continuous_scale=['#D71920', '#eeeeee', '#27AE60'], 
                        range_color=[-max(abs(c_diff.min()), abs(c_diff.max())), max(abs(c_diff.min()), abs(c_diff.max()))], 
                        text=c_diff.apply(lambda x: f"{x:+.1f}%")
                    )
                    fig_bar.add_vline(x=0, line_width=2, line_color="#111", line_dash="dash")
                    fig_bar.update_layout(title="Distance relative au barycentre global (%)", coloraxis_showscale=False, template="plotly_white", height=max(350, len(c_diff)*30))
                    st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("---")
            st.markdown(f"<h3 style='color:{SDR_RED};'>Recherche de Similarités</h3>", unsafe_allow_html=True)
            joueurs_dispos = df_analyse['Joueur'].unique()
            joueur_cible = st.selectbox("Individu de référence :", joueurs_dispos)

            if joueur_cible:
                X_scaled_sim = st.session_state['X_scaled']
                idx_cible = df_analyse.index[df_analyse['Joueur'] == joueur_cible].tolist()[-1]
                target_vec = X_scaled_sim[idx_cible]
                distances = np.linalg.norm(X_scaled_sim - target_vec, axis=1)
                max_dist = distances.max()
                similarites = 100 * (1 - (distances / max_dist)) if max_dist > 0 else np.full(len(distances), 100)
                
                df_sim_calc = df_analyse[['Joueur']].copy()
                df_sim_calc['Distance'], df_sim_calc['Similarité (%)'] = distances, np.round(similarites, 1)
                df_top = df_sim_calc[df_sim_calc['Joueur'] != joueur_cible].sort_values('Distance').drop_duplicates(subset=['Joueur']).head(3)
                
                cols_m = st.columns(3)
                for i, (idx, row) in enumerate(df_top.iterrows()): 
                    with cols_m[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 class="metric-value">{row['Similarité (%)']}%</h3>
                            <p class="metric-label">Rang {i+1}</p>
                            <h4 class="metric-title">{row['Joueur']}</h4>
                        </div>
                        """, unsafe_allow_html=True)

                if not df_top.empty:
                    st.markdown("---")
                    joueur_comp = st.selectbox("Comparaison :", df_top['Joueur'].tolist())
                    idx_comp = df_top.index[df_top['Joueur'] == joueur_comp][0]
                    X_raw = df_analyse[vars_pca_actives]
                    X_radar_visuel = MinMaxScaler(feature_range=(0.1, 1)).fit_transform(X_raw.fillna(X_raw.mean()))
                    
                    df_radar = pd.DataFrame(dict(Métrique=vars_pca_actives, Cible=X_radar_visuel[idx_cible], Comparaison=X_radar_visuel[idx_comp], Moyenne=X_radar_visuel.mean(axis=0)))
                    df_radar = pd.concat([df_radar, df_radar.iloc[[0]]], ignore_index=True)
                    
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(r=df_radar['Cible'], theta=df_radar['Métrique'], fill='toself', name=joueur_cible, fillcolor='rgba(215, 25, 32, 0.4)', line=dict(color=SDR_RED, width=2)))
                    fig_radar.add_trace(go.Scatterpolar(r=df_radar['Comparaison'], theta=df_radar['Métrique'], fill='toself', name=joueur_comp, fillcolor='rgba(17, 17, 17, 0.4)', line=dict(color='#111', width=2)))
                    fig_radar.add_trace(go.Scatterpolar(r=df_radar['Moyenne'], theta=df_radar['Métrique'], fill='none', name='Moyenne', line=dict(color='#888', dash='dash')))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1])), height=600, template="plotly_white")
                    st.plotly_chart(fig_radar, use_container_width=True)

        # ----------------- MODE TESTS -----------------
        elif mode_run == 'tests':
            df_vars = st.session_state['df_vars']
            
            st.markdown(f"<h3 style='color:{SDR_RED};'>Composition des Groupes de Tests</h3>", unsafe_allow_html=True)
            with st.expander("💡 Comment lire ce tableau ?"):
                st.markdown("""
                L'algorithme K-Means a calculé la distance entre chaque test. Les tests qui se trouvent dans le même groupe sont ceux dont les résultats varient de la même manière chez vos joueurs. S'ils sont dans le même groupe, ils évaluent probablement la même dimension athlétique.
                """)
                
            cols_groupes = st.columns(len(df_vars['Cluster'].unique()))
            for i, c in enumerate(sorted(df_vars['Cluster'].unique())):
                with cols_groupes[i]:
                    st.markdown(f"**Groupe {c}**")
                    tests = df_vars[df_vars['Cluster'] == c]['Variable'].tolist()
                    for t in tests:
                        st.markdown(f"- {t}")

            if n_comp >= 2:
                st.markdown("---")
                st.markdown(f"<h3 style='color:{SDR_RED};'>Cercle des Corrélations (Coloré par Groupes)</h3>", unsafe_allow_html=True)
                with st.expander("💡 Comment interpréter le cercle des corrélations ?"):
                    st.markdown("""
                    *   **Flèches de même couleur :** Appartiennent au même groupe (Cluster) mathématique. Elles mesurent la même qualité physique globale.
                    *   **Longueur de la flèche :** Plus elle s'approche du bord, mieux elle est représentée sur cet axe.
                    *   **Flèches proches :** Corrélations positives (évoluent ensemble).
                    *   **Flèches opposées à 180° :** Anti-corrélation (évoluent en sens inverse, ex: vitesse vs temps).
                    """)

                col_x, col_y, col_vide = st.columns([1, 1, 2])
                with col_x: dim_x = st.selectbox("Composante X", range(1, n_comp + 1), index=0, key="dimx_test")
                with col_y: dim_y = st.selectbox("Composante Y", range(1, n_comp + 1), index=1, key="dimy_test")

                fig_circle = go.Figure()
                fig_circle.add_shape(type="circle", xref="x", yref="y", x0=-1, y0=-1, x1=1, y1=1, line_color="#cbd5e1", line_width=2)
                fig_circle.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
                fig_circle.add_vline(x=0, line_dash="dash", line_color="#94a3b8")

                loadings_x = pca.components_[dim_x-1] * np.sqrt(pca.explained_variance_[dim_x-1])
                loadings_y = pca.components_[dim_y-1] * np.sqrt(pca.explained_variance_[dim_y-1])

                for c in sorted(df_vars['Cluster'].unique()):
                    color = colors[int(c) % len(colors)]
                    vars_in_c = df_vars[df_vars['Cluster'] == c]['Variable'].tolist()
                    idx_in_c = [vars_pca_actives.index(v) for v in vars_in_c]
                    
                    x_c = loadings_x[idx_in_c]
                    y_c = loadings_y[idx_in_c]
                    
                    for i in range(len(vars_in_c)):
                         fig_circle.add_shape(type='line', x0=0, y0=0, x1=x_c[i], y1=y_c[i], line=dict(color=color, width=2.5))
                    
                    fig_circle.add_trace(go.Scatter(
                        x=x_c, y=y_c, mode='markers+text', text=vars_in_c, textposition="top center", 
                        marker=dict(size=12, color=color, symbol='diamond', line=dict(width=1, color='white')), name=f"Groupe {c}", 
                        hovertemplate='<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>'
                    ))

                if vars_sup_quant:
                    sup_x, sup_y, sup_names = [], [], []
                    s_cx = pd.Series(pca_result[:, dim_x - 1])
                    s_cy = pd.Series(pca_result[:, dim_y - 1])
                    for v in vars_sup_quant:
                        s_v = df_analyse[v]
                        cx = s_v.corr(s_cx)
                        cy = s_v.corr(s_cy)
                        if pd.notna(cx) and pd.notna(cy):
                            sup_x.append(cx)
                            sup_y.append(cy)
                            sup_names.append(v)
                            fig_circle.add_shape(type='line', x0=0, y0=0, x1=cx, y1=cy, line=dict(color='rgba(150, 150, 150, 0.5)', width=2, dash='dash'))

                    if sup_x:
                        fig_circle.add_trace(go.Scatter(
                            x=sup_x, y=sup_y, mode='markers+text', text=sup_names, textposition="top center", 
                            marker=dict(size=9, color="#999999", symbol='circle-open', line=dict(width=2)), name='Variables Supplémentaires', 
                            hovertemplate='<b>%{text} (Sup)</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>'
                        ))

                fig_circle.update_layout(
                    xaxis=dict(range=[-1.2, 1.2], scaleanchor="y", scaleratio=1, zeroline=False), 
                    yaxis=dict(range=[-1.2, 1.2], zeroline=False), 
                    height=600, template="plotly_white", showlegend=True,
                    legend=dict(title="Clusters K-Means", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_circle, use_container_width=True)

        # ----------------- COMMUN AUX DEUX MODES -----------------
        st.markdown("---")
        st.markdown(f"<h3 style='color:{SDR_RED};'>Histogramme des Valeurs Propres</h3>", unsafe_allow_html=True)
        with st.expander("💡 Que représente ce % de variance ?"):
            st.markdown("""
            *   **Variance par axe :** Le pourcentage indique la quantité d'information conservée par cet axe.
            *   **Variance cumulée :** En additionnant les % des axes choisis, vous obtenez la représentativité globale. > 60-70% offre une très bonne représentation 2D.
            """)
        
        var_exp = pd.DataFrame({'Composante': [f"CP {i+1}" for i in range(n_comp)], 'Variance (%)': pca.explained_variance_ratio_ * 100})
        fig_var = px.bar(var_exp, x='Composante', y='Variance (%)', text_auto='.1f', color='Variance (%)', color_continuous_scale=['#D71920', '#111111'])
        fig_var.update_traces(textposition="outside", cliponaxis=False)
        fig_var.update_layout(coloraxis_showscale=False, template="plotly_white", height=350)
        st.plotly_chart(fig_var, use_container_width=True)

        st.markdown("---")
        st.markdown(f"<h3 style='color:{SDR_RED};'>Matrice de contribution des variables</h3>", unsafe_allow_html=True)
        with st.expander("💡 Comment lire cette matrice ?"):
            st.markdown("""
            Cette matrice indique dans quelle dimension chaque variable est la mieux représentée (qualité de représentation $\cos^2$).
            *   **Taille et couleur du cercle :** Plus le cercle est grand et rouge, plus la variable est liée à cette composante principale (axe).
            *   Cela permet de comprendre rapidement le "sens" de chaque axe (ex: si l'axe 1 a de gros cercles pour la VMA et le 1080 Sprint, c'est l'axe de l'endurance et de la vitesse).
            """)
        
        loadings_full = pca.components_.T * np.sqrt(pca.explained_variance_)
        cos2_matrix = loadings_full**2
        dim_names = [f"CP {i+1}" for i in range(n_comp)]
        
        df_cos2 = pd.DataFrame(cos2_matrix, index=vars_pca_actives, columns=dim_names)
        df_cos2_melted = df_cos2.reset_index().melt(id_vars='index', var_name='Composante', value_name='cos2')
        df_cos2_melted.rename(columns={'index': 'Variable'}, inplace=True)
        
        fig_contrib = px.scatter(
            df_cos2_melted, 
            x='Composante', 
            y='Variable', 
            size='cos2', 
            color='cos2',
            color_continuous_scale=['#eeeeee', SDR_RED],
            size_max=25
        )
        fig_contrib.update_layout(
            coloraxis_showscale=False, 
            template="plotly_white", 
            height=max(400, len(vars_pca_actives)*35),
            xaxis=dict(showgrid=True, gridcolor='#eee'),
            yaxis=dict(showgrid=True, gridcolor='#eee')
        )
        st.plotly_chart(fig_contrib, use_container_width=True)