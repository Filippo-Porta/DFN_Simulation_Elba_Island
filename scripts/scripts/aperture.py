import os
import pandas as pd

# Percorso base dove si trovano tutte le tue runs
base_path = "/hpc/archive/G_NEXT/runs/" 
output_file = "aperture_cumulativo.csv"

all_data = []

print("Inizio scansione cartelle...")

# Lista delle cartelle (18, 19, 20...)
folders = sorted([f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))])

for run_folder in folders:
    file_path = os.path.join(base_path, run_folder, "output_backbone", "aperture.dat")
    
    if os.path.exists(file_path):
        print(f"Processando Run {run_folder}...")
        try:
            # Leggiamo il file .dat
            # sep='\s+' gestisce spazi multipli o tabulazioni
            df = pd.read_csv(file_path, sep='\s+', skiprows=1, header=None)
            
            # Prendiamo la quarta colonna (aperture)
            apertures = df[3].values
            
            # Creiamo un DataFrame per questa specifica Run
            # Colonna A: ID della run, Colonna B: valore apertura
            temp_df = pd.DataFrame({
                'run_id': run_folder,
                'aperture': apertures
            })
            
            all_data.append(temp_df)
            
        except Exception as e:
            print(f"Errore nella lettura di Run {run_folder}: {e}")

# Uniamo tutto in un unico file
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Salviamo in CSV usando la virgola come separatore
    final_df.to_csv(output_file, index=False, sep=';')
    print(f"--- Fatto! ---")
    print(f"File salvato: {output_file}")
    print(f"Esempio contenuto:\n{final_df.head()}")
else:
    print("Nessun dato trovato.")
