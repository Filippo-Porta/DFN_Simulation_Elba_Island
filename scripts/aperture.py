import os
import pandas as pd

# Base path where all simulation runs are stored
base_path = "/hpc/archive/G_NEXT/runs/"
output_file = "aperture_cumulative.csv"

all_data = []

print("Starting folder scan...")

# List of run folders (18, 19, 20...)
folders = sorted([f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))])

for run_folder in folders:
    file_path = os.path.join(base_path, run_folder, "output_backbone", "aperture.dat")

    if os.path.exists(file_path):
        print(f"Processing Run {run_folder}...")
        try:
            # Read the .dat file
            # sep='\s+' handles multiple spaces or tabs
            df = pd.read_csv(file_path, sep='\s+', skiprows=1, header=None)

            # Select the fourth column (aperture)
            apertures = df[3].values

            # Create a DataFrame for this specific run
            # Column A: run ID, Column B: aperture value
            temp_df = pd.DataFrame({
                'run_id': run_folder,
                'aperture': apertures
            })

            all_data.append(temp_df)

        except Exception as e:
            print(f"Error reading Run {run_folder}: {e}")

# Merge all data into a single file
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)

    # Save as CSV using semicolon as separator
    final_df.to_csv(output_file, index=False, sep=';')
    print(f"--- Done! ---")
    print(f"File saved: {output_file}")
    print(f"Sample content:\n{final_df.head()}")
else:
    print("No data found.")