"""
EcoPackAI – Module 3 & 4: ML Models + Recommendation Engine
============================================================
Trains:
  1. Random Forest Regressor   → Cost Prediction
  2. Random Forest Regressor   → CO₂ Prediction
  3. Random Forest Classifier  → Packaging Type Recommendation

Outputs:
  models/rf_cost.pkl, rf_co2.pkl, rf_pkg.pkl
  models/le_pkg.pkl, le_cat.pkl, le_ship.pkl
  models/metrics.json
  outputs/model_evaluation_report.txt
"""

import os, json, pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (mean_squared_error, mean_absolute_error,
                             r2_score, accuracy_score, classification_report)
from sklearn.preprocessing import LabelEncoder

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE, '..', 'data')
MODEL_DIR  = os.path.join(BASE, '..', 'models')
OUT_DIR    = os.path.join(BASE, '..', 'outputs')
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

FEATURES = ['Weight_kg','Volumetric_Weight_kg','Distance_km','Fragility',
            'Moisture_Sens','volume_cm3','dimensional_weight_ratio',
            'Category_encoded','Shipping_Mode_encoded','month']

def load():
    print("\n[1] Loading engineered features...")
    hist = pd.read_csv(os.path.join(DATA_DIR, 'history_features.csv'))
    hist['Moisture_Sens'] = hist['Moisture_Sens'].astype(int)
    print(f"  ✔ History rows: {len(hist):,}")
    return hist

def train_models(hist):
    X = hist[FEATURES].copy()

    print("\n[2] Training Random Forest – Cost Prediction...")
    y_cost = hist['Cost_USD']
    X_tr, X_te, yc_tr, yc_te = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    rf_cost = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    rf_cost.fit(X_tr, yc_tr)
    yc_pred = rf_cost.predict(X_te)
    cost_metrics = {
        'rmse': float(np.sqrt(mean_squared_error(yc_te, yc_pred))),
        'mae':  float(mean_absolute_error(yc_te, yc_pred)),
        'r2':   float(r2_score(yc_te, yc_pred))
    }
    print(f"  RMSE={cost_metrics['rmse']:.4f} | MAE={cost_metrics['mae']:.4f} | R²={cost_metrics['r2']:.4f}")

    print("\n[3] Training Random Forest – CO₂ Prediction...")
    y_co2 = hist['CO2_Emission_kg']
    X_tr2, X_te2, yco_tr, yco_te = train_test_split(X, y_co2, test_size=0.2, random_state=42)
    rf_co2 = RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    rf_co2.fit(X_tr2, yco_tr)
    yco_pred = rf_co2.predict(X_te2)
    co2_metrics = {
        'rmse': float(np.sqrt(mean_squared_error(yco_te, yco_pred))),
        'mae':  float(mean_absolute_error(yco_te, yco_pred)),
        'r2':   float(r2_score(yco_te, yco_pred))
    }
    print(f"  RMSE={co2_metrics['rmse']:.4f} | MAE={co2_metrics['mae']:.4f} | R²={co2_metrics['r2']:.4f}")

    print("\n[4] Training RF Classifier – Packaging Recommendation...")
    le_pkg  = LabelEncoder(); hist['Packaging_Used_encoded'] = le_pkg.fit_transform(hist['Packaging_Used'])
    le_cat  = LabelEncoder(); hist['Category_encoded'] = le_cat.fit_transform(hist['Category'])
    le_ship = LabelEncoder(); hist['Shipping_Mode_encoded'] = le_ship.fit_transform(hist['Shipping_Mode'])
    y_pkg = hist['Packaging_Used_encoded']
    X_tr3, X_te3, yp_tr, yp_te = train_test_split(X, y_pkg, test_size=0.2, random_state=42)
    rf_pkg = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
    rf_pkg.fit(X_tr3, yp_tr)
    yp_pred = rf_pkg.predict(X_te3)
    pkg_acc = float(accuracy_score(yp_te, yp_pred))
    print(f"  Accuracy: {pkg_acc:.4f} ({pkg_acc*100:.1f}%)")

    # Save models
    for name, obj in [('rf_cost.pkl',rf_cost),('rf_co2.pkl',rf_co2),('rf_pkg.pkl',rf_pkg),
                       ('le_pkg.pkl',le_pkg),('le_cat.pkl',le_cat),('le_ship.pkl',le_ship)]:
        with open(os.path.join(MODEL_DIR, name), 'wb') as f:
            pickle.dump(obj, f)

    metrics = {
        'cost_model': cost_metrics, 'co2_model': co2_metrics,
        'pkg_classifier': {'accuracy': pkg_acc},
        'features': FEATURES,
        'packaging_classes': list(le_pkg.classes_),
        'category_classes': list(le_cat.classes_),
        'shipping_classes': list(le_ship.classes_),
    }
    with open(os.path.join(MODEL_DIR, 'metrics.json'), 'w', encoding='utf-8') as f:

        json.dump(metrics, f, indent=2)

    # Feature importances
    fi = sorted(zip(FEATURES, rf_cost.feature_importances_), key=lambda x: -x[1])
    print("\n  Feature Importances (Cost Model):")
    for feat, imp in fi:
        bar = '█' * int(imp * 40)
        print(f"    {feat:<30} {bar} {imp:.4f}")

    # Save evaluation report
    report = [
        "EcoPackAI – ML Model Evaluation Report",
        "=" * 55,
        "",
        "COST PREDICTION MODEL (Random Forest Regressor)",
        f"  Training samples : {len(X_tr):,}",
        f"  Test samples     : {len(X_te):,}",
        f"  RMSE             : {cost_metrics['rmse']:.4f}",
        f"  MAE              : {cost_metrics['mae']:.4f}",
        f"  R² Score         : {cost_metrics['r2']:.4f}",
        "",
        "CO₂ PREDICTION MODEL (Random Forest Regressor)",
        f"  Training samples : {len(X_tr2):,}",
        f"  Test samples     : {len(X_te2):,}",
        f"  RMSE             : {co2_metrics['rmse']:.4f}",
        f"  MAE              : {co2_metrics['mae']:.4f}",
        f"  R² Score         : {co2_metrics['r2']:.4f}",
        "",
        "PACKAGING CLASSIFIER (Random Forest Classifier)",
        f"  Training samples : {len(X_tr3):,}",
        f"  Test samples     : {len(X_te3):,}",
        f"  Accuracy         : {pkg_acc:.4f} ({pkg_acc*100:.1f}%)",
        "",
        "PACKAGING CLASSES:",
        *[f"  [{i}] {c}" for i, c in enumerate(le_pkg.classes_)],
        "",
        classification_report(yp_te, yp_pred, target_names=le_pkg.classes_),
    ]
    with open(os.path.join(OUT_DIR, 'model_evaluation_report.txt'), 'w', encoding='utf-8') as f:

        f.write('\n'.join(report))
    print(f"\n  ✔ Evaluation report saved")
    print("\n✅ Module 3 & 4 complete!\n")

if __name__ == '__main__':
    print("=" * 55)
    print("  EcoPackAI – Module 3 & 4: ML Training")
    print("=" * 55)
    hist = load()
    train_models(hist)
