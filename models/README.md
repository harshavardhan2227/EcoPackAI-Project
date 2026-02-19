# models/

This folder holds all trained ML model artifacts.

## Files

| File | Type | Description |
|---|---|---|
| `rf_cost.pkl` | RandomForestRegressor | Predicts packaging cost in USD |
| `rf_co2.pkl` | RandomForestRegressor | Predicts CO₂ emissions in kg |
| `rf_pkg.pkl` | RandomForestClassifier | Recommends packaging type (10 classes) |
| `le_cat.pkl` | LabelEncoder | Encodes product category |
| `le_ship.pkl` | LabelEncoder | Encodes shipping mode |
| `le_pkg.pkl` | LabelEncoder | Encodes packaging type (target) |
| `metrics.json` | JSON | Model evaluation metrics + class lists |

## Model Performance

| Model | Metric | Value |
|---|---|---|
| Cost (Random Forest) | R² | 1.0000 |
| Cost (Random Forest) | RMSE | 0.0671 |
| CO₂ (Random Forest) | R² | 0.9990 |
| CO₂ (Random Forest) | RMSE | 2.1348 |
| Packaging Classifier | Accuracy | 95.03% |

## Regenerating Models

```bash
python scripts/module3_ml_training.py
```

## Git LFS (Large File Storage)

If you want to commit the `.pkl` files to GitHub:
```bash
# Install Git LFS
git lfs install
git lfs track "*.pkl"
git add .gitattributes
git add models/
git commit -m "Add trained models via LFS"
```
