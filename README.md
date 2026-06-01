# 🏗️ DARKOM.MA — Data Warehouse & Tableaux de Bord Power BI

> Projet décisionnel complet : nettoyage des données, pipeline ETL, entrepôt de données et tableaux de bord analytiques Power BI pour la plateforme **Darkom.ma**.

---

## 📌 Table des matières

- [À propos du projet](#-à-propos-du-projet)
- [Architecture générale](#-architecture-générale)
- [Structure du projet](#-structure-du-projet)
- [Pipeline ETL](#-pipeline-etl)
- [Tableaux de bord Power BI](#-tableaux-de-bord-power-bi)
- [Technologies utilisées](#-technologies-utilisées)
- [Installation et exécution](#-installation-et-exécution)
- [Auteur(s)](#-auteurs)

---

## 🧭 À propos du projet

Ce projet réalise une chaîne **Business Intelligence complète** pour **Darkom.ma** :

- Extraction et nettoyage des données d'annonces immobilières
- Construction d'un **Data Warehouse** structuré
- Automatisation via un **pipeline ETL** Python
- Visualisation analytique avec **Power BI**

---

## 🏛️ Architecture générale

```
┌─────────────────────────────────┐
│     SOURCE : darkom-annonces    │
│        (CSV brut)               │
└────────────────┬────────────────┘
                 │
         ┌───────▼────────┐
         │   clean.py     │  ← Nettoyage & préparation
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │   staging.py   │  ← Zone de staging
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │  warehouse.py  │  ← Chargement Data Warehouse
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │  Power BI      │  ← Tableaux de bord
         │ (.pbix)        │
         └────────────────┘
```

---

## 📁 Structure du projet

```
📦 DARKOM.MA/
├── 📂 darkom power bi/
│   ├── Capture d'écran 2026-06-01 (1).png   # Aperçu dashboard
│   ├── Capture d'écran 2026-06-01 (2).png
│   ├── Capture d'écran 2026-06-01 (3).png
│   ├── Capture d'écran 2026-06-01 (4).png
│   └── darkom_power_pi (1).pbix              # Fichier Power BI principal
│
├── 📂 Data/
│   ├── darkom_cleaned.csv                    # Données nettoyées (output clean.py)
│   └── darkom-annonces-6a0a532a164...        # Données brutes sources
│
├── 📂 scripts/
│   ├── __pycache__/
│   ├── clean.py                              # Nettoyage des données
│   ├── db_connect.py                         # Connexion base de données
│   ├── staging.py                            # Chargement zone staging
│   └── warehouse.py                          # Alimentation Data Warehouse
│
├── .env                                      # Variables d'environnement (DB, credentials)
├── .gitignore
├── requirements.txt                          # Dépendances Python
├── run_pipeline.py                           # Orchestrateur ETL principal
└── test.ipynb                                # Notebook d'exploration / tests
```

---

## ⚙️ Pipeline ETL

Le pipeline est orchestré par `run_pipeline.py` et s'appuie sur 4 scripts modulaires :

### `clean.py` — Nettoyage
- Suppression des doublons et valeurs nulles
- Normalisation des types (prix, superficie, localisation)
- Standardisation des libellés (villes, types de bien)
- Export vers `Data/darkom_cleaned.csv`

### `db_connect.py` — Connexion DB
- Gestion centralisée de la connexion (PostgreSQL / SQLite)
- Lecture des paramètres depuis `.env`

### `staging.py` — Zone de Staging
- Chargement des données nettoyées dans la zone intermédiaire
- Contrôles de qualité avant intégration dans le DW

### `warehouse.py` — Data Warehouse
- Alimentation des tables de faits et de dimensions
- Gestion des mises à jour incrémentales

### Exécution

```bash
# Lancer le pipeline complet
python run_pipeline.py

# Tester / Explorer les données
jupyter notebook test.ipynb
```

---

## 📊 Tableaux de bord Power BI

Le fichier `darkom power bi/darkom_power_pi (1).pbix` contient les dashboards suivants :

| Dashboard | Indicateurs |
|---|---|
| 🏠 **Vue générale** | Nombre d'annonces, prix moyen, superficie moyenne |
| 🗺️ **Analyse géographique** | Répartition par ville / région |
| 💰 **Analyse des prix** | Distribution des prix, évolution, prix/m² |
| 🏢 **Types de biens** | Appartements, villas, terrains, commerces |
| 📅 **Tendances temporelles** | Évolution des annonces dans le temps |

---

## 🛠️ Technologies utilisées

| Catégorie | Outil |
|---|---|
| **Langage** | Python 3.x |
| **Data Processing** | Pandas, NumPy |
| **Base de données** | PostgreSQL / SQLite |
| **ORM / Connexion** | SQLAlchemy |
| **Visualisation** | Power BI Desktop |
| **Exploration** | Jupyter Notebook |
| **Versioning** | Git / GitHub |

---

## 🚀 Installation et exécution

### Prérequis

- Python 3.8+
- Power BI Desktop (Windows)
- PostgreSQL (optionnel, selon config)

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/elarabilamiaa43-wq/Conception-d-un-Data-Warehouse-et-Tableaux-.git
cd Conception-d-un-Data-Warehouse-et-Tableaux-

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env : renseigner DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# 5. Lancer le pipeline ETL complet
python run_pipeline.py

# 6. Ouvrir le tableau de bord
# → Ouvrir "darkom power bi/darkom_power_pi (1).pbix" dans Power BI Desktop
```

### Variables `.env` requises

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=darkom_dw
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## 👤 Auteur(s)

**El Arabi Lamiaa**
- GitHub : [@elarabilamiaa43-wq](https://github.com/elarabilamiaa43-wq)

---

## 📄 Licence

Projet académique — Tous droits réservés © 2026.

---

> 💡 *"Without data, you're just another person with an opinion."* — W. Edwards Deming
