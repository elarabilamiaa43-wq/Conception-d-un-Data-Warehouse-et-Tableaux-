import os
import sys
import time
import subprocess
 
# Racine du projet = dossier où se trouve ce fichier
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
 
# Python courant du venv (celui qui exécute CE fichier)
PYTHON = sys.executable
 
 
def run_step(label, script_name):
    print(f"\n{'═'*58}")
    print(f"  🚀  {label}")
    print(f"{'═'*58}")
 
    script_path = os.path.join(SCRIPTS_DIR, script_name)
 
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"❌ Script introuvable : {script_path}")
 
    t0 = time.time()
 
    result = subprocess.run(
        [PYTHON, script_path],
        cwd=ROOT_DIR,          # CWD = racine du projet
        text=True,
        check=False,
    )
 
    elapsed = time.time() - t0
 
    if result.returncode != 0:
        raise RuntimeError(f"❌ '{script_name}' a échoué (code {result.returncode})")
 
    print(f"  ⏱️   Terminé en {elapsed:.2f}s")
 
 
try:
    run_step("ÉTAPE 1 — Staging   (CSV brut → STAGING_ANNONCES)",  "staging.py")
    run_step("ÉTAPE 2 — Cleaning  (nettoyage → CLEANED_ANNONCES)", "clean.py")
    run_step("ÉTAPE 3 — Warehouse (Star Schema → bi_schema.db)",   "warehouse.py")
 
    print(f"\n{'═'*58}")
    print("  ✅  PIPELINE COMPLET !")
    print(f"  📂  {os.path.join(ROOT_DIR, 'bi_schema.db')}")
    print("  🔌  Connectez Power BI via : Get Data → SQLite")
    print(f"{'═'*58}\n")
 
except Exception as e:
    print(f"\n❌  ERREUR : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)