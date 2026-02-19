"""
EcoPackAI – Module 7: Business Intelligence Dashboard (Static Export)
=====================================================================
Generates static BI charts and exports sustainability reports to:
  • outputs/chart_*.png           (7 charts)
  • outputs/sustainability_report.csv  (summary data)

Run this script to regenerate all charts and reports.
Charts are also served live via the Flask /dashboard route.

Requirements: matplotlib, pandas, numpy
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import pickle, csv, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE, '..', 'data')
MODEL_DIR = os.path.join(BASE, '..', 'models')
OUT_DIR   = os.path.join(BASE, '..', 'outputs')
os.makedirs(OUT_DIR, exist_ok=True)

FOREST = '#0f4c35'; MOSS = '#1a7a52'; SAGE = '#4ba57a'; LIME = '#a8e063'
COLORS = ['#0f4c35','#1a7a52','#4ba57a','#a8e063','#6bb88a','#2d9b67','#38a169','#c8f08a','#84cc82','#b7eb8f']

plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True,
                     'grid.alpha': 0.3, 'grid.color': '#cccccc'})


def load_data():
    print("\n[1] Loading data...")
    hist = pd.read_csv(os.path.join(DATA_DIR, 'history_features.csv'), parse_dates=['Date'])
    mat  = pd.read_csv(os.path.join(DATA_DIR, 'materials_features.csv'))
    print(f"  ✔ History: {len(hist):,} | Materials: {len(mat):,}")
    return hist, mat


def chart_co2_trend(hist):
    hist['month_year'] = hist['Date'].dt.to_period('M')
    monthly = hist.groupby('month_year')['CO2_Emission_kg'].agg(['sum','mean']).reset_index()
    monthly['month_str'] = monthly['month_year'].astype(str)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.fill_between(range(len(monthly)), monthly['sum'], alpha=0.15, color=MOSS)
    ax.plot(range(len(monthly)), monthly['sum'], color=MOSS, lw=2.5, label='Total CO₂ (kg)')
    ax2 = ax.twinx()
    ax2.plot(range(len(monthly)), monthly['mean'], color=LIME, lw=2, ls='--', label='Avg CO₂/order')
    ax2.spines['top'].set_visible(False)
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly['month_str'], rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Total CO₂ (kg)', color=MOSS)
    ax2.set_ylabel('Avg CO₂/order (kg)', color=LIME)
    ax.set_title('Monthly CO₂ Emissions Trend', fontsize=14, fontweight='bold', color=FOREST, pad=15)
    lines1, _ = ax.get_legend_handles_labels()
    lines2, _ = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, ['Total CO₂','Avg CO₂/order'], loc='upper left', fontsize=9)
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_co2_trend.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_co2_trend.png")


def chart_packaging_usage(hist):
    pkg_counts = hist['Packaging_Used'].value_counts()
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        pkg_counts.values, labels=None, autopct='%1.1f%%', startangle=90,
        colors=COLORS[:len(pkg_counts)], pctdistance=0.75,
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'}, textprops={'fontsize': 9}
    )
    for at in autotexts: at.set_color('white'); at.set_fontweight('bold')
    ax.add_patch(plt.Circle((0,0), 0.55, fc='white'))
    ax.text(0, 0.05, '15,000', ha='center', va='center', fontsize=20, fontweight='bold', color=FOREST)
    ax.text(0, -0.15, 'orders', ha='center', va='center', fontsize=11, color='#6b7280')
    ax.legend(wedges, pkg_counts.index, title='Packaging Type', loc='lower center',
              bbox_to_anchor=(0.5,-0.12), ncol=2, fontsize=9, title_fontsize=9)
    ax.set_title('Packaging Material Usage Distribution', fontsize=14, fontweight='bold', color=FOREST, pad=15)
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_packaging_usage.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_packaging_usage.png")


def chart_category_co2(hist):
    cat_co2 = hist.groupby('Category')['CO2_Emission_kg'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(cat_co2.index, cat_co2.values, color=COLORS[:len(cat_co2)], edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, cat_co2.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{val:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold', color=FOREST)
    ax.set_title('Average CO₂ Emission by Product Category', fontsize=14, fontweight='bold', color=FOREST, pad=15)
    ax.set_ylabel('Avg CO₂ (kg per order)'); ax.set_xlabel('Product Category')
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_category_co2.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_category_co2.png")


def chart_shipping_comparison(hist):
    ship = hist.groupby('Shipping_Mode').agg(avg_co2=('CO2_Emission_kg','mean'), avg_cost=('Cost_USD','mean')).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, col, title, colors in [
        (axes[0], 'avg_co2', 'Avg CO₂ per Order (kg)', ['#ef4444','#3b82f6']),
        (axes[1], 'avg_cost', 'Avg Packaging Cost ($)',  ['#fca5a5','#93c5fd'])
    ]:
        bars = ax.bar(ship['Shipping_Mode'], ship[col], color=colors, edgecolor='white', linewidth=1.5, width=0.5)
        for bar, val in zip(bars, ship[col]):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2, f'{val:.2f}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', color=FOREST, pad=10)
    fig.suptitle('Air vs Road: Environmental & Cost Impact', fontsize=14, fontweight='bold', color=FOREST, y=1.02)
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_shipping_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_shipping_comparison.png")


def chart_eco_grades(mat):
    grade_counts = mat['eco_grade'].value_counts().sort_index()
    grade_colors = {'A':'#22c55e','B':'#3b82f6','C':'#f59e0b','D':'#ef4444'}
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(grade_counts.index, grade_counts.values,
                  color=[grade_colors[g] for g in grade_counts.index], edgecolor='white', linewidth=2, width=0.55)
    for bar, val in zip(bars, grade_counts.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2, str(val),
                ha='center', va='bottom', fontsize=13, fontweight='bold')
    ax.set_title('Material Eco Grade Distribution (600 Materials)', fontsize=14, fontweight='bold', color=FOREST, pad=15)
    ax.set_xlabel('Eco Grade'); ax.set_ylabel('Number of Materials')
    labels = ['A: Excellent\n(≥0.70)','B: Good\n(0.50–0.69)','C: Average\n(0.30–0.49)','D: Poor\n(<0.30)']
    patches = [mpatches.Patch(color=grade_colors[g], label=l) for g, l in zip('ABCD', labels)]
    ax.legend(handles=patches, fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_eco_grades.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_eco_grades.png")


def chart_material_scatter(mat):
    top15 = mat.nsmallest(15, 'sustainability_rank')
    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(top15['co2_impact_index'], top15['cost_efficiency_index'],
                    s=top15['material_suitability_score']*500+50,
                    c=top15['material_suitability_score'], cmap='YlGn', alpha=0.8, edgecolors=FOREST, lw=1.5)
    for _, row in top15.iterrows():
        ax.annotate(row['Material_Name'][:22], (row['co2_impact_index'], row['cost_efficiency_index']),
                    textcoords='offset points', xytext=(6,4), fontsize=7.5, color=FOREST)
    plt.colorbar(sc, ax=ax, label='Suitability Score', shrink=0.8)
    ax.set_xlabel('CO₂ Impact Index (higher = greener)')
    ax.set_ylabel('Cost Efficiency Index (higher = better value)')
    ax.set_title('Top Materials: CO₂ vs Cost Efficiency', fontsize=13, fontweight='bold', color=FOREST, pad=12)
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_material_scatter.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_material_scatter.png")


def chart_feature_importance():
    with open(os.path.join(MODEL_DIR, 'rf_cost.pkl'), 'rb') as f:
        rf_cost = pickle.load(f)
    FEATURES = ['Weight_kg','Volumetric_Weight_kg','Distance_km','Fragility',
                'Moisture_Sens','volume_cm3','dimensional_weight_ratio',
                'Category_encoded','Shipping_Mode_encoded','month']
    importances = rf_cost.feature_importances_
    sorted_idx = np.argsort(importances)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([FEATURES[i] for i in sorted_idx], importances[sorted_idx],
            color=[COLORS[i % len(COLORS)] for i in range(len(sorted_idx))], edgecolor='white')
    for i, (idx, val) in enumerate(zip(sorted_idx, importances[sorted_idx])):
        ax.text(val+0.002, i, f'{val:.3f}', va='center', fontsize=8.5, fontweight='bold', color=FOREST)
    ax.set_xlabel('Feature Importance')
    ax.set_title('Random Forest Feature Importances (Cost Model)', fontsize=13, fontweight='bold', color=FOREST, pad=12)
    fig.tight_layout()
    fig.savefig(f'{OUT_DIR}/chart_feature_importance.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  ✔ chart_feature_importance.png")


def export_sustainability_report(hist, mat):
    print("\n[3] Exporting sustainability report CSV...")
    cat_stats = hist.groupby('Category').agg(
        total_orders=('Order_ID','count'),
        total_co2_kg=('CO2_Emission_kg','sum'),
        avg_co2_kg=('CO2_Emission_kg','mean'),
        avg_cost_usd=('Cost_USD','mean'),
        avg_weight_kg=('Weight_kg','mean'),
        avg_distance_km=('Distance_km','mean'),
    ).reset_index().round(3)
    cat_stats.to_csv(f'{OUT_DIR}/sustainability_report.csv', index=False)
    print(f"  ✔ sustainability_report.csv saved ({len(cat_stats)} rows)")

    pkg_stats = hist.groupby('Packaging_Used').agg(
        order_count=('Order_ID','count'),
        total_co2_kg=('CO2_Emission_kg','sum'),
        avg_co2_kg=('CO2_Emission_kg','mean'),
        avg_cost_usd=('Cost_USD','mean'),
    ).reset_index().sort_values('order_count', ascending=False).round(3)
    pkg_stats.to_csv(f'{OUT_DIR}/packaging_performance_report.csv', index=False)
    print(f"  ✔ packaging_performance_report.csv saved")

    top_mats = mat.nsmallest(50, 'sustainability_rank')[
        ['Material_ID','Material_Name','Category','Biodegradable','CO2_Emission_kg',
         'Cost_per_kg','eco_grade','material_suitability_score','sustainability_rank']
    ]
    top_mats.to_csv(f'{OUT_DIR}/top_materials_report.csv', index=False)
    print(f"  ✔ top_materials_report.csv saved (top 50)")


if __name__ == '__main__':
    print("=" * 55)
    print("  EcoPackAI – Module 7: BI Dashboard Charts")
    print("=" * 55)
    hist, mat = load_data()
    print("\n[2] Generating charts...")
    chart_co2_trend(hist)
    chart_packaging_usage(hist)
    chart_category_co2(hist)
    chart_shipping_comparison(hist)
    chart_eco_grades(mat)
    chart_material_scatter(mat)
    chart_feature_importance()
    export_sustainability_report(hist, mat)
    print(f"\n✅ Module 7 complete! All outputs in: {OUT_DIR}\n")
