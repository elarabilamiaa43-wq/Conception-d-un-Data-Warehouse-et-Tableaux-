import os
import sys
import pandas as pd
 
# ── Chemins ───────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)          # pour importer db_connect
 
from db_connect import get_connection
 
CSV_PATH = os.path.join(ROOT_DIR, "Data", "darkom-annonces-6a0a532a16460470060059.csv")
 
print("⏳ [Étape 1] Chargement du CSV brut → STAGING_ANNONCES...")
 
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"❌ CSV introuvable : {CSV_PATH}")
 
df_raw = pd.read_csv(CSV_PATH)
 
engine = get_connection()

with engine.connect() as connection:
    df_raw.to_sql("STAGING_ANNONCES", connection, if_exists="replace", index=False)

print(f"✅ STAGING terminé : {len(df_raw)} lignes chargées dans STAGING_ANNONCES.")