# data/

This folder holds all datasets for EcoPackAI.

## Required Input Files (you provide these)

| File | Description |
|---|---|
| `materials_database_600.xlsx` | 600 eco-friendly packaging materials with attributes |
| `real_packaging_history.xlsx` | 15,000 real shipping orders with packaging used |

> ⚠️ These files are **not committed to Git** (listed in `.gitignore` due to size).  
> Copy them here before running `setup.sh`.

## Auto-Generated Files (created by pipeline scripts)

| File | Created by | Description |
|---|---|---|
| `materials_cleaned.csv` | `module1_data_collection.py` | Cleaned materials dataset |
| `history_cleaned.csv` | `module1_data_collection.py` | Cleaned history dataset |
| `materials_features.csv` | `module2_feature_engineering.py` | Materials + engineered features |
| `history_features.csv` | `module2_feature_engineering.py` | History + engineered features |
| `data_dictionary.txt` | `module1_data_collection.py` | Column definitions for all tables |

## Column Reference: materials_database_600.xlsx

| Column | Type | Description |
|---|---|---|
| Material_ID | Integer | Unique identifier |
| Material_Name | String | Full material name |
| Category | String | Eco / Paper / Plastic / Wood / Metal / Glass |
| Density_kg_m3 | Float | Density in kg/m³ |
| Tensile_Strength_MPa | Float | Tensile strength in MPa |
| CO2_Emission_kg | Float | CO₂ emitted per kg produced |
| Cost_per_kg | Float | Cost in USD per kg |
| Biodegradable | String | Yes / No |

## Column Reference: real_packaging_history.xlsx

| Column | Type | Description |
|---|---|---|
| Order_ID | Integer | Unique order ID |
| Date | Date | Order date |
| Category | String | Electronics / Clothing / Furniture / Beauty / Home Decor |
| Weight_kg | Float | Product weight |
| L_cm / W_cm / H_cm | Float | Package dimensions |
| Fragility | Integer | Fragility score (1–10) |
| Moisture_Sens | Boolean | Moisture sensitive? |
| Shipping_Mode | String | Air / Road |
| Distance_km | Integer | Shipping distance |
| Packaging_Used | String | Actual packaging material used |
| Cost_USD | Float | Packaging cost incurred |
| CO2_Emission_kg | Float | CO₂ emitted for this shipment |
