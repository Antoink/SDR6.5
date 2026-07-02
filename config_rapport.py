import pandas as pd
import re
import unicodedata

SDR_RED = "#D71920"

# ==========================================
# 1. MAPPING DES COLONNES (UI -> EXCEL)
# ==========================================
COL_MAPPING = {
    # --- INFO JOUEUR & ANTHROPO ---
    "Joueur": "Joueur", "Equipe": "Equipe", "Age": "Age", 
    "Poids": "Poids (kg)", "Taille": "Taille (cm)", "Masse Grasse": "Masse grasse",
    "Poste": "Poste", "Position": "Position",
    
    # --- TESTS PHYSIQUES ---
    "Knee To Wall (G)": "Knee to wall G", "Knee To Wall (D)": "Knee to wall D",
    "Sit And Reach": "Sit and reach",
    "Somme ADD": "Somme ADD", "Adducteurs (G)": "Adducteur G", "Adducteurs (D)": "Adducteur D",
    "Ratio Squeeze": "Ratio Squeeze (ADD/ABD)",
    "Somme ABD": "Somme ABD", "Abducteurs (G)": "Abducteur G", "Abducteurs (D)": "Abducteur D",
    "Nordic Ischio (G)": "Nordic G", "Nordic Ischio (D)": "Nordic D",
    "Inverseur (G)": "Inverseur G", "Inverseur (D)": "Inverseur D",
    "Everseur (G)": "Everseur G", "Everseur (D)": "Everseur D",
    "Endurance Heel Raise (G)": "Endurance Heel Raise G", "Endurance Heel Raise (D)": "Endurance Heel Raise D",
    
    
    
    # --- SAUTS & EXPLOSIVITE ---
    "CMJ 2JB": "CMJ 2JB", 
    "Peak Force CMJ": "Peak Force CMJ", 
    "RFD CMJ": "RFD CMJ", 
    "RSI CMJ": "RSI", 
    "Squat belt (N)": "Squat belt (N)",
    "Wattbike (6s)": "Wattbike 6s (W)",
    
    # --- COURSE & METABOLIQUE ---
    "SV1": "SV1", "SV2": "SV2", "FC": "FC", "VMA": "VMA",
    "Distance Totale": "Distance totale", "Distance HSR": "Distance HSR", "Distance Sprint (92% Vimax)": "Distance Sprint (92% Vimax)",
    "Vmax": "Vmax", "Amax": "Amax", "Dmax": "Dmax",
    "Temps sur 10m": "Temps sur 10m",
    
    # --- ISOCINETISME ---
    "Q Conc 60° (G)": "Q G conc 60°/s", "Q Conc 60° (D)": "Q Dt conc 60°/s",
    "Q Conc 240° (G)": "Q G conc 240°/s", "Q Conc 240° (D)": "Q Dt conc 240°/s",
    "IJ Conc 60° (G)": "IJ G conc 60°/s", "IJ Conc 60° (D)": "IJ Dt conc 60°/s",
    "IJ Conc 240° (G)": "IJ G conc 240°/s", "IJ Conc 240° (D)": "IJ Dt conc 240°/s",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s", "IJ Exc 30° (D)": "IJ Dt exc 30°/s"
}

# ==========================================
# 2. STRUCTURE DES MENUS DÉROULANTS & COMPARATEUR
# ==========================================
OFFICIAL_STRUCTURE = {
    "PROFILAGE MOTEUR": [
        "Knee To Wall (G)", "Knee To Wall (D)", "Sit And Reach",
        "Somme ADD", "Somme ABD", "Ratio Squeeze",
        "Adducteurs (G)", "Adducteurs (D)", 
        "Abducteurs (G)", "Abducteurs (D)",
        "Nordic Ischio (G)", "Nordic Ischio (D)",
        "Inverseur (G)", "Inverseur (D)", "Everseur (G)", "Everseur (D)",
        "Endurance Heel Raise (G)", "Endurance Heel Raise (D)",
        
    ],
    "PROFILAGE ATHLÉTIQUE": [
        "CMJ 2JB", "Peak Force CMJ", "RFD CMJ", "RSI CMJ",
        "Wattbike (6s)", "Squat belt (N)"
    ],
    "PROFILAGE PHYSIOLOGIQUE": [
        "VMA", "SV1", "SV2", "FC", "Temps sur 10m", 
        "Distance Totale", "Distance HSR", "Distance Sprint (92% Vimax)",
        "Vmax", "Amax", "Dmax"
    ]
}

TEAM_STRUCTURE = OFFICIAL_STRUCTURE.copy()
TEAM_STRUCTURE["ANALYSE DÉTAILLÉE (BIODEX)"] = [
    "Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)",
    "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)",
    "IJ Exc 30° (G)", "IJ Exc 30° (D)"
]

# ==========================================
# 3. NORMES & UNITES 
# ==========================================
REPORT_NORMES = {
    "VMA": 15, "Vmax": 32, "CMJ 2JB": 40, "Peak Force CMJ": 2000,
    "Nordic": 30, "Adducteur": 4, "Knee To Wall (G)": 9, "Knee To Wall (D)": 9,
    "Sit And Reach": 20, "Distance HSR": 800,
    "Distance Totale": 8000, "Amax": 5, "Dmax": 5, "Distance Sprint (92% Vimax)": 60,
    "Somme ADD": 34, "Somme ABD": 34, "Ratio Squeeze": [0.90, 1.10],
    "Nordic Ischio (G)": 0.7, "Nordic Ischio (D)": 0.7,
    "Q Conc 60° (G)": 2.8, "Q Conc 60° (D)": 2.8,
    "Q Conc 240° (G)": 1.9, "Q Conc 240° (D)": 1.9,
    "IJ Conc 60° (G)": 1.5, "IJ Conc 60° (D)": 1.5,
    "IJ Conc 240° (G)": 1.2, "IJ Conc 240° (D)": 1.2,
    "IJ Exc 30° (G)": 2.0, "IJ Exc 30° (D)": 2.0,
    "Wattbike (6s)": 1100, "Squat belt (N)": 1500,
    "Temps sur 10m": 1.90
}

RELATIVE_NORM_KEYS = [
    "Nordic Ischio (G)", "Nordic Ischio (D)",
    "Q Conc 60° (G)", "Q Conc 60° (D)",
    "Q Conc 240° (G)", "Q Conc 240° (D)",
    "IJ Conc 60° (G)", "IJ Conc 60° (D)",
    "IJ Conc 240° (G)", "IJ Conc 240° (D)",
    "IJ Exc 30° (G)", "IJ Exc 30° (D)"
]

UNITS = {
    "Peak Force CMJ": "N",
    "RFD CMJ": "N/s",
    "RSI CMJ": "m/s",
    "Squat belt (N)": "N", "CMJ 2JB": "cm", "Knee To Wall (G)": "cm", "Knee To Wall (D)": "cm", 
    "Sit And Reach": "cm", "Somme ADD": "N", "Somme ABD": "N",
    "Adducteurs (G)": "N", "Adducteurs (D)": "N", "Abducteurs (G)": "N", "Abducteurs (D)": "N",
    "Nordic Ischio (G)": "Kg", "Nordic Ischio (D)": "Kg",
    "Inverseur (G)": "Kg", "Inverseur (D)": "Kg", "Everseur (G)": "Kg", "Everseur (D)": "Kg",
    "Endurance Heel Raise (G)": "Reps", "Endurance Heel Raise (D)": "Reps",

    "Wattbike (6s)": "W", "SV1": "km/h", "SV2": "km/h", "FC": "bpm", "VMA": "km/h",
    "Distance Totale": "m", "Distance HSR": "m", "Distance Sprint (92% Vimax)": "m",
    "Vmax": "km/h", "Amax": "m/s²", "Dmax": "m/s²", "Temps sur 10m": "s",
    "Q Conc 60° (G)": "Nm", "Q Conc 60° (D)": "Nm", "Q Conc 240° (G)": "Nm", "Q Conc 240° (D)": "Nm",
    "IJ Conc 60° (G)": "Nm", "IJ Conc 60° (D)": "Nm", "IJ Conc 240° (G)": "Nm", "IJ Conc 240° (D)": "Nm",
    "IJ Exc 30° (G)": "Nm", "IJ Exc 30° (D)": "Nm",
    "Ratio Squeeze": "", "Ratio Mixte (G)": "", "Ratio Mixte (D)": ""
}