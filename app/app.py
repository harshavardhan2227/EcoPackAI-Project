"""
EcoPackAI – Flask Backend API
==============================
Endpoints:
  GET  /                     → Main UI
  GET  /dashboard            → BI Dashboard
  POST /api/recommend        → AI packaging recommendation
  GET  /api/materials        → Full material catalog (filterable)
  GET  /api/stats            → KPI metrics for dashboard
  GET  /api/top_materials    → Top eco-graded materials
  GET  /api/packaging_usage  → Historical packaging usage
  GET  /api/co2_trend        → Monthly CO₂ time series
  GET  /api/cost_trend       → Monthly cost time series
  GET  /api/category_stats   → Per-category sustainability stats
  GET  /api/shipping_stats   → Air vs Road comparison
  GET  /health               → Health check
"""

import os, sys, json, pickle
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from datetime import datetime

# Path resolution - works locally AND on Render/Heroku
APP_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR  = os.path.dirname(APP_DIR)
MODEL_DIR = os.path.join(ROOT_DIR, 'models')
DATA_DIR  = os.path.join(ROOT_DIR, 'data')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'ecopackai-dev-key-change-in-prod')

def _load(filename):
    with open(os.path.join(MODEL_DIR, filename), 'rb') as f:
        return pickle.load(f)

try:
    rf_cost = _load('rf_cost.pkl')
    rf_co2  = _load('rf_co2.pkl')
    rf_pkg  = _load('rf_pkg.pkl')
    le_pkg  = _load('le_pkg.pkl')
    le_cat  = _load('le_cat.pkl')
    le_ship = _load('le_ship.pkl')
    with open(os.path.join(MODEL_DIR, 'metrics.json')) as f:
        metrics = json.load(f)
    mat  = pd.read_csv(os.path.join(DATA_DIR, 'materials_features.csv'))
    hist = pd.read_csv(os.path.join(DATA_DIR, 'history_features.csv'), parse_dates=['Date'])
    MODELS_LOADED = True
    print("EcoPackAI: models loaded OK")
except Exception as e:
    MODELS_LOADED = False
    print(f"EcoPackAI: models not loaded - {e}")
    rf_cost = rf_co2 = rf_pkg = le_pkg = le_cat = le_ship = None
    metrics = {'features':[],'packaging_classes':[],'category_classes':[],
               'shipping_classes':[],'cost_model':{'r2':0},'co2_model':{'r2':0},'pkg_classifier':{'accuracy':0}}
    mat = pd.DataFrame()
    hist = pd.DataFrame()

def build_features(data):
    cat_enc  = int(le_cat.transform([data['category']])[0])
    ship_enc = int(le_ship.transform([data['shipping_mode']])[0])
    weight = float(data['weight_kg'])
    vol = float(data.get('length_cm',30)) * float(data.get('width_cm',20)) * float(data.get('height_cm',15))
    vol_wt = round(vol / 5000.0, 3)
    return pd.DataFrame([{
        'Weight_kg': weight, 'Volumetric_Weight_kg': vol_wt,
        'Distance_km': float(data['distance_km']),
        'Fragility': int(data.get('fragility', 5)),
        'Moisture_Sens': int(data.get('moisture_sensitive', 0)),
        'volume_cm3': vol,
        'dimensional_weight_ratio': round(vol_wt / (weight + 1e-6), 4),
        'Category_encoded': cat_enc,
        'Shipping_Mode_encoded': ship_enc,
        'month': datetime.now().month,
    }])

@app.route('/')
def index():
    return render_template('index.html',
        categories=metrics.get('category_classes', []),
        packaging_classes=metrics.get('packaging_classes', []))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    if not MODELS_LOADED:
        return jsonify({'success': False, 'error': 'Models not loaded. Run module3_ml_training.py first.'}), 503
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON body'}), 400
        for field in ['category', 'shipping_mode', 'weight_kg', 'distance_km']:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing: {field}'}), 400
        X = build_features(data)
        pred_cost = float(rf_cost.predict(X)[0])
        pred_co2  = float(rf_co2.predict(X)[0])
        pkg_probs = rf_pkg.predict_proba(X)[0]
        recs = []
        for rank, idx in enumerate(pkg_probs.argsort()[-5:][::-1], 1):
            pkg_name = le_pkg.classes_[idx]
            kw = pkg_name.split('(')[0].strip().lower()[:10]
            mm = mat[mat['Material_Name'].str.lower().str.contains(kw, na=False)] if not mat.empty else pd.DataFrame()
            if len(mm):
                b = mm.nsmallest(1,'sustainability_rank').iloc[0]
                g, s, ci, ce = str(b['eco_grade']), float(b['material_suitability_score']), float(b['co2_impact_index']), float(b['cost_efficiency_index'])
            else:
                g, s, ci, ce = 'B', 0.5, 0.6, 0.5
            recs.append({'rank': rank, 'packaging': pkg_name, 'confidence': round(float(pkg_probs[idx])*100,1),
                         'eco_grade': g, 'suitability_score': round(s,3), 'co2_impact_index': round(ci,3), 'cost_efficiency_index': round(ce,3)})
        max_co2 = float(hist['CO2_Emission_kg'].quantile(0.9)) if not hist.empty else 100
        return jsonify({'success': True, 'predicted_cost_usd': round(pred_cost,2), 'predicted_co2_kg': round(pred_co2,3),
                        'co2_saving_pct': max(0, round((1-pred_co2/max(max_co2,1))*100,1)),
                        'recommendations': recs,
                        'model_metrics': {'cost_r2': round(metrics['cost_model']['r2'],4),
                                          'co2_r2': round(metrics['co2_model']['r2'],4),
                                          'pkg_accuracy': round(metrics['pkg_classifier']['accuracy'],4)}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/materials')
def get_materials():
    if mat.empty: return jsonify([])
    df = mat.copy()
    cat = request.args.get('category','')
    grade = request.args.get('grade','')
    limit = int(request.args.get('limit',50))
    if cat: df = df[df['Category']==cat]
    if grade: df = df[df['eco_grade']==grade]
    cols = ['Material_ID','Material_Name','Category','Biodegradable','CO2_Emission_kg','Cost_per_kg','eco_grade','material_suitability_score','sustainability_rank']
    return jsonify(df.nsmallest(limit,'sustainability_rank')[cols].to_dict(orient='records'))

@app.route('/api/stats')
def get_stats():
    if hist.empty or mat.empty: return jsonify({'error':'Data not loaded'}), 503
    bio = int(mat[mat['Biodegradable']=='Yes'].shape[0])
    pkg_co2 = hist.groupby('Packaging_Used')['CO2_Emission_kg'].mean()
    saving = round((float(pkg_co2.max())-float(pkg_co2.min()))/max(float(pkg_co2.max()),1)*100,1)
    return jsonify({'total_orders':len(hist),'total_co2_kg':round(float(hist['CO2_Emission_kg'].sum()),1),
                    'avg_cost_usd':round(float(hist['Cost_USD'].mean()),2),'total_materials':len(mat),
                    'biodegradable_count':bio,'biodegradable_pct':round(bio/len(mat)*100,1),
                    'grade_a_materials':int(mat[mat['eco_grade']=='A'].shape[0]),
                    'potential_co2_saving_pct':saving,
                    'model_accuracy_pct':round(metrics['pkg_classifier']['accuracy']*100,1)})

@app.route('/api/top_materials')
def top_materials():
    if mat.empty: return jsonify([])
    n = int(request.args.get('n',15))
    cols = ['Material_Name','Category','Biodegradable','CO2_Emission_kg','Cost_per_kg','eco_grade','material_suitability_score','sustainability_rank']
    return jsonify(mat.nsmallest(n,'sustainability_rank')[cols].to_dict(orient='records'))

@app.route('/api/packaging_usage')
def packaging_usage():
    if hist.empty: return jsonify([])
    u = hist.groupby('Packaging_Used').agg(order_count=('Order_ID','count'),avg_co2=('CO2_Emission_kg','mean'),
        avg_cost=('Cost_USD','mean'),total_co2=('CO2_Emission_kg','sum')).reset_index().sort_values('order_count',ascending=False).round(3)
    return jsonify(u.to_dict(orient='records'))

@app.route('/api/co2_trend')
def co2_trend():
    if hist.empty: return jsonify([])
    t = hist.copy(); t['month_year'] = t['Date'].dt.to_period('M').astype(str)
    m = t.groupby('month_year').agg(total_co2=('CO2_Emission_kg','sum'),avg_co2=('CO2_Emission_kg','mean'),
        order_count=('Order_ID','count')).reset_index().sort_values('month_year').round(3)
    return jsonify(m.to_dict(orient='records'))

@app.route('/api/cost_trend')
def cost_trend():
    if hist.empty: return jsonify([])
    t = hist.copy(); t['month_year'] = t['Date'].dt.to_period('M').astype(str)
    m = t.groupby('month_year').agg(total_cost=('Cost_USD','sum'),avg_cost=('Cost_USD','mean'),
        order_count=('Order_ID','count')).reset_index().sort_values('month_year').round(3)
    return jsonify(m.to_dict(orient='records'))

@app.route('/api/category_stats')
def category_stats():
    if hist.empty: return jsonify([])
    s = hist.groupby('Category').agg(total_orders=('Order_ID','count'),avg_co2=('CO2_Emission_kg','mean'),
        avg_cost=('Cost_USD','mean'),total_co2=('CO2_Emission_kg','sum'),
        avg_weight=('Weight_kg','mean'),avg_distance=('Distance_km','mean')).reset_index().sort_values('total_co2',ascending=False).round(3)
    return jsonify(s.to_dict(orient='records'))

@app.route('/api/shipping_stats')
def shipping_stats():
    if hist.empty: return jsonify([])
    s = hist.groupby('Shipping_Mode').agg(total_orders=('Order_ID','count'),avg_co2=('CO2_Emission_kg','mean'),
        avg_cost=('Cost_USD','mean'),total_co2=('CO2_Emission_kg','sum')).reset_index().round(3)
    return jsonify(s.to_dict(orient='records'))

@app.route('/health')
def health():
    return jsonify({'status':'ok','models_loaded':MODELS_LOADED,'materials_count':len(mat),'history_count':len(hist)})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_ENV','development')=='development', host='0.0.0.0', port=port)
