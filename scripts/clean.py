import os
import sys
import pandas as pd
import numpy as np

# ── Chemins ───────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from db_connect import get_connection

CSV_PATH    = os.path.join(ROOT_DIR, "Data", "darkom-annonces-6a0a532a16460470060059.csv")
OUTPUT_CSV  = os.path.join(ROOT_DIR, "Data", "darkom_cleaned.csv")

print("⏳ [Étape 2] Nettoyage des données...")

df = pd.read_csv(CSV_PATH)

# Normalise toutes les colonnes : minuscules + sans espaces parasites
df.columns = df.columns.str.strip().str.lower()

# ════════════════════════════════════════════════════════════════
# PARTIE 1 — NETTOYAGE DE BASE
# ════════════════════════════════════════════════════════════════

# STEP 1 — Drop duplicates
df = df.drop_duplicates(subset="annonce_id", keep="first")

# STEP 2 — Sort + ffill/bfill date
df["date_publication"] = pd.to_datetime(df["date_publication"])
df = df.sort_values("date_publication").reset_index(drop=True)
df["date_publication"] = df["date_publication"].ffill().bfill()

# STEP 3 — Quartier : mode par ville
df["quartier"] = df["quartier"].fillna(
    df.groupby("ville")["quartier"].transform(
        lambda x: x.mode()[0] if not x.mode().empty else np.nan
    )
)

# STEP 4 — type_bien depuis les 3 premiers mots du titre
def extract_type_from_titre(row):
    if pd.notna(row["type_bien"]):
        return row["type_bien"]
    titre = str(row["titre"]).lower()
    first_words = " ".join(titre.split()[:3])
    for kw, val in [("appartement","Appartement"),("villa","Villa"),
                    ("terrain","Terrain"),("bureau","Bureau"),("duplex","Duplex")]:
        if kw in first_words:
            return val
    return row["type_bien"]

df["type_bien"] = df.apply(extract_type_from_titre, axis=1)

# STEP 5 — transaction selon prix
SEUIL = 50_000
def fill_transaction(row):
    if pd.notna(row["transaction"]):
        return row["transaction"]
    return "Vente" if row["prix"] >= SEUIL else "Location"

df["transaction"] = df.apply(fill_transaction, axis=1)

# STEP 6 — médiane par type_bien
for col in ["nb_chambres", "nb_salles_bain", "etage"]:
    df[col] = df[col].fillna(df.groupby("type_bien")[col].transform("median"))

# STEP 7 — annee_construction : médiane par ville puis globale
df["annee_construction"] = df.groupby("ville")["annee_construction"].transform(
    lambda x: x.fillna(x.median())
)
df["annee_construction"] = df["annee_construction"].fillna(df["annee_construction"].median())

# ════════════════════════════════════════════════════════════════
# PARTIE 2 — OUTLIERS IQR (drop)
# ════════════════════════════════════════════════════════════════

def iqr_mask(series, factor=1.5):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return (series >= Q1 - factor * IQR) & (series <= Q3 + factor * IQR)

before = len(df)
df = df[
    iqr_mask(df["prix"]) &
    iqr_mask(df["surface"]) &
    iqr_mask(df["nb_chambres"])
].reset_index(drop=True)
print(f"   🗑️  Outliers supprimés : {before - len(df)} | Restantes : {len(df)}")

# ════════════════════════════════════════════════════════════════
# PARTIE 3 — STANDARDISATION
# ════════════════════════════════════════════════════════════════

ville_mapping = {
    "casablanca":"Casablanca","casa":"Casablanca","rabat":"Rabat",
    "marrakech":"Marrakech","marrakesh":"Marrakech","fes":"Fès","fez":"Fès",
    "tanger":"Tanger","tangier":"Tanger","agadir":"Agadir","meknes":"Meknès",
    "oujda":"Oujda","kenitra":"Kénitra","tetouan":"Tétouan","sale":"Salé",
    "temara":"Témara","mohammedia":"Mohammedia","el jadida":"El Jadida",
    "beni mellal":"Beni Mellal","nador":"Nador",
}
df["ville"] = df["ville"].str.strip().str.lower().replace(ville_mapping).str.title()

type_mapping = {
    "appartement":"Appartement","app":"Appartement","appart":"Appartement",
    "villa":"Villa","terrain":"Terrain","bureau":"Bureau","duplex":"Duplex",
}
df["type_bien"] = df["type_bien"].str.strip().str.lower().replace(type_mapping).str.capitalize()

transaction_mapping = {
    "vente":"Vente","sale":"Vente","location":"Location","louer":"Location","rent":"Location",
}
df["transaction"] = df["transaction"].str.strip().str.lower().replace(transaction_mapping).str.capitalize()

# ════════════════════════════════════════════════════════════════
# PARTIE 4 — TYPES
# ════════════════════════════════════════════════════════════════

df["date_publication"] = pd.to_datetime(df["date_publication"])

for col in ["prix","surface","nb_chambres","nb_salles_bain","etage","annee_construction"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

for col in ["nb_chambres","nb_salles_bain","etage","annee_construction"]:
    df[col] = df[col].round(0).astype("Int64")

# ════════════════════════════════════════════════════════════════
# PARTIE 5 — FEATURE ENGINEERING
# ════════════════════════════════════════════════════════════════

ANNEE_COURANTE = 2026

df["prix_par_m2"] = (df["prix"] / df["surface"]).round(2)
df["age_estime"]  = (ANNEE_COURANTE - df["annee_construction"]).astype("Int64")

def categoriser_prix(row):
    p = row["prix"]
    if pd.isna(p): return np.nan
    if row["transaction"] == "Vente":
        return ("Économique" if p < 500_000 else "Moyen" if p < 1_500_000
                else "Haut standing" if p < 4_000_000 else "Luxe")
    return ("Économique" if p < 3_000 else "Moyen" if p < 8_000
            else "Haut standing" if p < 20_000 else "Luxe")

df["categorie_prix"] = df.apply(categoriser_prix, axis=1)

df["cat_surface"] = pd.cut(
    df["surface"], bins=[0, 80, 150, 99999],
    labels=["Petit", "Moyen", "Grand"]
).astype(str)

df["annee"]     = df["date_publication"].dt.year
df["mois"]      = df["date_publication"].dt.month
df["trimestre"] = df["date_publication"].dt.quarter

# ════════════════════════════════════════════════════════════════
# SAVE CSV + CLEANED_ANNONCES dans PostgreSQL
# ════════════════════════════════════════════════════════════════

df.to_csv(OUTPUT_CSV, index=False)
print(f"   💾 CSV sauvegardé : {OUTPUT_CSV}")

engine = get_connection()
df["date_publication"] = df["date_publication"].astype(str)

# FIX: Smiyt l-table hiya 'cleaned_annonces' b s-sghor bach tmchi standard f Postgres
with engine.connect() as connection:
    df.to_sql("cleaned_annonces", connection, if_exists="replace", index=False)

print(f"✅ Clean terminé : {len(df)} lignes — shape {df.shape}")