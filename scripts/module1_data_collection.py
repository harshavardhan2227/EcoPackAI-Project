"""
EcoPackAI – Module 1: Data Collection & Database Management
============================================================
Uses real datasets:
  • materials_database_600.xlsx  → 600 packaging materials
  • real_packaging_history.xlsx  → 15,000 real shipping orders

This script:
  1. Loads both Excel files
  2. Validates schema and data integrity
  3. Loads into PostgreSQL (optional – falls back to CSV mode)
  4. Exports cleaned CSVs and a data dictionary

Requirements:
    pip install pandas openpyxl psycopg2-binary sqlalchemy python-dotenv
"""

import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(BASE_DIR, "..", "data")
MAT_XLSX     = os.path.join(DATA_DIR, "materials_database_600.xlsx")
HIST_XLSX    = os.path.join(DATA_DIR, "real_packaging_history.xlsx")
MAT_CLEAN    = os.path.join(DATA_DIR, "materials_cleaned.csv")
HIST_CLEAN   = os.path.join(DATA_DIR, "history_cleaned.csv")

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER','postgres')}:"
    f"{os.getenv('DB_PASSWORD','password')}@"
    f"{os.getenv('DB_HOST','localhost')}:"
    f"{os.getenv('DB_PORT','5432')}/"
    f"{os.getenv('DB_NAME','ecopackai')}"
)


# ──────────────────────────────────────────────
# 1. Load Excel files
# ──────────────────────────────────────────────
def load_datasets():
    print("\n[1] Loading real datasets...")
    mat  = pd.read_excel(MAT_XLSX)
    hist = pd.read_excel(HIST_XLSX)
    mat.columns  = [c.strip() for c in mat.columns]
    hist.columns = [c.strip() for c in hist.columns]
    print(f"  ✔ Materials:  {len(mat):,} rows × {mat.shape[1]} columns")
    print(f"  ✔ History:    {len(hist):,} rows × {hist.shape[1]} columns")
    return mat, hist


# ──────────────────────────────────────────────
# 2. Validate & Clean
# ──────────────────────────────────────────────
def validate_and_clean(mat, hist):
    print("\n[2] Validating and cleaning...")

    # Missing values
    mat_miss  = mat.isnull().sum().sum()
    hist_miss = hist.isnull().sum().sum()
    print(f"  Missing – Materials: {mat_miss} | History: {hist_miss}")

    # Duplicates
    mat.drop_duplicates(subset=["Material_ID"], keep="first", inplace=True)
    hist.drop_duplicates(subset=["Order_ID"], keep="first", inplace=True)
    print(f"  Unique materials: {len(mat):,} | Unique orders: {len(hist):,}")

    # Clip negatives
    for col in ["CO2_Emission_kg", "Cost_per_kg", "Tensile_Strength_MPa", "Density_kg_m3"]:
        mat[col] = mat[col].clip(lower=0)
    for col in ["Cost_USD", "CO2_Emission_kg", "Weight_kg", "Distance_km"]:
        hist[col] = hist[col].clip(lower=0)

    # Parse dates
    hist["Date"] = pd.to_datetime(hist["Date"], errors="coerce")

    print("  ✔ Cleaning complete")
    return mat, hist


# ──────────────────────────────────────────────
# 3. Save Cleaned CSVs
# ──────────────────────────────────────────────
def save_cleaned(mat, hist):
    print("\n[3] Saving cleaned datasets...")
    mat.to_csv(MAT_CLEAN, index=False)
    hist.to_csv(HIST_CLEAN, index=False)
    print(f"  ✔ {MAT_CLEAN}")
    print(f"  ✔ {HIST_CLEAN}")


# ──────────────────────────────────────────────
# 4. Load into PostgreSQL (optional)
# ──────────────────────────────────────────────
def load_to_postgres(mat, hist):
    print("\n[4] Loading into PostgreSQL...")
    try:
        from sqlalchemy import create_engine
        engine = create_engine(DB_URL)
        mat.to_sql("materials",         engine, if_exists="replace", index=False, chunksize=200)
        hist.to_sql("packaging_history", engine, if_exists="replace", index=False, chunksize=500)
        print(f"  ✔ Loaded {len(mat):,} materials and {len(hist):,} history rows")
    except Exception as e:
        print(f"  ⚠  DB skipped (offline mode): {e}")


# ──────────────────────────────────────────────
# 5. Print Summary & Data Dictionary
# ──────────────────────────────────────────────
def summarize(mat, hist):
    print("\n[5] Summary Statistics")
    print("\n── Materials ──")
    print(mat[["Density_kg_m3", "Tensile_Strength_MPa",
               "CO2_Emission_kg", "Cost_per_kg"]].describe().round(3).to_string())
    print("\n  Category Distribution:")
    print(mat["Category"].value_counts().to_string())
    print("\n  Biodegradable Split:")
    print(mat["Biodegradable"].value_counts().to_string())

    print("\n── Packaging History ──")
    print(hist[["Cost_USD", "CO2_Emission_kg",
                "Weight_kg", "Distance_km"]].describe().round(3).to_string())
    print("\n  Product Category Distribution:")
    print(hist["Category"].value_counts().to_string())
    print("\n  Top Packaging Materials Used:")
    print(hist["Packaging_Used"].value_counts().head(10).to_string())

    # Data dictionary
    schema = {
        "materials": {
            "Material_ID":           "INTEGER – Unique material identifier",
            "Material_Name":         "VARCHAR – Name of packaging material",
            "Category":              "VARCHAR – Eco / Paper / Plastic / Wood / Metal / Glass",
            "Density_kg_m3":         "NUMERIC – Material density in kg/m³",
            "Tensile_Strength_MPa":  "NUMERIC – Tensile strength in megapascals",
            "CO2_Emission_kg":       "NUMERIC – CO₂ emitted per kg of material produced",
            "Cost_per_kg":           "NUMERIC – Cost in USD per kilogram",
            "Biodegradable":         "VARCHAR – Yes / No",
        },
        "packaging_history": {
            "Order_ID":              "INTEGER – Unique order identifier",
            "Date":                  "DATE – Order date",
            "Item_Name":             "VARCHAR – Product name",
            "Category":              "VARCHAR – Electronics / Clothing / Furniture / Beauty / Home Decor",
            "Weight_kg":             "NUMERIC – Actual product weight in kg",
            "Volumetric_Weight_kg":  "NUMERIC – Calculated volumetric weight",
            "L_cm / W_cm / H_cm":   "NUMERIC – Package dimensions in cm",
            "Fragility":             "INTEGER – Fragility score (scale)",
            "Moisture_Sens":         "BOOLEAN – Moisture sensitive flag",
            "Shipping_Mode":         "VARCHAR – Air / Road",
            "Distance_km":           "INTEGER – Shipping distance in km",
            "Packaging_Used":        "VARCHAR – Actual packaging material used",
            "Cost_USD":              "NUMERIC – Packaging cost in USD",
            "CO2_Emission_kg":       "NUMERIC – CO₂ emitted for shipment",
        }
    }
    dict_path = os.path.join(DATA_DIR, "data_dictionary.txt")
    with open(dict_path, "w", encoding="utf-8") as f:

        for tbl, cols in schema.items():
            f.write(f"\nTABLE: {tbl}\n{'='*55}\n")
            for col, desc in cols.items():
                f.write(f"  {col:<30} {desc}\n")
    print(f"\n  ✔ Data dictionary → {dict_path}")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  EcoPackAI – Module 1: Data Collection & Management")
    print("=" * 55)
    mat, hist = load_datasets()
    mat, hist = validate_and_clean(mat, hist)
    save_cleaned(mat, hist)
    load_to_postgres(mat, hist)
    summarize(mat, hist)
    print("\n✅ Module 1 complete!\n")
