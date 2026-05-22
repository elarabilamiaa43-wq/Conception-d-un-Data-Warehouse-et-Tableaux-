import os
import sys
import pandas as pd
import numpy as np

# ── Chemins ───────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from db_connect import get_connection

print("⏳ [Étape 3] Modélisation et remplissage du Data Warehouse (Star Schema)...")

# 1. Kan-akhdo l-engine dyal SQLAlchemy
engine = get_connection()

# 2. Kan-jbdw l-connexion brute dyal psycopg2 m3a l-cursor dyalha bach ndiro DROP/CREATE
raw_conn = engine.raw_connection()
cur      = raw_conn.cursor()

# ════════════════════════════════════════════════════════════════
# CRÉATION DU SCHÉMA (Version PostgreSQL sans tranche_min/max)
# ════════════════════════════════════════════════════════════════
cur.execute("CREATE SCHEMA IF NOT EXISTS bi_schema")
# F PostgreSQL n7iyydo tables b CASCADE bach maykonch mochkil dyal Foreign Keys
cur.execute("DROP TABLE IF EXISTS bi_schema.fait_annonce CASCADE;")
cur.execute("DROP TABLE IF EXISTS bi_schema.dim_date CASCADE;")
cur.execute("DROP TABLE IF EXISTS bi_schema.dim_localisation CASCADE;")
cur.execute("DROP TABLE IF EXISTS bi_schema.dim_bien CASCADE;")
cur.execute("DROP TABLE IF EXISTS bi_schema.dim_transaction CASCADE;")
cur.execute("DROP TABLE IF EXISTS bi_schema.dim_prix CASCADE;")

cur.execute("""
CREATE TABLE bi_schema.dim_date (
    date_id          SERIAL PRIMARY KEY,
    date_publication VARCHAR NOT NULL,
    annee            INTEGER NOT NULL,
    mois             INTEGER NOT NULL,
    trimestre        INTEGER NOT NULL
);
""")

cur.execute("""
CREATE TABLE bi_schema.dim_localisation (
    localisation_id  SERIAL PRIMARY KEY,
    ville            VARCHAR NOT NULL,
    quartier         VARCHAR
);
""")

cur.execute("""
CREATE TABLE bi_schema.dim_bien (
    bien_id              SERIAL PRIMARY KEY,
    type_bien            VARCHAR NOT NULL,
    surface              NUMERIC,
    cat_surface          VARCHAR,
    nb_chambres          INTEGER,
    nb_salles_bain       INTEGER,
    etage                INTEGER,
    annee_construction   INTEGER,
    age_estime           INTEGER
);
""")

cur.execute("""
CREATE TABLE bi_schema.dim_transaction (
    transaction_id   SERIAL PRIMARY KEY,
    type_transaction VARCHAR NOT NULL
);
""")

# FIX: Hna hiyydna complètement tranche_min w tranche_max
cur.execute("""
CREATE TABLE bi_schema.dim_prix (
    prix_id        SERIAL PRIMARY KEY,
    categorie_prix VARCHAR NOT NULL
);
""")

cur.execute("""
CREATE TABLE bi_schema.fait_annonce (
    annonce_id      VARCHAR PRIMARY KEY NOT NULL,
    date_id         INTEGER NOT NULL REFERENCES bi_schema.dim_date(date_id),
    localisation_id INTEGER NOT NULL REFERENCES bi_schema.dim_localisation(localisation_id),
    bien_id         INTEGER NOT NULL REFERENCES bi_schema.dim_bien(bien_id),
    transaction_id  INTEGER NOT NULL REFERENCES bi_schema.dim_transaction(transaction_id),
    prix_id         INTEGER NOT NULL REFERENCES bi_schema.dim_prix(prix_id),
    prix            NUMERIC NOT NULL,
    prix_m2         NUMERIC
);
""")
raw_conn.commit()

# ════════════════════════════════════════════════════════════════
# LECTURE CLEANED_ANNONCES (Version Sécurisée)
# ════════════════════════════════════════════════════════════════
try:
    df = pd.read_sql_query("SELECT * FROM cleaned_annonces", engine)
except Exception as e:
    cur.close()
    raw_conn.close()
    raise RuntimeError(f"❌ Impossible de lire la table 'cleaned_annonces'. Erreur : {e}")

print(f"   📋 CLEANED_ANNONCES : {len(df)} lignes")

# ════════════════════════════════════════════════════════════════
# REMPLISSAGE DES DIMENSIONS
# ════════════════════════════════════════════════════════════════

# 1. DIM_DATE
dim_date = df[['date_publication', 'annee', 'mois', 'trimestre']].drop_duplicates().reset_index(drop=True)
dim_date['date_publication'] = dim_date['date_publication'].astype(str)
dim_date.to_sql("dim_date", engine, if_exists="append", schema="bi_schema", index=False)

# 2. DIM_LOCALISATION
dim_localisation = df[['ville', 'quartier']].drop_duplicates().reset_index(drop=True)
dim_localisation.to_sql("dim_localisation", engine, if_exists="append", schema="bi_schema", index=False)

# 3. DIM_BIEN
dim_bien = df[['type_bien', 'surface', 'cat_surface', 'nb_chambres', 'nb_salles_bain', 'etage', 'annee_construction', 'age_estime']].drop_duplicates().reset_index(drop=True)
dim_bien.to_sql("dim_bien", engine, if_exists="append", schema="bi_schema", index=False)

# 4. DIM_TRANSACTION
dim_transaction = df[['transaction']].drop_duplicates().reset_index(drop=True)
dim_transaction.columns = ['type_transaction']
dim_transaction.to_sql("dim_transaction", engine, if_exists="append", schema="bi_schema", index=False)

# 5. DIM_PRIX (FIX: Ghir categorie_prix bo7dha daba)
dim_prix = df[['categorie_prix']].drop_duplicates().reset_index(drop=True)
dim_prix.to_sql("dim_prix", engine, if_exists="append", schema="bi_schema", index=False)

print("   ✅ Dimensions insérées avec succès.")

# ════════════════════════════════════════════════════════════════
# LECTURE DES IDS GÉNÉRÉS POUR CONSTRUIRE LA TABLE DE FAITS
# ════════════════════════════════════════════════════════════════
db_date = pd.read_sql_query("SELECT date_id, date_publication FROM bi_schema.dim_date", engine)
db_loc  = pd.read_sql_query("SELECT localisation_id, ville, quartier FROM bi_schema.dim_localisation", engine)
db_bien = pd.read_sql_query("SELECT bien_id, type_bien, surface, nb_chambres FROM bi_schema.dim_bien", engine)
db_trans = pd.read_sql_query("SELECT transaction_id, type_transaction FROM bi_schema.dim_transaction", engine)
db_prix = pd.read_sql_query("SELECT prix_id, categorie_prix FROM bi_schema.dim_prix", engine)

# Mapping / Merging pour récupérer les Foreign Keys
df['date_publication_str'] = df['date_publication'].astype(str)
db_date['date_publication_str'] = db_date['date_publication'].astype(str)

fait = df.merge(db_date, on='date_publication_str', how='left')
fait = fait.merge(db_loc, on=['ville', 'quartier'], how='left')
fait = fait.merge(db_bien, on=['type_bien', 'surface', 'nb_chambres'], how='left')
fait = fait.merge(db_trans, left_on='transaction', right_on='type_transaction', how='left')
fait = fait.merge(db_prix, on='categorie_prix', how='left')

fait_annonce = fait[['annonce_id', 'date_id', 'localisation_id', 'bien_id', 'transaction_id', 'prix_id', 'prix', 'prix_par_m2']].copy()
fait_annonce.columns = ['annonce_id', 'date_id', 'localisation_id', 'bien_id', 'transaction_id', 'prix_id', 'prix', 'prix_m2']

fait_annonce = fait_annonce.drop_duplicates(subset='annonce_id')
fait_annonce.to_sql("fait_annonce", engine, if_exists="append", schema="bi_schema", index=False)

print("   ✅ Table de faits (FAIT_ANNONCE) insérée avec succès.")

# ════════════════════════════════════════════════════════════════
# CONTRÔLE DE COHÉRENCE
# ════════════════════════════════════════════════════════════════
print("\n" + "═"*55)
print("  CONTRÔLE DE COHÉRENCE")
print("═"*55)

checks = {
    "FAIT — FK date_id nulles"        : "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE date_id IS NULL",
    "FAIT — FK localisation_id nulles": "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE localisation_id IS NULL",
    "FAIT — FK bien_id nulles"        : "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE bien_id IS NULL",
    "FAIT — FK transaction_id nulles" : "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE transaction_id IS NULL",
    "FAIT — FK prix_id nulles"        : "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE prix_id IS NULL",
    "FAIT — prix NULL ou négatif"     : "SELECT COUNT(*) FROM bi_schema.fait_annonce WHERE prix IS NULL OR prix < 0",
    "DIM_DATE — doublons"             : "SELECT COUNT(*)-COUNT(DISTINCT date_id) FROM bi_schema.dim_date",
    "DIM_LOC — ville NULL"            : "SELECT COUNT(*) FROM bi_schema.dim_localisation WHERE ville IS NULL",
}

for label, query in checks.items():
    cur.execute(query)
    res = cur.fetchone()[0]
    status = "❌" if res > 0 else "✅"
    print(f" {status} {label:<35} : {res}")

# Fermeture sécurisée
cur.close()
raw_conn.close()
print("\n🏁 [Pipeline Terminé avec Succès dans PostgreSQL !]")