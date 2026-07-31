from pydfnworks import *
import os
import numpy as np
import shutil
import sys
import json

# =========================
# SEED INPUT
# =========================
if len(sys.argv) != 2:
    print("Usage: python alpha_variabile.py <seed>")
    sys.exit(1)

seed = int(sys.argv[1])

# =========================
# FUNCTIONS
# =========================
def get_keff(filename):
    with open(filename) as f:
        for line in f:
            if 'effective perm' in line:
                return float(line.split()[-1])
    return None


def apply_alpha_properties(DFN, alpha):
    result = DFN.generate_hydraulic_values(
        "aperture",
        "correlated",
        {"alpha": alpha, "beta": 0.5}
    )

    if isinstance(result, tuple) and len(result) == 3:
        b, perm, T = result
        try:
            DFN.dump_hydraulic_values(b, perm, T)
        except TypeError:
            DFN.dump_hydraulic_values(b, perm, T, None)
        return

    if result is None:
        return

    raise RuntimeError(f"Unexpected return: {type(result)}")


# =========================
# PARAMETERS
# =========================
home = os.getcwd()
dfnTrans_file = os.path.join(home, "PTDFN_control.dat")

alpha_values = [5e-6, 1.0e-4, 5e-4, 5.0e-5, 5.0e-3]
directions = ['x', 'y', 'z']
inflow_pressure = 2e6
outflow_pressure = 1.95e6

all_results = []

try:
    print(f"\n=== START seed {seed} ===")

    # =========================
    # DFN GENERATION
    # =========================
    dfn_dir = os.path.join(home, f"perm_tensor_seed_{seed}")

    DFN = DFNWORKS(
        dfn_dir,
        dfnTrans_file=dfnTrans_file,
        ncpu=8
    )

    DFN.params['domainSize']['value'] = [50, 50, 50]
    DFN.params['domainSizeIncrease']['value'] = [24, 24, 24]
    DFN.params['ignoreBoundaryFaces']['value'] = False
    DFN.params['boundaryFaces']['value'] = [1, 1, 1, 1, 1, 1]
    DFN.params['stopCondition']['value'] = 1
    DFN.params['rejectsPerFracture']['value'] = 2
    DFN.params['seed']['value'] = seed
    DFN.params['h']['value'] = 0.1
    DFN.params['angleOption']['value'] = 'degree'

    DFN.params['orientationOption']['value'] = 2
    alpha0 = alpha_values[0]

    # Fracture families
    DFN.add_fracture_family(
        shape="ell", distribution="tpl",
        alpha=1.12, kappa=31.94, p32=0.48,
        aspect=1.0, dip=68, strike=63.53,
        min_radius=1, max_radius=23.59,
        hy_variable="aperture", hy_function="correlated",
        hy_params={"alpha": alpha0, "beta": 0.5}
    )

    DFN.add_fracture_family(
        shape="ell", distribution="tpl",
        alpha=1.23, kappa=52.98, p32=0.42,
        aspect=1.0, dip=81, strike=90.98,
        min_radius=1, max_radius=18.8,
        hy_variable="aperture", hy_function="correlated",
        hy_params={"alpha": alpha0, "beta": 0.5}
    )

    DFN.add_fracture_family(
        shape="ell", distribution="tpl",
        alpha=1.7, kappa=6.04, p32=0.21,
        aspect=1.0, dip=51, strike=144.79,
        min_radius=1, max_radius=13.226,
        hy_variable="aperture", hy_function="correlated",
        hy_params={"alpha": alpha0, "beta": 0.5}
    )

    DFN.make_working_directory(delete=True)
    DFN.check_input()
    DFN.create_network()

    G = DFN.create_graph("fracture", "front", "back")
    H = DFN.current_flow_threshold(G, "s", "t", thrs=1e-16)

    DFN.dump_fractures(H, "backbone.dat")
    DFN.to_pickle()

    del DFN

    # =========================
    # BACKBONE
    # =========================
    jobname = os.path.join(home, f"output_backbone_seed_{seed}")
    src_path = dfn_dir + os.sep

    BACKBONE = DFNWORKS(
        jobname=jobname,
        pickle_file=os.path.join(src_path, f"perm_tensor_seed_{seed}.pkl"),
        ncpu=8,
        dfnTrans_file=dfnTrans_file,
    )

    BACKBONE.prune_file = os.path.join(src_path, "backbone.dat")
    BACKBONE.path = src_path
    BACKBONE.jobname = jobname + os.sep
    BACKBONE.local_jobname = "output_backbone"

    BACKBONE.assign_hydraulic_properties()
    BACKBONE.make_working_directory(delete=True)
    BACKBONE.params['h']['value'] = 0.1

    BACKBONE.mesh_network(min_dist=1, max_dist=5, max_resolution_factor=10)

    # =========================
    # ALPHA LOOP
    # =========================
    for alpha_id, alpha in enumerate(alpha_values, start=1):

        print(f"\n  -> alpha {alpha}")

        apply_alpha_properties(BACKBONE, alpha)
        BACKBONE.lagrit2pflotran()

        row = {
            "dfn_id": seed,
            "seed": seed,
            "alpha_id": alpha_id,
            "alpha": alpha
        }

        for direction in directions:

            BACKBONE.dfnFlow_file = os.path.join(home, f"dfn_steady_pressure_{direction}.in")
            BACKBONE.local_dfnFlow_file = f"dfn_steady_pressure_{direction}.in"

            BACKBONE.pflotran()
            BACKBONE.pflotran_cleanup()

            boundary_file = {
                "x": "boundary_left_w.ex",
                "y": "boundary_front_n.ex",
                "z": "boundary_bottom.ex"
            }[direction]

            BACKBONE.effective_perm(
                inflow_pressure, outflow_pressure,
                boundary_file, direction
            )

            fname = f"{BACKBONE.local_jobname}_seed{seed}_alpha{alpha_id}_{direction}.txt"
            os.rename(f"{BACKBONE.local_jobname}_effective_perm.txt", fname)

            keff = get_keff(fname)
            row[f"keff_{direction}"] = keff

        all_results.append(row)

    # =========================
    # SAVE JSON
    # =========================
    output_json = os.path.join(home, f"results_seed_{seed}.json")

    with open(output_json, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"=== SUCCESS seed {seed} ===")
    sys.exit(0)

except Exception as e:
    print(f"\n!!! ERROR seed {seed} !!!")
    print(e)

    shutil.rmtree(os.path.join(home, f"perm_tensor_seed_{seed}"), ignore_errors=True)
    shutil.rmtree(os.path.join(home, f"output_backbone_seed_{seed}"), ignore_errors=True)

    sys.exit(1)
