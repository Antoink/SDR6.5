import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
import re
import unicodedata
from io import BytesIO
from math import pi
import streamlit.components.v1 as components


SDR_RED = "#D71920"

COL_MAPPING = {
    "Joueur": "Joueur", "Equipe": "Equipe", "Age": "Age", 
    "Poids": "Poids (kg)", "Taille": "Taille (cm)", "Masse Grasse": "Masse grasse",
    "Poste": "Position",
    "Sit And Reach": "Sit and reach", "Knee To Wall (D)": "Knee to wall D",
    "Adducteurs (G)": "Adducteur G", "Adducteurs (D)": "Adducteur D", "Somme ADD": "Somme ADD", "Ratio Squeeze": "Ratio Squeeze (ADD/ABD)",
    "Abducteurs (G)": "Abducteur G", "Abducteurs (D)": "Abducteur D", "Somme ABD": "Somme ABD",
    "Nordic Ischio (G)": "Nordic G", "Nordic Ischio (D)": "Nordic D",
    
    "Inverseur (G)": "Inverseur G", "Inverseur (D)": "Inverseur D",
    "Everseur (G)": "Everseur G", "Everseur (D)": "Everseur D",
    "Endurance Heel Raise (G)": "Endurance Heel Raise G", "Endurance Heel Raise (D)": "Endurance Heel Raise D",
    
    "CMJ 2JB": "CMJ 2JB", "Peak Force CMJ": "Peak Force CMJ", "RFD CMJ": "RFD CMJ", "RSI CMJ": "RSI", "Drop jump": "Drop jump",
    "Wattbike (6s)": "Wattbike 6s (W)", "Squat belt (N)": "Squat belt (N)",
    "VMA": "VMA", "FC": "FC", "SV1": "SV1", "SV2": "SV2",
    "Temps sur 10m": "Temps sur 10m",
    "Amax": "Amax", "Dmax": "Dmax", "Vmax": "Vmax",
    "Nb Accélérations": "Nb Acc", "Nb Décélérations": "Nb Dec",
    "Distance HSR": "Distance HSR", "Distance Totale": "Distance totale", "Distance Sprint (92% Vimax)": "Distance Sprint (92% Vimax)",
    "Q Conc 60° (G)": "Q G conc 60°/s", "Q Conc 60° (D)": "Q Dt conc 60°/s",
    "Q Conc 240° (G)": "Q G conc 240°/s", "Q Conc 240° (D)": "Q Dt conc 240°/s",
    "IJ Conc 60° (G)": "IJ G conc 60°/s", "IJ Conc 60° (D)": "IJ Dt conc 60°/s",
    "IJ Conc 240° (G)": "IJ G conc 240°/s", "IJ Conc 240° (D)": "IJ Dt conc 240°/s",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s", "IJ Exc 30° (D)": "IJ Dt exc 30°/s"
}

OFFICIAL_STRUCTURE = {
    "KINÉ - MOBILITÉ": ["Sit And Reach", "Knee To Wall (D)"],
    "KINÉ - ZONE ADDUCTEURS & ABDUCTEURS": ["Somme ADD", "Ratio Squeeze", "Somme ABD", "Adducteurs (G)", "Adducteurs (D)", "Abducteurs (G)", "Abducteurs (D)"],
    "KINÉ - ZONE ISCHIO-JAMBIERS": ["Nordic Ischio (G)", "Nordic Ischio (D)"],
    "KINÉ - ZONE CHEVILLE": ["Inverseur (G)", "Inverseur (D)", "Everseur (G)", "Everseur (D)"],
    "KINÉ - ZONE PIED": ["Endurance Heel Raise (G)", "Endurance Heel Raise (D)"],
    "BIODEX (VALEURS ABSOLUES)": ["Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)", "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)", "IJ Exc 30° (G)", "IJ Exc 30° (D)"],
    "SALLE - EXPLOSIVITÉ ET PUISSANCE": ["CMJ 2JB", "CMJ 1JB (G)", "CMJ 1JB (D)", "Drop jump"],
    "SALLE - PUISSANCE ET FORCE": ["Wattbike (6s)", "Squat belt (N)"],
    "TERRAIN - PHYSIOLOGIE ET CARDIO": ["VMA", "FC", "SV1", "SV2"],
    "TERRAIN - ACCÉLÉRATION": ["Temps sur 10m"],
    "TERRAIN - GPS": ["Amax", "Dmax", "Vmax", "Nb Accélérations", "Nb Décélérations", "Distance HSR", "Distance Totale", "Distance Sprint (92% Vimax)"]
}

REPORT_NORMES = {
    "VMA": 18, "FC": 180, "SV1": 14, "SV2": 16, "Vmax": 32, "CMJ 2JB": 40, "CMJ 1JB": 20, "Drop jump": 30,
    "Knee To Wall (D)": 9, "Sit And Reach": 20, "Distance HSR": 800,
    "Distance Totale": 8000, "Amax": 5, "Dmax": 5, "Distance Sprint (92% Vimax)": 60,
    "Somme ADD": 34, "Somme ABD": 34, "Ratio Squeeze": [0.90, 1.10],
    "Adducteurs": 4, "Abducteurs": 4,
    "Nordic Ischio": 0.7, "Inverseur": 20, "Everseur": 18, 
    "Endurance Heel Raise": 30,
    "Wattbike (6s)": 1100, "Squat belt (N)": 1500, "Temps sur 10m": 1.90,
    "Nb Accélérations": 50, "Nb Décélérations": 50
}

UNITS = {
    "Knee To Wall (D)": "cm", "Sit And Reach": "cm",
    "Somme ADD": "N", "Somme ABD": "N", "Ratio Squeeze": "",
    "Adducteurs (G)": "N", "Adducteurs (D)": "N", "Abducteurs (G)": "N", "Abducteurs (D)": "N",
    "Nordic Ischio (G)": "N", "Nordic Ischio (D)": "N", 
    "Inverseur (G)": "N", "Inverseur (D)": "N", 
    "Everseur (G)": "N", "Everseur (D)": "N", 
    "Endurance Heel Raise (G)": "reps", "Endurance Heel Raise (D)": "reps", 
    
    "Q Conc 60°": "Nm", "Q Conc 240°": "Nm", "IJ Conc 60°": "Nm", "IJ Conc 240°": "Nm", "IJ Exc 30°": "Nm",
    "CMJ 2JB": "cm", "CMJ 1JB (G)": "cm", "CMJ 1JB (D)": "cm", "Drop jump": "cm",
    "Wattbike (6s)": "W", "Squat belt (N)": "N",
    "VMA": "km/h", "Vmax": "km/h", "Temps sur 10m": "s", "SV1": "km/h", "SV2": "km/h", "FC": "bpm",
    "Distance Totale": "m", "Distance HSR": "m", "Distance Sprint (92% Vimax)": "m", "Amax": "m/s²", "Dmax": "m/s²",
    "Nb Accélérations": "", "Nb Décélérations": ""
}

def clean_numeric_value(val):
    if pd.isna(val) or val == "" or val == "-": return None
    try:
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '.')
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match: return float(match.group())
        return None
    except: return None

def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_column_in_df(df, label):
    col_map_lower = {k.lower(): v for k, v in COL_MAPPING.items()}
    label_lower = label.lower()
    if label_lower in col_map_lower:
        mapped = col_map_lower[label_lower]
        if mapped in df.columns: return mapped
    df_cols_clean = [remove_accents(str(c)).lower().strip() for c in df.columns]
    label_clean = remove_accents(label).lower().strip().replace("(g)", "").replace("(d)", "")
    for idx, col in enumerate(df_cols_clean):
        if label_clean in col: return df.columns[idx]
    return None

def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing %']
    return any(x in str(label).lower() for x in keywords)

def calculate_percentile(df, col_name, value):
    if col_name not in df.columns or pd.isna(value): return 0, 0
    valid_values = pd.to_numeric(df[col_name], errors='coerce').dropna()
    if valid_values.empty: return 0, 0
    mean_val = valid_values.mean()
    inverted = is_inverted(col_name)
    percentile = (valid_values >= value).mean() * 100 if inverted else (valid_values <= value).mean() * 100
    return mean_val, percentile

def get_report_color(label, val):
    import pandas as pd
    if val is None or pd.isna(val) or val == "" or val == "-": return "#eee"
    try: val = float(val)
    except: return "#eee"

    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    
    if "Ratio Squeeze" in col_clean:
        if 0.90 <= val <= 1.10: return "#27AE60"
        return "#D71920"

    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    if not found_key: return "#eee"
        
    norm_val = REPORT_NORMES[found_key]
    
    keywords_inv = ['temps', 'chrono', '10m', '505', 'masse grasse']
    inverted = any(x in str(label).lower() for x in keywords_inv)

    if isinstance(norm_val, (list, tuple)):
        low, high = norm_val
        if inverted:
            if val < low: return "#27AE60"
            elif val <= high: return "#F39C12"
            else: return "#D71920"
        else:
            if val < low: return "#D71920"
            elif val <= high: return "#F39C12"
            else: return "#27AE60"
    else:
        if inverted:
            if val <= norm_val: return "#27AE60"
            else: return "#D71920"
        else:
            if val >= norm_val: return "#27AE60"
            else: return "#D71920"

def get_norm_text(label):
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    if not found_key: return "-"
    
    norm_val = REPORT_NORMES[found_key]
    
    if isinstance(norm_val, (list, tuple)):
        low, high = norm_val
        return f"{low} - {high}"
    else:
        keywords_inv = ['temps', 'chrono', '10m', '505', 'masse grasse']
        inverted = any(x in str(label).lower() for x in keywords_inv)
        if "Ratio" in col_clean:
            return str(norm_val)
        if inverted:
            return f"< {norm_val}"
        else:
            return f"> {norm_val}"

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

def img_to_b64(img_path):
    try:
        if not os.path.exists(img_path): return ""
        with open(img_path, "rb") as f: 
            return base64.b64encode(f.read()).decode()
    except: return ""

def get_best_photo_path(player_name):
    folder = "Photos"
    if not os.path.exists(folder): return None
    clean_player = remove_accents(player_name).lower()
    player_parts = clean_player.split()
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for f in files:
        clean_filename = remove_accents(f).lower()
        match = True
        for part in player_parts:
            if part not in clean_filename:
                match = False
                break
        if match: return os.path.join(folder, f)
    return None

def create_radar_chart(categories, values, text_color="black"):
    if not categories: return ""
    N = len(categories)
    values_closed = values + values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill_between(angles, 0, 33, color='#D71920', alpha=0.15)
    ax.fill_between(angles, 66, 100, color='#27AE60', alpha=0.15)
    plt.xticks(angles[:-1], categories, color=text_color, size=9, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([33, 66, 100], ["33", "66", ""], color="#888", size=8)
    plt.ylim(0, 100)
    ax.plot(angles, values_closed, linewidth=2, linestyle='solid', color="black", marker='o', markersize=5)
    ax.fill(angles, values_closed, color="black", alpha=0.4)
    ax.spines['polar'].set_color('#ccc')
    ax.yaxis.grid(True, color='#ccc', linestyle='dashed')
    ax.xaxis.grid(True, color='#ccc')
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64

def create_biodex_radar(categories, values_g, values_d, norms):
    if not categories: return ""
    N = len(categories)
    
    values_g_closed = values_g + values_g[:1]
    values_d_closed = values_d + values_d[:1]
    norms_closed = norms + norms[:1]
    
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    plt.xticks(angles[:-1], categories, color='black', size=9, weight='bold')
    ax.set_rlabel_position(0)
    grid_color = "#ccc"
    
    max_val = max(max(values_g), max(values_d), max(norms)) * 1.2 if max(values_g) > 0 else 4.0
    plt.yticks([max_val*0.33, max_val*0.66, max_val], ["", "", ""], color="#888", size=8)
    plt.ylim(0, max_val)
    
    ax.yaxis.grid(True, color=grid_color, linestyle='dashed')
    ax.xaxis.grid(True, color=grid_color)
    ax.spines['polar'].set_color(grid_color)
    
    c_g_col = "#1ABC9C"
    c_d_col = "#9B59B6"
    
    ax.plot(angles, values_g_closed, linewidth=2.5, linestyle='solid', color=c_g_col, label='Gauche', marker='o', markersize=4)
    ax.fill(angles, values_g_closed, color=c_g_col, alpha=0.15)
    
    ax.plot(angles, values_d_closed, linewidth=2.5, linestyle='solid', color=c_d_col, label='Droite', marker='o', markersize=4)
    ax.fill(angles, values_d_closed, color=c_d_col, alpha=0.15)
    
    ax.plot(angles, norms_closed, linewidth=1.5, linestyle='dashed', color='#7f8c8d', label='Norme')
    
    # Légende en haut à droite
    plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.15), fontsize=8, frameon=False)
    
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64

def format_pct_display(pct):
    import pandas as pd
    if pct is None or pd.isna(pct): return ""
    try:
        val = int(pct)
        if val >= 66: return f"Top {max(1, 100 - val)}%"
        elif val >= 33: return f"{val}%"  # Affiche uniquement la valeur entre 33 et 66
        else: return f"Flop {max(1, val)}%"
    except:
        return "" 
    
def get_bar_html(val, title, val_g_str, val_d_str):
    limit = 25 
    pct_pos = 50 + max(min((val / limit) * 50, 50), -50)
    c_asym = "#27AE60" if abs(val) < 10 else ("#F39C12" if abs(val) < 15 else "#D71920")
    diff_text = f"{abs(val):.1f}% {'D' if val > 0 else ('G' if val < 0 else '')}" if val != 0 else "Symétrique"
    
    return f"""
    <div style="margin-bottom:15px; background:#fff; padding:12px; border-radius:6px; border:1px solid #eee;">
        <div style="display:flex; justify-content:space-between; font-size:8pt; margin-bottom:8px; font-weight:bold; color:#555; text-align:center;">
            <div style="flex:1; text-align:left; color:#3498DB;">G: {val_g_str}</div> 
            <div style="flex:2; color:#333; font-size:9pt; text-transform:uppercase;">{title}<br><span style="color:{c_asym}; font-size:8pt;">{diff_text}</span></div> 
            <div style="flex:1; text-align:right; color:#D71920;">D: {val_d_str}</div>
        </div>
        <div style="position:relative; width:100%; height:8px; background:linear-gradient(90deg, #3498db 0%, #ebedef 45%, #ebedef 55%, #D71920 100%); border-radius:4px;">
            <div style="position:absolute; left:50%; top:-2px; width:2px; height:12px; background:#ccc;"></div>
            <div style="position:absolute; left:calc({pct_pos}% - 4px); top:-3px; width:8px; height:14px; background:#333; border-radius:3px; border:1px solid white; box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
        </div>
    </div>
    """

def generate_report(player_name, df_row, df, poste, laterality, number, dominant_point, weak_point, strat_point, antecedents, selected_injuries, anthro_data):  
    df_fixed = df.copy()
    poids_col = COL_MAPPING.get("Poids", "Poids (Kg)")
    if poids_col not in df_fixed.columns: 
        poids_col = find_column_in_df(df_fixed, "Poids")
    
    if poids_col and poids_col in df_fixed.columns:
        df_fixed[poids_col] = pd.to_numeric(df_fixed[poids_col], errors='coerce')
        for col in df_fixed.columns:
            if "(N/kg)" in str(col) or "N/kg" in str(col):
                df_fixed[col] = pd.to_numeric(df_fixed[col], errors='coerce')
                mask = (df_fixed[col] > 10) & (df_fixed[poids_col] > 0)
                df_fixed.loc[mask, col] = df_fixed.loc[mask, col] / df_fixed.loc[mask, poids_col]
    
    df = df_fixed
    try:
        df_row = df[df["Joueur"] == player_name].iloc[0]
    except:
        pass

    age_brut = clean_numeric_value(df_row.get(COL_MAPPING.get("Age", "Age")))
    age_str = f"{int(age_brut)}" if age_brut else "-"

    REPORT_NORMES = {
    "VMA": 18, "Vmax": 32, "CMJ": 40,
    "Nordic": 4, "Adducteurs": 4, "Knee To Wall": 9,
    "Sit And Reach": 20, "Distance HSR": 800,
    "Distance Totale": 8000, "Amax": 5, "Dmax": 5, "Distance Sprint (92% Vimax)": 60,
    "Knee To Wall (G)": 9, "Knee To Wall (D)": 9,
    "Adducteurs (G)": 33, "Adducteurs (D)": 33, "Abducteurs (G)": 33, "Abducteurs (D)": 33,
    "Somme ADD": 34, "Somme ABD": 34, "Ratio Squeeze": [0.90, 1.10],
    "Landing %": 10, "Landing (G)": 20, "Landing (D)": 20,
    "Nordic Ischio (G)": 0.7, "Nordic Ischio (D)": 0.7,
    "Q Conc 60° (G)": 2.8, "Q Conc 60° (D)": 2.8,
    "Q Conc 240° (G)": 1.9, "Q Conc 240° (D)": 1.9,
    "IJ Conc 60° (G)": 1.5, "IJ Conc 60° (D)": 1.5,
    "IJ Conc 240° (G)": 1.2, "IJ Conc 240° (D)": 1.2,
    "IJ Exc 30° (G)": 2.0, "IJ Exc 30° (D)": 2.0,
    "Score Sommeil": 8, "Score Nutrition": 8,
    "Développé couché (W)": 400, "Développé couché (W/kg)": 5,
    "Masse Grasse Plis (mm)": 50, "CMJ (cm)": 40, "Wattbike (6s)": 1100,
    "Squat Keiser": 1500, "Tirage Dos Keiser": 800, "Landmine Throw": 600,
    "Temps 10m (Terrain)": 1.90, "5-0-5": 2.40,
    "Nb Accélérations": 50, "Nb Décélérations": 50
}

    REPORT_UNITS = {
        "Knee To Wall": "cm", "Sit And Reach": "cm", "Landing": "N/kg", "Landing %": "%",
        "Adducteurs": "N", "Somme ADD": "N", "Abducteurs": "N", "Somme ABD": "N", "Nordic Ischio": "N",
        "Q Conc 60°": "Nm", "Q Conc 240°": "Nm", "IJ Conc 60°": "Nm", "IJ Conc 240°": "Nm", "IJ Exc 30°": "Nm",
        "CMJ (cm)": "cm", "Landmine Throw": "W", "Wattbike (6s)": "W", "Développé couché (W)": "W", 
        "Développé couché (W/kg)": "W/kg", "Squat Keiser": "W", "Tirage Dos Keiser": "W",
        "VMA": "km/h", "Vmax": "km/h", "Temps 10m (Terrain)": "s", "5-0-5": "s",
        "Distance Totale": "m", "Distance HSR": "m", "Amax": "m/s²", "Dmax": "m/s²",
        "Score Sommeil": "pts", "Score Nutrition": "pts"
    }

    def get_norm_color_value(label, val):
        norm = REPORT_NORMES.get(label) # Pointe vers le dictionnaire global
        if norm is None or val is None: return "#333"
        inv = any(x in label for x in ["Temps", "5-0-5", "Masse", "Plis"])
        if isinstance(norm, list):
            low, high = norm[0], norm[1]
            if inv:
                return "#27AE60" if val <= high else "#D71920"
            else:
                return "#27AE60" if val >= low else "#D71920"
        else:
            if inv:
                return "#27AE60" if val <= norm else "#D71920"
            else:
                return "#27AE60" if val >= norm else "#D71920"
    
    all_scores = []
    for cat, vars in OFFICIAL_STRUCTURE.items():
        if "BIODEX" in cat.upper() or "ISO" in cat.upper(): continue
        for label in vars:
            col_name = COL_MAPPING.get(label, label)
            if col_name not in df.columns: col_name = find_column_in_df(df, label)
            val = clean_numeric_value(df_row.get(col_name))
            if col_name and val is not None:
                mean_val, p = calculate_percentile(df, col_name, val)
                all_scores.append({"label": label, "percentile": p, "val": val, "mean": mean_val})
    all_scores.sort(key=lambda x: x["percentile"], reverse=True)
    top_3, flop_3 = all_scores[:3], all_scores[-3:]

    def get_perf_card(item, is_top=True):
        color_main = "#27AE60" if is_top else "#D71920"
        bg_color = "#f4fbf7" if is_top else "#fef5f5"
        label = item['label'].replace("(G)", "").replace("(D)", "").strip()
        val_str = f"{int(item['val'])}" if item['val'] % 1 == 0 else f"{item['val']:.2f}"
        unit = UNITS.get(label, "")
        pct = item['percentile']
        
        pct_txt = format_pct_display(pct)
        pct_html = f'<div style="font-size:12pt; font-weight:900; color:{color_main};">{pct_txt}</div>' if pct_txt else '<div style="font-size:12pt; font-weight:900; color:#888;">-</div>'
        
        return f"""
        <div style="background:{bg_color}; border-left:4px solid {color_main}; padding:10px; border-radius:6px; margin-bottom:10px; border:1px solid #eee; display:flex; align-items:center;">
            <div style="flex:1.2; border-right:1px solid #ddd; padding-right:10px;">
                <div style="font-weight:bold; color:#333; font-size:8pt; text-transform:uppercase; margin-bottom:2px;">{label}</div>
                <div style="font-size:7pt; color:#666;">Moy: {item['mean']:.1f} {unit}</div>
            </div>
            <div style="flex:1; text-align:center; border-right:1px solid #ddd; padding:0 10px;">
                <div style="font-size:7pt; color:#888; text-transform:uppercase; font-weight:bold; margin-bottom:2px;">Valeur</div>
                <div style="font-weight:900; color:{color_main}; font-size:14pt;">{val_str} <span style="font-size:8pt; color:#888;">{unit}</span></div>
            </div>
            <div style="flex:1; text-align:center; padding-left:10px;">
                <div style="font-size:7pt; color:#888; text-transform:uppercase; font-weight:bold; margin-bottom:2px;">Classement</div>
                {pct_html}
            </div>
        </div>
        """

    radar_config = [
        {"label": "Vmax", "cols": ["Vmax"], "unit": ["km/h"]},
        {"label": "Amax", "cols": ["Amax"], "unit": ["m/s²"]},
        {"label": "Dmax", "cols": ["Dmax"], "unit": ["m/s²"]},
        {"label": "Dist. Totale", "cols": ["Distance Totale"], "unit": ["m"]},
        {"label": "Dist. HSR", "cols": ["Distance HSR"], "unit": ["m"]},
        {"label": "Sprint (>92%)", "cols": ["Distance Sprint (92% Vmax)", "Distance Sprint (92% Vimax)", "Sprint (>25km/h)"], "unit": ["m"]}
    ]

    radar_labels, radar_values = [], []
    
    
    details_html = """
    <div style="background:#fff; border-radius:10px; padding:15px; border:1px solid #eee; box-shadow:0 2px 8px rgba(0,0,0,0.03); height:100%; box-sizing:border-box;">
        <div style="font-weight:900; color:#333; border-bottom:2px solid #eee; padding-bottom:8px; margin-bottom:10px; font-size:9.5pt; text-transform:uppercase;">
            Valeurs Détaillées
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:8.5pt;">
            <tbody>
    """

    for item in radar_config:
        radar_labels.append(item['label'])
        sum_p, count, disp_val, u, p_val, col_found = 0, 0, "-", "", 0, False
        
        for col_key in item['cols']:
            col_name = COL_MAPPING.get(col_key, find_column_in_df(df, col_key))
            val = clean_numeric_value(df_row.get(col_name))
            if val is not None:
                mean_val = 0
                try:
                    mean_val, p = calculate_percentile(df, col_name, val)
                    p_val = p
                    count += 1
                except: pass
                u = item['unit'][0] if 'unit' in item and len(item['unit']) > 0 else ""
                disp_val = f"{val:.2f}" if val <= 100 else f"{int(val)}"
                col_found = True
                
                radar_values.append(p)
                
                c_val = get_report_color(col_key, val)
                if p >= 95:
                    bar_color = "#00E5FF"
                elif p >= 66:
                    bar_color = "#27AE60"
                elif p >= 33:
                    bar_color = "#F39C12"
                else:
                    bar_color = "#D71920"
                
                target_str = ""
                found_key = next((k for k in REPORT_NORMES.keys() if k in item['label']), None)
                if found_key:
                    target = REPORT_NORMES[found_key]
                    target_str = f"Obj. {target}"
                
                p_txt = format_pct_display(p)
                p_html = f'<span style="font-weight:bold; font-size:8pt; color:#666; min-width:24px; text-align:right;">{p_txt}</span>' if p_txt else ''
                
                details_html += f"""
                <tr>
                    <td style="padding:7px 0; border-bottom:1px solid #f5f5f5;">
                        <div style="font-weight:bold; color:#444; font-size:9pt;">{item['label']}</div>
                        <div style="font-size:7pt; color:#999;">{u}</div>
                    </td>
                    <td style="padding:7px 8px; text-align:right; border-bottom:1px solid #f5f5f5;">
                        <div style="font-weight:900; color:{c_val}; font-size:10.5pt;">{disp_val}</div>
                        <div style="font-size:7pt; color:#aaa; font-weight:bold; margin-top:2px;">{target_str}</div>
                    </td>
                    <td style="padding:7px 0; border-bottom:1px solid #f5f5f5; width:45%;">
                        <div style="display:flex; align-items:center; gap:6px;">
                            <div style="flex-grow:1; height:6px; background:#eee; border-radius:3px; overflow:hidden;">
                                <div style="height:100%; width:{int(p)}%; background:{bar_color};"></div>
                            </div>
                            {p_html}
                        </div>
                    </td>
                </tr>
                """
                break
                
        if not col_found:
            radar_values.append(0)

    details_html += "</tbody></table></div>"
    radar_b64 = create_radar_chart(radar_labels, radar_values, text_color="black")

    photo_path = get_best_photo_path(player_name)
    photo_b64 = img_to_b64(photo_path)
    if photo_b64:
        photo_html = f'<img src="data:image/png;base64,{photo_b64}" style="max-width:130px; max-height:130px; width:auto; height:auto; display:block; border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">'
    else:
        photo_html = f'<div style="width:110px; height:130px; background:#e0e0e0; display:flex; align-items:center; justify-content:center; color:#888; font-weight:bold; font-size:24pt; border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">{player_name[:1]}</div>'

    logo_b64 = img_to_b64("logo_sdr.png")
    if logo_b64:
        logo_html_header = f'<img src="data:image/png;base64,{logo_b64}" style="width:75px; margin-bottom:5px;">'
    else:
        logo_html_header = ''

    top_html = "".join([get_perf_card(x, True) for x in top_3])
    flop_html = "".join([get_perf_card(x, False) for x in flop_3])

    page_1 = f"""
    <div class="page">
        
        <div class="header-container" style="display:flex; justify-content:space-between; align-items:center; border-bottom: 3px solid {SDR_RED}; padding-bottom: 15px; margin-bottom: 25px;">
            <div style="display:flex; align-items:center; gap: 25px;">
                {photo_html}
                <div>
                    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:3px;">
                        <h1 style="margin:0; color:{SDR_RED}; font-size:28pt; text-transform:uppercase; line-height:1;">{player_name}</h1>
                        <span style="font-size:22pt; font-weight:900; color:#ccc; line-height:1;">#{number}</span>
                    </div>
                    <div style="font-size:12pt; font-weight:bold; text-transform:uppercase; color:#555; margin-bottom:15px; letter-spacing:1px;">
                        {poste} <span style="color:#ddd; margin:0 5px;">|</span> {laterality}
                    </div>
                    
                    <div style="display:flex; gap:15px; font-size:9.5pt; color:#333; background:#f9f9f9; padding:8px 15px; border-radius:6px; border:1px solid #eee; white-space:nowrap;">
                                <div><span style="color:#888; font-weight:bold; text-transform:uppercase; font-size:7.5pt; display:block;">Âge</span><span style="font-weight:900; font-size:14pt;">{age_str}</span> ans</div>
                                <div><span style="color:#888; font-weight:bold; text-transform:uppercase; font-size:7.5pt; display:block;">Taille</span><span style="font-weight:900; font-size:14pt;">{anthro_data.get('Taille','-')}</span> cm</div>
                                <div><span style="color:#888; font-weight:bold; text-transform:uppercase; font-size:7.5pt; display:block;">Poids</span><span style="font-weight:900; font-size:14pt;">{anthro_data.get('Poids','-')}</span> kg</div>
                                <div><span style="color:#888; font-weight:bold; text-transform:uppercase; font-size:7.5pt; display:block;">Masse Grasse</span><span style="font-weight:900; font-size:14pt;">{anthro_data.get('Masse Grasse','-')}</span> mm</div>
                            </div>
                </div>
            </div>
            
            <div style="text-align:right;">
                {logo_html_header}
                <div style="font-weight:900; color:#333; font-size:9pt; text-transform:uppercase; line-height:1.2;">
                    Département<br><span style="color:{SDR_RED}">Performance</span>
                </div>
            </div>
        </div>

        <div style="margin-bottom:25px;">
            <div style="font-weight:900; font-size:10pt; color:white; background-color:{SDR_RED}; padding:4px 12px; border-radius:4px; display:inline-block; margin-bottom:15px; text-transform:uppercase;">
                PROFIL TERRAIN
            </div>
            <div style="display:flex; align-items:stretch; gap:25px;">
                <div style="width:60%; display:flex; justify-content:center; align-items:center; background:#fff; padding:15px; border-radius:10px; border:1px solid #eee; box-shadow:0 2px 8px rgba(0,0,0,0.03);">
                    <img src="data:image/png;base64,{radar_b64}" style="width:100%; max-width:550px; object-fit:contain;">
                </div>
                <div style="width:40%;">
                    {details_html}
                </div>
            </div>
        </div>

        <div>
            <div style="font-weight:900; font-size:10pt; color:white; background-color:{SDR_RED}; padding:4px 12px; border-radius:4px; display:inline-block; margin-bottom:15px; text-transform:uppercase;">
                PERFORMANCES CLÉS
            </div>
            <div style="display:flex; gap:25px;">
                <div style="flex:1;">
                    <div style="font-weight:bold; color:#27AE60; font-size:10pt; border-bottom:2px solid #27AE60; padding-bottom:4px; margin-bottom:12px; text-transform:uppercase;">Points Forts</div>
                    {top_html}
                </div>
                <div style="flex:1;">
                    <div style="font-weight:bold; color:#D71920; font-size:10pt; border-bottom:2px solid #D71920; padding-bottom:4px; margin-bottom:12px; text-transform:uppercase;">Axes de Progression</div>
                    {flop_html}
                </div>
            </div>
            <div style="font-size: 7.5pt; color: #888; font-style: italic; margin-top: 5px; text-align:center;">
                * <b>Top/Flop</b> : Classement par rapport à l'effectif actuel.
            </div>
        </div>

        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 1/5</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">Stade de Reims - Département PERFORMANCE</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:left; font-size:8pt; color:#ccc;">AK</div>
    </div>
    """

    # PAGE 2
    
    poids_val = clean_numeric_value(df_row.get(COL_MAPPING.get("Poids", "Poids (kg)"))) or 1.0

    sections_config = [
        {
            "title": "PUISSANCE & CARDIO",
            "subsections": [
                {"name": "EXPLOSIVITÉ", "metrics": ["CMJ 2JB", "CMJ 1JB (G)", "CMJ 1JB (D)", "Drop jump"]},
                {"name": "PUISSANCE & FORCE", "metrics": ["Wattbike (6s)", "Squat belt (N)"]},
                {"name": "PHYSIOLOGIE ET CARDIO", "metrics": ["VMA", "FC", "SV1", "SV2"]}
            ]
        },
        {
            "title": "VITESSE & GPS",
            "subsections": [
                {"name": "ACCÉLÉRATION", "metrics": ["Temps sur 10m"]},
                {"name": "GPS", "metrics": ["Amax", "Dmax", "Vmax", "Nb Accélérations", "Nb Décélérations", "Distance HSR", "Distance Totale", "Distance Sprint (92% Vimax)"]}
            ]
        }
    ]

    def build_app_style_column(section):
        # Titre principal légèrement réduit en marges pour gagner de la place
        html = f"<div style='font-weight:900; font-size:11pt; color:{SDR_RED}; border-bottom:2px solid {SDR_RED}; margin-bottom:10px; padding-bottom:4px; text-transform:uppercase;'>{section['title']}</div>"
        
        for sub in section['subsections']:
            html += f"<div style='font-weight:bold; color:#555; font-size:9pt; margin-bottom:6px; margin-top:8px; text-transform:uppercase; background:#f4f4f4; padding:3px 8px; border-radius:4px;'>{sub['name']}</div>"
            
            for label in sub['metrics']:
                col_name = COL_MAPPING.get(label, find_column_in_df(df, label)) or label
                val = clean_numeric_value(df_row.get(col_name))
                if val is not None:
                    try:
                        _, p = calculate_percentile(df, col_name, val)
                    except:
                        p = 0
                    unit = UNITS.get(label, "")
                    
                    if p >= 95: pct_color = "#00E5FF"
                    elif p >= 66: pct_color = "#27AE60"
                    elif p >= 33: pct_color = "#F39C12"
                    else: pct_color = "#D71920"
                    
                    val_color = get_norm_color_value(label, val) 
                    norm_obj = REPORT_NORMES.get(label, "-")
                    norm_text = str(norm_obj)

                    # Paddings et margins ajustés pour faire tenir les 10 cartes de la colonne de gauche sur une seule page
                    html += f"""
                    <div style="background:#fff; border: 1px solid #eee; border-left:4px solid {pct_color}; border-radius:4px; padding:6px 10px; margin-bottom:5px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-weight:bold; font-size:9pt; color:#333;">{label}</div>
                            <div style="font-weight:900; font-size:11pt; color:{val_color};">{int(val) if val%1==0 else f"{val:.2f}"}<span style="font-size:7.5pt; color:#888; font-weight:normal;"> {unit}</span></div>
                        </div>
                        <div style="margin-top:4px; display:flex; justify-content:space-between; font-size:8pt; border-top:1px solid #f9f9f9; padding-top:4px;">
                            <div style="color:#444;">Niveau : <span style="font-weight:bold; color:{pct_color};">Top {int(p)}%</span></div>
                            <div style="color:#777;">Objectif : <span style="font-weight:bold; color:#444;">{norm_text} {unit}</span></div>
                        </div>
                    </div>
                    """
        return html

    left_content = build_app_style_column(sections_config[0])
    right_content = build_app_style_column(sections_config[1])


    legend_html = f"""
    <div style="margin-top:auto; margin-bottom:25px; padding:15px; background:#f8f9fa; border:1px solid #e9ecef; border-radius:8px; font-size:8pt; color:#495057; box-shadow: 0 2px 4px rgba(0,0,0,0.02); width:100%; box-sizing:border-box;">
        <div style="font-weight:900; color:{SDR_RED}; margin-bottom:10px; text-transform:uppercase; font-size:10pt; border-bottom:2px solid #dee2e6; padding-bottom:4px;">
            Guide de lecture
        </div>
        
        <div style="display:flex; justify-content:space-around; align-items:flex-start;">
            <div style="flex:1;">
                <div style="font-weight:bold; color:#333; margin-bottom:8px; font-size:8pt; letter-spacing:0.5px;">🎯 PAR RAPPORT À L'OBJECTIF</div>
                <div style="display:flex; gap:15px; align-items:center;">
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#27AE60;"><div style="width:10px; height:10px; border-radius:50%; background:#27AE60;"></div> Objectif Atteint</span>
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#D71920;"><div style="width:10px; height:10px; border-radius:50%; background:#D71920;"></div> Sous l'objectif</span>
                </div>
            </div>
            
            <div style="flex:2; border-left:1px dashed #ccc; padding-left:20px;">
                <div style="font-weight:bold; color:#333; margin-bottom:8px; font-size:8pt; letter-spacing:0.5px;">📊 PAR RAPPORT AU GROUPE (Classement)</div>
                <div style="display:flex; flex-wrap:wrap; gap:15px; align-items:center;">
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#00B8D4;"><div style="width:12px; height:4px; border-radius:2px; background:#00E5FF;"></div> Élite (Top 5%)</span>
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#27AE60;"><div style="width:12px; height:4px; border-radius:2px; background:#27AE60;"></div> Bon (Top 34%)</span>
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#F39C12;"><div style="width:12px; height:4px; border-radius:2px; background:#F39C12;"></div> Moyen (33-66%)</span>
                    <span style="display:flex; align-items:center; gap:5px; font-weight:bold; color:#D71920;"><div style="width:12px; height:4px; border-radius:2px; background:#D71920;"></div> Flop (&lt; 33%)</span>
                </div>
            </div>
        </div>
    </div>
    """

    page_2 = f"""
    <div class="page" style="position:relative; display:flex; flex-direction:column; box-sizing: border-box; padding-bottom: 70px;">
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:15px; padding-bottom:8px;">
            <span style="font-weight:900; font-size:15pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:10pt; color:#666; margin-left:12px; text-transform:uppercase; letter-spacing:1px;">Profilage Athlétique & Physiologique</span>
        </div>
        
        <div style="display: flex; gap: 25px; flex: 1; align-items: stretch; margin-bottom:15px;">
            <div style="flex: 1; width: 50%; display: flex; flex-direction: column;">
                {left_content}
            </div>
            <div style="flex: 1; width: 50%; display: flex; flex-direction: column;">
                {right_content}
            </div>
        </div>
        
        {legend_html}
        
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 2/5</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">Stade de Reims - Département PERFORMANCE</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:left; font-size:8pt; color:#ccc;">AK</div>
    </div>
    """
   #PAGE 3 : ANTÉCÉDENTS 
    
    def get_medical_body_b64(injury_counts):
        import base64
        import os
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
        if isinstance(injury_counts, dict):
            for inj, count in injury_counts.items():
                if inj in coords:
                    x, y = coords[inj]
                    markers += f'<circle cx="{x}" cy="{y}" r="16" fill="rgba(52, 152, 219, 0.4)" stroke="#3498DB" stroke-width="2"/>'
                    if count > 1:
                        markers += f'<circle cx="{x+10}" cy="{y-10}" r="8" fill="#D71920"/><text x="{x+10}" y="{y-6}" font-size="10" font-family="Arial" font-weight="bold" fill="white" text-anchor="middle">{count}</text>'
                    else:
                        markers += f'<circle cx="{x}" cy="{y}" r="4" fill="#3498DB"/>'

        svg_code = f"""<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{bg_html}{markers}</svg>"""
        svg_b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
        return f'<img src="data:image/svg+xml;base64,{svg_b64}" style="max-width:100%; max-height:100%; object-fit:contain;">'

    body_html = get_medical_body_b64(selected_injuries)

    # BIODEX 
    biodex_conf = [
        {"label": "Q 60", "g": "Q G conc 60°/s (N/kg)", "d": "Q Dt conc 60°/s (N/kg)", "n": 3.1},
        {"label": "Q 240", "g": "Q G conc 240°/s (N/kg)", "d": "Q Dt conc 240°/s (N/kg)", "n": 2.2},
        {"label": "IJ 60", "g": "IJ G conc 60°/s (N/kg)", "d": "IJ Dt conc 60°/s (N/kg)", "n": 1.8},
        {"label": "IJ 240", "g": "IJ G conc 240°/s (N/kg)", "d": "IJ Dt conc 240°/s (N/kg)", "n": 1.5},
        {"label": "IJ Exc", "g": "IJ G Exc 30°/s (N/kg)", "d": "IJ Dt exc 30°/s (N/kg)", "n": 2.4}
    ]
    b_l, b_g, b_d, b_n = [], [], [], []
    for b in biodex_conf:
        b_l.append(b["label"]); b_n.append(b["n"])
        col_g = find_column_in_df(df, b["g"]) or b["g"]
        col_d = find_column_in_df(df, b["d"]) or b["d"]
        b_g.append(clean_numeric_value(df_row.get(col_g)) or 0)
        b_d.append(clean_numeric_value(df_row.get(col_d)) or 0)
    biodex_b64 = create_biodex_radar(b_l, b_g, b_d, b_n)

    def format_asym(val_g, val_d, is_ktw=False):
        if val_g is None or val_d is None: return "-", "#888"
        ref = max(val_g, val_d)
        if is_ktw and ref == 0: ref = 15
        if ref == 0: return "0%", "#27AE60"
        diff_abs = (abs(val_d - val_g) / ref) * 100
        if diff_abs < 0.5: asym_str = "0%"
        elif val_d > val_g: asym_str = f"{diff_abs:.0f}% D"
        else: asym_str = f"{diff_abs:.0f}% G"
        if diff_abs >= 15: c_asym = "#D71920"
        elif diff_abs >= 10: c_asym = "#F39C12"
        else: c_asym = "#27AE60"
        return asym_str, c_asym

    biodex_raw_conf = [
        {"label": "Q 60°", "g": "Q G conc 60°/s", "d": "Q Dt conc 60°/s", "n": 3.1},
        {"label": "Q 240°", "g": "Q G conc 240°/s", "d": "Q Dt conc 240°/s", "n": 2.2},
        {"label": "IJ 60°", "g": "IJ G conc 60°/s", "d": "IJ Dt conc 60°/s", "n": 1.8},
        {"label": "IJ 240°", "g": "IJ G conc 240°/s", "d": "IJ Dt conc 240°/s", "n": 1.5},
        {"label": "IJ Exc 30°", "g": "IJ G Exc 30°/s", "d": "IJ Dt exc 30°/s", "n": 2.4}
    ]
    
    poids_joueur = clean_numeric_value(df_row.get(COL_MAPPING.get("Poids", find_column_in_df(df, "Poids")))) or 1.0
    
    biodex_table_rows = ""
    for b in biodex_raw_conf:
        c_g = find_column_in_df(df, b["g"]) or b["g"]
        c_d = find_column_in_df(df, b["d"]) or b["d"]
        v_g = clean_numeric_value(df_row.get(c_g))
        v_d = clean_numeric_value(df_row.get(c_d))
        val_g_str = f"{v_g:.0f}" if v_g is not None else "-"
        val_d_str = f"{v_d:.0f}" if v_d is not None else "-"
        asym_str, c_asym = format_asym(v_g, v_d)
        target_abs_str = f"{b['n'] * poids_joueur:.0f}" if poids_joueur > 1.0 else "-"
        
        biodex_table_rows += f"<tr><td style='padding:2px 4px; border-bottom:1px solid #eee;'>{b['label']}</td><td style='text-align:center; color:#888; font-weight:bold; padding:2px 4px; border-bottom:1px solid #eee;'>{target_abs_str}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_g_str}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_d_str}</td><td style='text-align:center; font-weight:bold; color:{c_asym}; padding:2px 4px; border-bottom:1px solid #eee;'>{asym_str}</td></tr>"

    c_rm_g = find_column_in_df(df, "Ratio Mixte G") or "Ratio Mixte G"
    c_rm_d = find_column_in_df(df, "Ratio Mixte D") or "Ratio Mixte D"
    v_rm_g = clean_numeric_value(df_row.get(c_rm_g))
    v_rm_d = clean_numeric_value(df_row.get(c_rm_d))
    val_rm_g_str = f"{v_rm_g:.2f}" if v_rm_g is not None else "-"
    val_rm_d_str = f"{v_rm_d:.2f}" if v_rm_d is not None else "-"
    biodex_table_rows += f"<tr style='background-color:#fdfdfd;'><td style='padding:2px 4px; border-bottom:1px solid #eee; font-weight:bold;'>R. Mixte</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>-</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_rm_g_str}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_rm_d_str}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>-</td></tr>"
    biodex_rel_conf = [
        {"label": "Q 60°", "g": "Q G conc 60°/s (N/kg)", "d": "Q Dt conc 60°/s (N/kg)"},
        {"label": "Q 240°", "g": "Q G conc 240°/s (N/kg)", "d": "Q Dt conc 240°/s (N/kg)"},
        {"label": "IJ 60°", "g": "IJ G conc 60°/s (N/kg)", "d": "IJ Dt conc 60°/s (N/kg)"},
        {"label": "IJ 240°", "g": "IJ G conc 240°/s (N/kg)", "d": "IJ Dt conc 240°/s (N/kg)"},
        {"label": "IJ Exc 30°", "g": "IJ G Exc 30°/s (N/kg)", "d": "IJ Dt exc 30°/s (N/kg)"}
    ]
    biodex_rel_table_rows = ""
    for b in biodex_rel_conf:
        c_g = find_column_in_df(df, b["g"]) or b["g"]
        c_d = find_column_in_df(df, b["d"]) or b["d"]
        v_g = clean_numeric_value(df_row.get(c_g))
        v_d = clean_numeric_value(df_row.get(c_d))
        val_g_str = f"{v_g:.2f}" if v_g is not None else "-"
        val_d_str = f"{v_d:.2f}" if v_d is not None else "-"
        asym_str, c_asym = format_asym(v_g, v_d)
        biodex_rel_table_rows += f"<tr><td style='padding:2px 4px; border-bottom:1px solid #eee;'>{b['label']}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_g_str}</td><td style='text-align:center; padding:2px 4px; border-bottom:1px solid #eee;'>{val_d_str}</td><td style='text-align:center; font-weight:bold; color:{c_asym}; padding:2px 4px; border-bottom:1px solid #eee;'>{asym_str}</td></tr>"

    formatted_lines = []
    if antecedents:
        for line in str(antecedents).split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('📅'):
                match = re.search(r'\((\d+)j\)', line)
                if match:
                    d = int(match.group(1))
                    if d <= 14: c_dur = "#27AE60"
                    elif d <= 30: c_dur = "#F39C12"
                    else: c_dur = "#D71920"
                    line = line.replace(match.group(0), f"<span style='color:{c_dur}; font-weight:900;'>{match.group(0)}</span>")
                formatted_lines.append(f'<div style="font-weight:bold; color:#D71920; margin-top:8px; font-size:8pt;">{line}</div>')
            elif line.startswith('↳'):
                formatted_lines.append(f'<div style="font-size:7.5pt; color:#555; padding-left:12px; margin-bottom:4px; font-style:italic;">{line}</div>')
            else:
                formatted_lines.append(f'<div style="font-size:8pt; color:#444; margin-bottom:4px;">{line}</div>')
        formatted_antecedents = "".join(formatted_lines)
    else:
        formatted_antecedents = "<div style='font-size:8pt; color:#888; font-style:italic;'>Aucun antécédent majeur signalé à ce jour.</div>"
        
               
    page_3 = f"""
    <div class="page" style="position:relative; display:flex; flex-direction:column; box-sizing: border-box; padding-bottom: 50px;">
        
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:20px; padding-bottom:10px;">
            <span style="font-weight:900; font-size:16pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:11pt; color:#666; margin-left:15px; text-transform:uppercase; letter-spacing:1px;">HISTORIQUE MÉDICAL ET ANTÉCÉDENTS</span>
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 20px; flex: 1; margin-bottom: 20px;">
            
            <div style="flex: 35; background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 15px; display: flex; flex-direction: column; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                <div style="font-weight:900; color:{SDR_RED}; font-size:12pt; margin-bottom:10px; text-transform:uppercase; text-align:center; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px;">
                    CARTOGRAPHIE DES BLESSURES
                </div>
                <div style="flex: 1; display: flex; justify-content: center; align-items: center; overflow: hidden; background: #fafafa; border-radius: 8px; border: 1px dashed #e0e0e0; padding: 5px;">
                    {body_html}
                </div>
            </div>
            
            <div style="flex: 65; background: #fdfdfd; border: 1px solid #eee; border-radius: 10px; padding: 15px; display: flex; flex-direction: column; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                <div style="font-size: 8.5pt; color: #444; line-height: 1.5; overflow-y: auto; flex: 1; column-count: 2; column-gap: 30px; padding: 0 10px;">
                    {formatted_antecedents}
                </div>
            </div>
            
        </div>
        
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 3/5</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">Stade de Reims - Département PERFORMANCE</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:left; font-size:8pt; color:#ccc;">AK</div>
    </div>
    """
    
# PAGE 4 
    
    sar_col = COL_MAPPING.get("Sit And Reach", find_column_in_df(df, "Sit And Reach"))
    sar_val = clean_numeric_value(df_row.get(sar_col)) if sar_col else None
    sar_html = ""
    
    if sar_val is not None:
        _, sar_pct = calculate_percentile(df, sar_col, sar_val)
        sar_c = get_report_color("Sit And Reach", sar_val)
        if sar_pct >= 95:
            sar_bar_c = "#00E5FF"
        elif sar_pct >= 66:
            sar_bar_c = "#27AE60"
        elif sar_pct >= 33:
            sar_bar_c = "#F39C12"
        else:
            sar_bar_c = "#D71920"

        sar_html = f"""
        <div style="margin-bottom:15px; padding:10px; background:#fff; border-radius:8px; border:1px solid #eee;">
            <div style="font-weight:bold; color:{SDR_RED}; font-size:9pt; text-transform:uppercase; margin-bottom:5px;">TEST UNILATÉRAL</div>
            <table style="width:100%; border-collapse:collapse; font-size:9pt;">
                <tr>
                    <td width="30%" style="font-weight:bold; color:#555;">Sit And Reach</td>
                    <td width="20%" class="val-cell" style="color:{sar_c}; font-size:10pt;">{sar_val} <span style="font-size:7pt;color:#999;">cm</span></td>
                    <td width="50%">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="flex-grow:1; height:8px; background:#eee; border-radius:4px;">
                                <div style="height:100%; width: {int(sar_pct)}%; background-color: {sar_bar_c}; border-radius:4px;"></div>
                            </div>
                            <div style="font-size:8pt; color:#666; font-weight:bold;">{format_pct_display(sar_pct)}</div>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
        """
    
    def get_asym_bar_html(val_pct, title, val_g_str, val_d_str):
        limit = 20
        pct_pos = 50 + max(min((val_pct / limit) * 50, 50), -50)
        
        return f'''
        <div style="margin-bottom:12px; background:#f9f9f9; padding:10px 12px; border-radius:6px; border:1px solid #eee; break-inside: avoid;">
            <div style="display:flex; justify-content:space-between; font-size:8pt; margin-bottom:10px; font-weight:bold; color:#555; text-align:center; align-items:center;">
                <div style="flex:1; text-align:left; color:#666; font-size:9pt;">G: {val_g_str}</div> 
                <div style="flex:2; color:#333; font-size:8.5pt; text-transform:uppercase;">{title}</div> 
                <div style="flex:1; text-align:right; color:#666; font-size:9pt;">D: {val_d_str}</div>
            </div>
            <div style="position:relative; width:100%; height:8px; background:#e0e0e0; border-radius:4px;">
                <div style="position:absolute; left:50%; top:-2px; width:2px; height:12px; background:#aaa;"></div>
                <div style="position:absolute; left:calc({pct_pos}% - 4px); top:-3px; width:8px; height:14px; background:#D71920; border-radius:3px; border:1px solid white; box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
        </div>
        '''

    def get_ktw_bar_html(diff_cm, title, val_g_str, val_d_str):
        limit = 6
        pct_pos = 50 + max(min((diff_cm / limit) * 50, 50), -50)
        
        return f'''
        <div style="margin-bottom:12px; background:#f9f9f9; padding:10px 12px; border-radius:6px; border:1px solid #eee; break-inside: avoid;">
            <div style="display:flex; justify-content:space-between; font-size:8pt; margin-bottom:10px; font-weight:bold; color:#555; text-align:center; align-items:center;">
                <div style="flex:1; text-align:left; color:#666; font-size:9pt;">G: {val_g_str}</div> 
                <div style="flex:2; color:#333; font-size:8.5pt; text-transform:uppercase;">{title}</div> 
                <div style="flex:1; text-align:right; color:#666; font-size:9pt;">D: {val_d_str}</div>
            </div>
            <div style="position:relative; width:100%; height:8px; background:#e0e0e0; border-radius:4px;">
                <div style="position:absolute; left:50%; top:-2px; width:2px; height:12px; background:#aaa;"></div>
                <div style="position:absolute; left:calc({pct_pos}% - 4px); top:-3px; width:8px; height:14px; background:#D71920; border-radius:3px; border:1px solid white; box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
        </div>
        '''
    
    bilateral_tests = [
        ("MOBILITÉ CHEVILLE (KTW)", "Knee To Wall (G)", "Knee To Wall (D)", "cm"),
        ("FORCE ISOMÉTRIQUE - ADDUCTEURS", "Adducteurs (G)", "Adducteurs (D)", "N/kg"),
        ("FORCE ISOMÉTRIQUE - ABDUCTEURS", "Abducteurs (G)", "Abducteurs (D)", "N/kg"),
        ("FORCE EXCENTRIQUE - ISCHIOS", "Nordic Ischio (G)", "Nordic Ischio (D)", "N/kg"),
        ("MÉCANIQUE DE SAUT - RÉCEPTION", "Landing (G)", "Landing (D)", "N/kg")
    ]

    bilateral_rows = ""
    bar_graphs_html = ""

    for title, l_g, l_d, unit in bilateral_tests:
        c_g = COL_MAPPING.get(l_g, find_column_in_df(df, l_g))
        c_d = COL_MAPPING.get(l_d, find_column_in_df(df, l_d))
        
        v_g = clean_numeric_value(df_row.get(c_g)) if c_g else None
        v_d = clean_numeric_value(df_row.get(c_d)) if c_d else None
        
        if v_g is not None and v_d is not None:
            # Stats Gauche
            _, pct_g = calculate_percentile(df, c_g, v_g)
            c_val_g = get_report_color(l_g, v_g)
            if pct_g >= 95:
                c_bar_g = "#00E5FF"
            elif pct_g >= 66:
                c_bar_g = "#27AE60"
            elif pct_g >= 33:
                c_bar_g = "#F39C12"
            else:
                c_bar_g = "#D71920"
            val_g_str = f"{int(v_g)}" if v_g % 1 == 0 else f"{v_g:.2f}"
            
            _, pct_d = calculate_percentile(df, c_d, v_d)
            c_val_d = get_report_color(l_d, v_d)
            if pct_d >= 95:
                c_bar_d = "#00E5FF"
            elif pct_d >= 66:
                c_bar_d = "#27AE60"
            elif pct_d >= 33:
                c_bar_d = "#F39C12"
            else:
                c_bar_d = "#D71920"
            val_d_str = f"{int(v_d)}" if v_d % 1 == 0 else f"{v_d:.2f}"
            
            # Asymétrie et Graphique
            name_graph = title.split(" - ")[1] if " - " in title else title
            if "Cheville" in title or "KTW" in title:
                diff = v_d - v_g
                c_asym = "#27AE60" if abs(diff) < 2 else ("#F39C12" if abs(diff) < 3 else "#D71920")
                diff_text = f"{abs(diff):.1f} cm<br><span style='font-size:10pt;'>{'D' if diff > 0 else ('G' if diff < 0 else '')}</span>" if diff != 0 else "Symétrique"
                bar_graphs_html += get_ktw_bar_html(diff, name_graph, f"{val_g_str} {unit}", f"{val_d_str} {unit}")
            else:
                ref = max(v_g, v_d)
                val_pct = ((v_d - v_g) / ref) * 100 if ref > 0 else 0
                c_asym = "#27AE60" if abs(val_pct) < 10 else ("#F39C12" if abs(val_pct) < 15 else "#D71920")
                diff_text = f"{abs(val_pct):.1f}%<br><span style='font-size:10pt;'>{'D' if val_pct > 0 else ('G' if val_pct < 0 else '')}</span>" if val_pct != 0 else "Symétrique"
                bar_graphs_html += get_asym_bar_html(val_pct, name_graph, f"{val_g_str} {unit}", f"{val_d_str} {unit}")

            bilateral_rows += f"""
            <tr><td colspan="3" style="text-align:center; font-weight:bold; font-size:8pt; color:#888; background:#f0f0f0; padding:4px; border-bottom:1px solid #ddd; border-top:2px solid #ddd; text-transform:uppercase;">{title}</td></tr>
            <tr>
                <td style="padding:10px; border-right:1px dashed #ddd; width:40%; background:#fdfdfd;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px; align-items:flex-end;">
                        <span style="font-weight:900; font-size:11pt; color:{c_val_g};">{val_g_str} <span style="font-size:7pt;color:#999;font-weight:normal;">{unit}</span></span>
                        <span style="font-size:8pt; color:#666; font-weight:bold;">{format_pct_display(pct_g)}</span>
                    </div>
                    <div style="height:6px; background:#eee; border-radius:3px; width:100%;">
                        <div style="height:100%; border-radius:3px; width: {int(pct_g)}%; background-color: {c_bar_g};"></div>
                    </div>
                </td>
                
                <td style="text-align:center; vertical-align:middle; font-weight:bold; color:{c_asym}; font-size:9pt; padding:8px; background:#fff; width:20%;">
                    {diff_text}
                </td>
                
                <td style="padding:10px; border-left:1px dashed #ddd; width:40%; background:#fdfdfd;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px; align-items:flex-end;">
                        <span style="font-weight:900; font-size:11pt; color:{c_val_d};">{val_d_str} <span style="font-size:7pt;color:#999;font-weight:normal;">{unit}</span></span>
                        <span style="font-size:8pt; color:#666; font-weight:bold;">{format_pct_display(pct_d)}</span>
                    </div>
                    <div style="height:6px; background:#eee; border-radius:3px; width:100%;">
                        <div style="height:100%; border-radius:3px; width: {int(pct_d)}%; background-color: {c_bar_d};"></div>
                    </div>
                </td>
            </tr>
            """

    legend_asym_html = f"""
    <div style="background-color: #f9f9f9; padding: 10px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #eee; font-size: 8pt; break-inside: avoid;">
        <div style="font-weight:bold; margin-bottom:4px; color:#333; text-transform:uppercase;">Légende des Asymétries</div>
        <div style="display:flex; gap: 20px;">
            <div style="flex:1;">
                <div style="font-weight:bold; color:#666; font-size:8pt; margin-bottom:4px;">Code couleur Force</div>
                <div style="display:flex; gap:10px; font-size:7pt; font-weight:bold;">
                    <span style="color:#27AE60;">Vert (&lt;10%)</span>
                    <span style="color:#F39C12;">Orange (10-15%)</span>
                    <span style="color:#D71920;">Rouge (&gt;15%)</span>
                </div>
            </div>
            <div style="flex:1;">
                <div style="font-weight:bold; color:#666; font-size:8pt; margin-bottom:4px;">Code couleur Mobilité (KTW)</div>
                <div style="display:flex; gap:10px; font-size:7pt; font-weight:bold;">
                    <span style="color:#27AE60;">Vert (&lt;2cm)</span>
                    <span style="color:#F39C12;">Orange (2-3cm)</span>
                    <span style="color:#D71920;">Rouge (&gt;3cm)</span>
                </div>
            </div>
        </div>
    </div>
    """

    #PAGE 4 : 
    page_4 = f"""
    <div class="page" style="position:relative; display:flex; flex-direction:column; box-sizing: border-box; padding-bottom: 40px;">
        
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:20px; padding-bottom:10px;">
            <span style="font-weight:900; font-size:16pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:11pt; color:#666; margin-left:15px; text-transform:uppercase; letter-spacing:1px;">BIODEX & SYMÉTRIES FONCTIONNELLES</span>
        </div>
        
        <div style="display: flex; gap: 20px; background:#fff; padding:20px; border-radius:10px; border:1px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.03); box-sizing: border-box; margin-bottom: 30px;">
            
            <div style="width: 60%; display:flex; flex-direction:column; align-items:center; border-right: 1px solid #eee; padding-right: 20px;">
                <div style="font-weight:900; color:{SDR_RED}; font-size:12pt; margin-bottom:10px; text-transform:uppercase;">RADAR BIODEX (N/kg)</div>
                <div style="flex: 1; display: flex; justify-content: center; align-items: center; width: 100%;">
                    <img src="data:image/png;base64,{biodex_b64}" style="width:100%; max-height:420px; object-fit:contain;">
                </div>
            </div>
            
            <div style="width: 40%; padding-left: 5px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-weight:900; color:{SDR_RED}; border-bottom:1px solid #ddd; margin-bottom:8px; padding-bottom:4px; font-size:10pt; text-transform:uppercase;">
                    VALEURS BRUTES (Nm)
                </div>
                <table style="width:100%; border-collapse:collapse; font-size:9pt; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color:#f9f9f9; color:#333;">
                            <th style="padding:4px; text-align:left; border-bottom:1px solid #ddd;">Test</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">Obj.</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">G</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">D</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">LSI</th>
                        </tr>
                    </thead>
                    <tbody>{biodex_table_rows}</tbody>
                </table>

                <div style="font-weight:900; color:{SDR_RED}; border-bottom:1px solid #ddd; margin-bottom:8px; padding-bottom:4px; font-size:10pt; text-transform:uppercase;">
                    VALEURS RELATIVES (N/kg)
                </div>
                <table style="width:100%; border-collapse:collapse; font-size:9pt; margin-bottom: 10px;">
                    <thead>
                        <tr style="background-color:#f9f9f9; color:#333;">
                            <th style="padding:4px; text-align:left; border-bottom:1px solid #ddd;">Test</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">G</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">D</th>
                            <th style="padding:4px; text-align:center; border-bottom:1px solid #ddd;">LSI</th>
                        </tr>
                    </thead>
                    <tbody>{biodex_rel_table_rows}</tbody>
                </table>
                
                <div style="margin-top: auto; font-size:7.5pt; color:#666; font-style:italic; line-height:1.4; background: #fdfdfd; padding: 10px; border-radius: 8px; border: 1px solid #eee;">
                    * <b>Obj.</b> : L'objectif absolu (Nm) est calculé en multipliant la norme relative (N/kg) par le poids du joueur.<br>
                    * <b>LSI</b> : Écart mesuré entre les deux membres.<br>
                    * <span style="color:#27AE60; font-weight:bold;">Vert</span>: &lt;10% | <span style="color:#F39C12; font-weight:bold;">Orange</span>: 10-15% | <span style="color:#D71920; font-weight:bold;">Rouge</span>: &gt;15%
                </div>
            </div>
        </div>
        
        <div style="font-weight:900; color:{SDR_RED}; border-bottom:2px solid {SDR_RED}; margin-bottom:15px; padding-bottom:8px; font-size:12pt; text-transform:uppercase;">
            SYMÉTRIES FONCTIONNELLES
        </div>
        
        <div style="column-count: 2; column-gap: 30px; margin-top: 10px;">
            {bar_graphs_html}
        </div>
        
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 4/5</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">Stade de Reims - Département PERFORMANCE</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:left; font-size:8pt; color:#ccc;">AK</div>
    </div>
    """
    #PAGE 5 
    logo_b64 = img_to_b64("logo_sdr.png")
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:80px; margin-bottom:10px;">'
    else:
        logo_html = ''

    page_5 = f"""
    <div class="page">
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:30px; padding-bottom:5px;">
            <span style="font-weight:900; font-size:14pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:9pt; color:#666; margin-left:10px;">SYNTHÈSE</span>
        </div>
        
        <div style="margin-top:20px;">
            <div style="padding: 12px 15px; margin-bottom: 15px; border-radius: 6px; border-left: 6px solid #27AE60; background: #eefaf3; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <h3 style="color: #27AE60; margin: 0 0 6px 0; font-size: 10pt;">POINT(S) FORT(S)</h3>
                <p style="margin: 0; font-size: 9pt; color: #333;">{dominant_point if dominant_point else " "}</p>
            </div>
            
            <div style="padding: 12px 15px; margin-bottom: 15px; border-radius: 6px; border-left: 6px solid #D71920; background: #fef5f5; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <h3 style="color: #D71920; margin: 0 0 6px 0; font-size: 10pt;">AXES D'AMÉLIORATION</h3>
                <p style="margin: 0; font-size: 9pt; color: #333;">{weak_point if weak_point else " "}</p>
            </div>
            
            <div style="padding: 12px 15px; margin-bottom: 15px; border-radius: 6px; border-left: 6px solid #3498DB; background: #f0f7fd; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <h3 style="color: #3498DB; margin: 0 0 6px 0; font-size: 10pt;">STRATÉGIE</h3>
                <p style="margin: 0; font-size: 9pt; color: #333;">{strat_point if strat_point else " "}</p>
            </div>
            
            <div style="padding: 12px 15px; margin-bottom: 15px; border-radius: 6px; border-left: 6px solid #8E44AD; background: #f4f0f8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <h3 style="color: #8E44AD; margin: 0 0 6px 0; font-size: 10pt;">ANTÉCÉDENTS BLESSURE</h3>
                <p style="margin: 0; font-size: 9pt; color: #333;">{antecedents if antecedents else " "}</p>
            </div>
        </div>

        <div style="margin-top:25px;">
            <div style="font-weight:bold; color:#333; font-size:10pt; margin-bottom:8px; text-transform:uppercase;">NOTES ADDITIONNELLES</div>
            <div style="width:100%; height:220px; border:1px solid #ccc; border-radius:8px; background:#fff;"></div>
        </div>
        
        <div style="position: absolute; bottom: 15mm; right: 15mm; display: flex; flex-direction: column; align-items: flex-end; text-align: right;">
            {logo_html}
            <div style="font-weight:900; color:#333; font-size:10pt; text-transform:uppercase; line-height:1.2;">
                Département<br><span style="color:{SDR_RED}">Performance</span>
            </div>
        </div>
        
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 5/5</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">Stade de Reims - Département PERFORMANCE</div>
        <div style="position:absolute; bottom:6mm; width:100%; text-align:left; font-size:8pt; color:#ccc;">AK</div>
    </div>
    """

    css = f"""
    <style>
        /* STYLES ÉCRAN (Aperçu navigateur) */
        body {{ 
            font-family: 'Helvetica', 'Arial', sans-serif; 
            margin: 0; 
            padding: 0; 
            background-color: #eee; 
            font-size: 9pt; 
        }}
        .page {{ 
            background: white; 
            width: 210mm; 
            height: 297mm; /* Hauteur A4 exacte */
            margin: 10px auto; 
            padding: 12mm 15mm; 
            box-shadow: 0 0 10px rgba(0,0,0,0.1); 
            box-sizing: border-box; 
            position: relative; 
            page-break-after: always; 
            overflow: hidden; 
        }}
        .page:last-child {{ page-break-after: avoid; }}

        /* TYPOGRAPHIE & ÉLÉMENTS */
        .header-container {{ display: flex; padding: 5px 0; margin-bottom: 20px; align-items:center; border-bottom: 2px solid #eee; padding-bottom:10px; }}
        .section-title {{ font-size: 10pt; font-weight: 900; color: white; background-color: {SDR_RED}; padding: 4px 12px; margin-top: 10px; margin-bottom: 5px; border-radius: 4px; display: block; text-align: center; text-transform: uppercase; }}
        
        /* PIED DE PAGE "CARRÉ" */
        .footer-report {{
            position: absolute;
            bottom: 10mm;
            left: 15mm;
            right: 15mm;
            border-top: 1px solid #eee;
            padding-top: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 8pt;
            color: #ccc;
        }}

        /* STYLES D'IMPRESSION */
        @media print {{
            @page {{ 
                size: A4; 
                margin: 0; 
            }}
            body {{ 
                background-color: white; 
                margin: 0; 
                padding: 0;
                -webkit-print-color-adjust: exact !important; 
                print-color-adjust: exact !important;
            }}
            .page {{ 
                margin: 0; 
                box-shadow: none; 
                width: 210mm; 
                height: 297mm; 
                page-break-after: always; 
                page-break-inside: avoid;
            }}
            .page:last-child {{ page-break-after: auto; }}
        }}
    </style>
    """
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{page_1}{page_2}{page_3}{page_4}{page_5}</body></html>"


def main():
    st.set_page_config(page_title="Générateur de Rapport", layout="wide")
    st.title("Générateur de Profils Joueurs")

    if not os.path.exists("Photos"):
        st.sidebar.warning("⚠️ Dossier 'Photos' introuvable.")
    else:
        st.sidebar.success("✅ Dossier 'Photos' détecté.")

    uploaded_file = st.sidebar.file_uploader("Charger le fichier CSV", type=["csv", "xlsx"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file, sep=",")
            else: df = pd.read_excel(uploaded_file)
            df.columns = [c.strip() for c in df.columns]
            
            if "Equipe" in df.columns:
                sel_equipe = st.sidebar.selectbox("Equipe", sorted(df["Equipe"].dropna().astype(str).unique()))
                df = df[df["Equipe"].astype(str) == sel_equipe]

            col_session = next((c for c in df.columns if 'session' in str(c).lower()), None)
            if col_session:
                sel_session = st.sidebar.selectbox("Session", sorted(df[col_session].dropna().astype(str).unique()))
                df = df[df[col_session].astype(str) == sel_session]

            players = df["Joueur"].dropna().unique().tolist()
            if not players: return
            selected_player = st.sidebar.selectbox("Joueur", players)
            
            if selected_player:
                player_data = df[df["Joueur"] == selected_player].iloc[0]
                st.sidebar.subheader("Commentaires du Staff")
                dom = st.sidebar.text_area("Points Forts", "Excellent profil physique...")
                weak = st.sidebar.text_area("Axes d'amélioration", "Manque de force excentrique...")
                strat = st.sidebar.text_area("Stratégie", "Renforcement chaîne post...")

                if st.button("Générer le Rapport"):
                    poste = player_data.get("Poste", "-")
                    lat = player_data.get("Latéralité", "-")
                    num = int(player_data.get("Numero", 0)) if pd.notna(player_data.get("Numero")) else 0
                    anthro = {"Age": int(player_data.get("Age", 0)), "Taille": player_data.get("Taille (cm)", "-"), "Poids": player_data.get("Poids (Kg)", "-")}
                    
                    html_content = generate_report(selected_player, player_data, df, poste, lat, num, dom, weak, strat, anthro)
                    st.success("Rapport généré avec succès !")
                    components.html(html_content, height=800, scrolling=True)
                    st.download_button("Télécharger le Rapport HTML", data=html_content, file_name=f"Profil_{selected_player}.html", mime="text/html")

        except Exception as e: st.error(f"Erreur : {e}")

if __name__ == "__main__":
    main()