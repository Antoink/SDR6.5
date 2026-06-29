import os
import pandas as pd
import csv
import re
import io

DOSSIER_BRUT = "CMJ_Brut"
FICHIER_SORTIE = "CMJ20262027.csv"

# Ordre EXACT et complet de tes colonnes
COLONNES_ATTENDUES = [
    "Joueur", "Poids_de_corps_N", "Poids_kg", "Fichier_Source", 
    "Hauteur de Saut TV (cm)", "Hauteur de saut (Vitesse) (cm)", "Temps de Contraction (ms)", 
    "Temps de Mouvement (ms)", "Pic de Force Max (N)", "Pic de Puissance Max (W)", 
    "Pic de Vitesse Max (m/s)", "Pic de RFD Max (N/s)", "Impulsion Totale (N•s)", 
    "Vitesse à Puissance Maximale(m/s)", "Force à Puissance Maximale (N)", "Pic de RPD Max (W/s)", 
    "RSI (TV/TC)", "mRSI (JH/CT) (m/s)", "mRSI (JH/TTT) (m/s)", "Rigidité de la jambe (N/m)", 
    "Temps jusqu'au pic de force Max (ms)", "Temps jusqu'au pic de Puissance Max (ms)", 
    "Force Moyenne (N)", "Force Max Nette (N)", "Impulsion totale Nette (N•s)", 
    "RFD moyenne (N/s)", "Puissance Moyenne (W)", "nan", "Phase de Décharge - Durée (ms)", 
    "Phase de Décharge - Force Minimale(N)", "Phase de Décharge - Pic de Décharge (N)", 
    "Phase de Décharge - RFD Max Négative (N/s)", "Phase de Décharge - Impulsion Totale (N•s)", 
    "Phase de Décharge - Impulsion Nette (N•s)", "Phase de Freinage - Durée (ms)", 
    "Phase de Freinage - Force de Freinage Max (N)", "Phase de Freinage - Force de Freinage Moy (N)", 
    "Phase de Freinage - Puissance de Freinage Max (W)", "Phase de Freinage - RFD moyenne (N/s)", 
    "Phase de Freinage - RFD 0-50ms (N/s)", "Phase de Freinage - RFD 0-100ms (N/s)", 
    "Phase de Freinage - RFD 0-150ms (N/s)", "Phase de Freinage - RFD 0-200ms (N/s)", 
    "Phase de Freinage - RFD 50-100ms (N/s)", "Phase de Freinage - RFD 100-150ms (N/s)", 
    "Phase de Freinage - RFD 150-200ms (N/s)", "Phase de Freinage - Impulsion de freinage (N•s)", 
    "Phase de Freinage - Impulsion 50-100ms (N•s)", "Phase de Freinage - Impulsion 100-150ms (N•s)", 
    "Phase de Freinage - Impulsion 150-200ms (N•s)", "Phase de Freinage - Force de Freinage Moy Nette (N)", 
    "Phase de Freinage - Impulsion de freinage nette (N•s)", "Phase de Freinage - Déplacement Min (cm)", 
    "Phase de Freinage - Vitesse Négative Max (m/s)", "Phase de Freinage - RFD Décélération (N/s)", 
    "Phase de Freinage - RFD Excentrique (N/s)", "Propulsion - Durée (ms)", 
    "Propulsion - Force Propulsive Max (N)", "Propulsion - Force Propulsive Moy (N)", 
    "Propulsion - Puissance Propulsive Max (W)", "Propulsion - Puissance Propulsive Moy (W)", 
    "Propulsion - RPD Moyen(W/s)", "Propulsion - RPD 0-50ms (W/s)", "Propulsion - RPD 0-100ms (W/s)", 
    "Propulsion - RPD 0-150ms (W/s)", "Propulsion - RPD 0-200ms (W/s)", "Propulsion - Impulsion Propulsive (N•s)", 
    "Propulsion - Impulsion Propulsive Phase 1 (N•s)", "Propulsion - Impulsion Propulsive Phase 2 (N•s)", 
    "Propulsion - Force Propulsive Max Nette (N)", "Propulsion - Force Propulsive Moy Nette (N)", 
    "Propulsion - Impulsion Propulsive Nette (N•s)", "Propulsion - Vitesse Propulsive Max (m/s)", 
    "Vol - Durée (ms)", "Hauteur de Saut + Temps de vol (cm)", 
    "Vol - Hauteur du saut en fonction de la vitesse de décollage (cm)", "Vol - Vitesse au décollage (m/s)", 
    "Force Max à l'Atterrissage (N)", "Ratio Pic de force d'atterrissage/poids du corps (N/kg)", 
    "Force d'Atterrissage Moy (N)", "Atterrissage - Temps de Stabilisation (ms)"
]

def process_kinvent_file(filepath):
    current_jump_data = {col: None for col in COLONNES_ATTENDUES}
    filename = os.path.basename(filepath)
    current_jump_data['Fichier_Source'] = filename
    
    match = re.search(r"mouvement_(.*?)__", filename)
    if match:
        raw_name = match.group(1).replace('_', ' ')
        parts = raw_name.split()
        if len(parts) >= 2:
            current_jump_data['Joueur'] = f"{parts[1]} {parts[0].upper()}"
        else:
            current_jump_data['Joueur'] = raw_name
    else:
        current_jump_data['Joueur'] = "Inconnu"

    with open(filepath, 'r', encoding='utf-8') as f:
        try: lines = f.readlines()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f_alt:
                lines = f_alt.readlines()

    for line in lines:
        if "Poids de corps (N)" in line:
            try:
                poids_n = float(line.split(',')[1].strip())
                current_jump_data['Poids_de_corps_N'] = poids_n
                current_jump_data['Poids_kg'] = round(poids_n / 9.81, 2)
            except: pass
            break

    params_start, params_end = -1, -1
    phase_start, phase_end = -1, -1

    for i, line in enumerate(lines):
        clean_line = line.strip()
        if clean_line == "Paramètres": params_start = i + 3
        if clean_line == "Paramètres par phase":
            params_end = i - 1
            phase_start = i + 3
        if (clean_line == "Données brutes" or clean_line == "Données brutes du canal") and phase_start != -1:
            phase_end = i - 1
            break
            
    if phase_start != -1 and phase_end == -1:
        phase_end = len(lines)

    if params_start != -1 and params_end > params_start:
        table_str = "".join(lines[params_start:params_end])
        try:
            df_params = pd.read_csv(io.StringIO(table_str), sep=',', header=None)
            for _, row in df_params.iterrows():
                if pd.isna(row[0]): continue
                metric_name = str(row[0]).strip()
                try:
                    val = pd.to_numeric(row[8], errors='coerce')
                    if metric_name in current_jump_data and pd.notna(val):
                        current_jump_data[metric_name] = val
                except: pass
        except: pass

    if phase_start != -1 and phase_end > phase_start:
        table_str = "".join(lines[phase_start:phase_end])
        try:
            df_phase = pd.read_csv(io.StringIO(table_str), sep=',', header=None)
            for _, row in df_phase.iterrows():
                try:
                    phase_name = str(row[0]).strip()
                    metric_name = str(row[1]).strip()
                    if pd.isna(phase_name) or pd.isna(metric_name): continue

                    if phase_name.lower() not in metric_name.lower():
                        full_metric_name = f"{phase_name} - {metric_name}"
                    else:
                        full_metric_name = metric_name
                    
                    val = pd.to_numeric(row[9], errors='coerce')
                    if full_metric_name in current_jump_data and pd.notna(val):
                        current_jump_data[full_metric_name] = val
                except: pass
        except: pass

    if current_jump_data.get('Hauteur de saut (Vitesse) (cm)') is not None:
        current_jump_data['Hauteur de Saut TV (cm)'] = current_jump_data['Hauteur de saut (Vitesse) (cm)']

    # ------- NOTIFICATION POUR LE STAFF --------
    t_freinage = current_jump_data.get("Phase de Freinage - Durée (ms)")
    if t_freinage and t_freinage < 200:
        print(f"   ℹ️ Info: Freinage de {current_jump_data['Joueur']} très rapide ({t_freinage}ms). Les valeurs > 100ms seront vides.")
        
    return current_jump_data

def main():
    if not os.path.exists(DOSSIER_BRUT):
        os.makedirs(DOSSIER_BRUT)
        print(f"⚠️ Le dossier '{DOSSIER_BRUT}' vient d'être créé. Placez vos CSV à l'intérieur.")
        return
        
    fichiers_csv = [f for f in os.listdir(DOSSIER_BRUT) if f.endswith('.csv')]
    if not fichiers_csv:
        print(f"⚠️ Aucun fichier CSV trouvé dans '{DOSSIER_BRUT}'.")
        return
        
    tous_les_joueurs = []
    print(f"🔄 Traitement de {len(fichiers_csv)} fichier(s) en cours...")
    
    for fichier in fichiers_csv:
        chemin = os.path.join(DOSSIER_BRUT, fichier)
        donnees_joueur = process_kinvent_file(chemin)
        tous_les_joueurs.append(donnees_joueur)
        print(f"   ✅ Fichier traité : {donnees_joueur['Joueur']}")
        
    df_final = pd.DataFrame(tous_les_joueurs, columns=COLONNES_ATTENDUES)
    df_final.to_csv(FICHIER_SORTIE, index=False, sep=";", encoding='utf-8-sig')
    
    print(f"\n🎉 Terminé ! Le fichier consolidé '{FICHIER_SORTIE}' a été créé avec succès.")

if __name__ == "__main__":
    main()