"""
EcoPackAI – Module 2: Data Cleaning & Feature Engineering
==========================================================
Inputs:  materials_cleaned.csv  (600 rows)
         history_cleaned.csv    (15,000 rows)

Outputs:
  • materials_features.csv   – 600 rows + 8 engineered features
  • history_features.csv     – 15,000 rows + 7 engineered features

Engineered features:
  Materials:
    • co2_impact_index          (0–1, higher = greener)
    • cost_efficiency_index     (0–1, higher = better value)
    • material_suitability_score (0–1, weighted composite)
    • sustainability_rank        (1 = best)
    • eco_grade                  (A / B / C / D)

  History:
    • volume_cm3                 (L × W × H)
    • dimensional_weight_ratio   (volumetric / actual)
    • cost_per_km                (USD per km shipped)
    • co2_per_kg                 (CO₂ per kg of product)
    • month                      (1–12)
    • day_of_week                (0=Mon … 6=Sun)
    • category_encoded, shipping_mode_encoded, packaging_used_encoded
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "..", "data")
MAT_IN     = os.path.join(DATA_DIR, "materials_cleaned.csv")
HIST_IN    = os.path.join(DATA_DIR, "history_cleaned.csv")
MAT_OUT    = os.path.join(DATA_DIR, "materials_features.csv")
HIST_OUT   = os.path.join(DATA_DIR, "history_features.csv")

EPS = 1e-6


# ──────────────────────────────────────────────
# 1. Load cleaned data
# ──────────────────────────────────────────────
def load():
    print("\n[1] Loading cleaned datasets...")
    mat  = pd.read_csv(MAT_IN)
    hist = pd.read_csv(HIST_IN, parse_dates=["Date"])
    print(f"  ✔ Materials: {len(mat):,} rows | History: {len(hist):,} rows")
    return mat, hist


# ──────────────────────────────────────────────
# 2. Materials – normalise + encode
# ──────────────────────────────────────────────
def prepare_materials(mat):
    print("\n[2] Normalising and encoding materials...")

    # Binary biodegradable flag
    mat["biodegradable_flag"] = (mat["Biodegradable"] == "Yes").astype(int)

    # Label-encode Category
    le = LabelEncoder()
    mat["category_encoded"] = le.fit_transform(mat["Category"])
    mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    print(f"  Category encoding: {mapping}")

    # MinMax normalise numerics
    scaler = MinMaxScaler()
    num_cols = ["Density_kg_m3", "Tensile_Strength_MPa", "CO2_Emission_kg", "Cost_per_kg"]
    norm_names = [c + "_norm" for c in num_cols]
    mat[norm_names] = scaler.fit_transform(mat[num_cols])
    print(f"  ✔ Normalised: {norm_names}")
    return mat


# ──────────────────────────────────────────────
# 3. Materials – engineer features
# ──────────────────────────────────────────────
def engineer_materials(mat):
    print("\n[3] Engineering material features...")

    # ── CO₂ Impact Index ────────────────────────────────────
    # Lower emission + biodegradable = higher index (greener)
    # Weight: 65% CO₂ inversion | 35% biodegradable flag
    mat["co2_impact_index"] = (
        0.65 * (1 - mat["CO2_Emission_kg_norm"]) +
        0.35 * mat["biodegradable_flag"]
    ).round(4)
    print("  ✔ CO₂ Impact Index  [0=worst … 1=greenest]")

    # ── Cost Efficiency Index ────────────────────────────────
    # High strength + low density at low cost = efficient
    # Performance = avg(tensile_norm, 1-density_norm)
    # CEI = performance / (cost_norm + ε), re-normalised 0–1
    perf = (mat["Tensile_Strength_MPa_norm"] + (1 - mat["Density_kg_m3_norm"])) / 2
    raw  = perf / (mat["Cost_per_kg_norm"] + EPS)
    rmin, rmax = raw.min(), raw.max()
    mat["cost_efficiency_index"] = ((raw - rmin) / (rmax - rmin)).round(4)
    print("  ✔ Cost Efficiency Index  [0=poor value … 1=best value]")

    # ── Material Suitability Score ───────────────────────────
    # Weighted composite for ML ranking
    # CO₂ impact 35% | cost efficiency 25% | strength 20% |
    # low density 10% | biodegradable 10%
    mat["material_suitability_score"] = (
        0.35 * mat["co2_impact_index"] +
        0.25 * mat["cost_efficiency_index"] +
        0.20 * mat["Tensile_Strength_MPa_norm"] +
        0.10 * (1 - mat["Density_kg_m3_norm"]) +
        0.10 * mat["biodegradable_flag"]
    ).round(4)
    print("  ✔ Material Suitability Score  [composite]")

    # ── Rank & Grade ─────────────────────────────────────────
    mat["sustainability_rank"] = (
        mat["material_suitability_score"]
          .rank(ascending=False, method="first")
          .astype(int)
    )

    def grade(s):
        if s >= 0.70: return "A"
        elif s >= 0.50: return "B"
        elif s >= 0.30: return "C"
        else: return "D"

    mat["eco_grade"] = mat["material_suitability_score"].apply(grade)

    print("\n  Eco Grade Distribution:")
    print(mat["eco_grade"].value_counts().sort_index().to_string())
    print("\n  🏆 Top 10 Materials:")
    top10 = mat[["Material_Name", "Category", "material_suitability_score",
                 "eco_grade", "sustainability_rank"]].nsmallest(10, "sustainability_rank")
    print(top10.to_string(index=False))

    return mat


# ──────────────────────────────────────────────
# 4. History – engineer features
# ──────────────────────────────────────────────
def engineer_history(hist):
    print("\n[4] Engineering history features...")

    hist["volume_cm3"]              = hist["L_cm"] * hist["W_cm"] * hist["H_cm"]
    hist["dimensional_weight_ratio"]= (hist["Volumetric_Weight_kg"] / (hist["Weight_kg"] + EPS)).round(4)
    hist["cost_per_km"]             = (hist["Cost_USD"] / (hist["Distance_km"] + EPS)).round(6)
    hist["co2_per_kg"]              = (hist["CO2_Emission_kg"] / (hist["Weight_kg"] + EPS)).round(4)

    # Date features
    hist["month"]       = hist["Date"].dt.month
    hist["day_of_week"] = hist["Date"].dt.dayofweek

    # Encode categoricals (needed for ML in Milestone 2)
    for col in ["Category", "Shipping_Mode", "Packaging_Used"]:
        le = LabelEncoder()
        hist[col + "_encoded"] = le.fit_transform(hist[col].astype(str))

    print("  ✔ volume_cm3, dimensional_weight_ratio, cost_per_km, co2_per_kg")
    print("  ✔ month, day_of_week")
    print("  ✔ Category / Shipping_Mode / Packaging_Used encoded")
    print(f"  ✔ {len(hist):,} history rows engineered")
    return hist


# ──────────────────────────────────────────────
# 5. Validate & save
# ──────────────────────────────────────────────
def validate_and_save(mat, hist):
    print("\n[5] Validating engineered features...")

    # Check no NaN in key features
    mat_key_cols  = ["co2_impact_index", "cost_efficiency_index", "material_suitability_score"]
    hist_key_cols = ["volume_cm3", "co2_per_kg", "cost_per_km"]

    for col in mat_key_cols:
        nan_count = mat[col].isnull().sum()
        if nan_count: print(f"  ⚠  {col}: {nan_count} NaN values")
        else: print(f"  ✔ {col}: no NaN")

    for col in hist_key_cols:
        nan_count = hist[col].isnull().sum()
        if nan_count: print(f"  ⚠  {col}: {nan_count} NaN values")
        else: print(f"  ✔ {col}: no NaN")

    mat.to_csv(MAT_OUT, index=False)
    hist.to_csv(HIST_OUT, index=False)
    print(f"\n  ✔ Saved: {MAT_OUT}")
    print(f"  ✔ Saved: {HIST_OUT}")


# ──────────────────────────────────────────────
# 6. Final summary
# ──────────────────────────────────────────────
def print_summary(mat, hist):
    print("\n" + "=" * 55)
    print("  FEATURE ENGINEERING SUMMARY REPORT")
    print("=" * 55)

    print("\n  Materials – Feature Stats:")
    print(mat[["co2_impact_index", "cost_efficiency_index",
               "material_suitability_score"]].describe().round(4).to_string())

    print("\n  History – Derived Feature Stats:")
    print(hist[["volume_cm3", "co2_per_kg",
                "cost_per_km", "dimensional_weight_ratio"]].describe().round(4).to_string())

    print("\n  Most Common Packaging in Real Orders:")
    print(hist["Packaging_Used"].value_counts().head(8).to_string())

    print("\n  Average CO₂ per kg by Product Category:")
    avg_co2 = hist.groupby("Category")["co2_per_kg"].mean().round(3).sort_values(ascending=False)
    print(avg_co2.to_string())

    print("\n  Average Cost per km by Shipping Mode:")
    avg_cost = hist.groupby("Shipping_Mode")["cost_per_km"].mean().round(6).sort_values(ascending=False)
    print(avg_cost.to_string())


# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  EcoPackAI – Module 2: Data Cleaning & Feature Engineering")
    print("=" * 55)

    mat, hist = load()
    mat  = prepare_materials(mat)
    mat  = engineer_materials(mat)
    hist = engineer_history(hist)
    validate_and_save(mat, hist)
    print_summary(mat, hist)
    print("\n✅ Module 2 complete! Ready for Milestone 2 (ML Models).\n")
