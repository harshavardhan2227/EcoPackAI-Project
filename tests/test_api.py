"""
EcoPackAI – API Tests
=====================
Run with: pytest tests/test_api.py -v

Tests all Flask endpoints to ensure correct status codes and response structure.
Models must be trained (models/*.pkl) before running tests.
"""

import sys, os, json
import pytest

# Make sure the app module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

try:
    from app import app as flask_app
    MODELS_AVAILABLE = True
except Exception as e:
    MODELS_AVAILABLE = False
    print(f"Warning: Could not load app — {e}")


@pytest.fixture
def client():
    if not MODELS_AVAILABLE:
        pytest.skip("Models not available — run module3_ml_training.py first")
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


# ── GET endpoints ─────────────────────────────────────────

def test_index(client):
    """Main UI returns 200"""
    res = client.get('/')
    assert res.status_code == 200
    assert b'EcoPackAI' in res.data


def test_dashboard(client):
    """Dashboard returns 200"""
    res = client.get('/dashboard')
    assert res.status_code == 200


def test_api_stats(client):
    """Stats endpoint returns correct JSON keys"""
    res = client.get('/api/stats')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'total_orders' in data
    assert 'total_co2_kg' in data
    assert 'total_materials' in data
    assert data['total_orders'] == 15000
    assert data['total_materials'] == 600


def test_api_materials(client):
    """Materials endpoint returns list of materials"""
    res = client.get('/api/materials?limit=10')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert isinstance(data, list)
    assert len(data) <= 10
    assert 'Material_Name' in data[0]
    assert 'eco_grade' in data[0]


def test_api_materials_filter_category(client):
    """Materials endpoint supports category filter"""
    res = client.get('/api/materials?category=Eco&limit=5')
    assert res.status_code == 200
    data = json.loads(res.data)
    for item in data:
        assert item['Category'] == 'Eco'


def test_api_materials_filter_grade(client):
    """Materials endpoint supports grade filter"""
    res = client.get('/api/materials?grade=B&limit=10')
    assert res.status_code == 200
    data = json.loads(res.data)
    for item in data:
        assert item['eco_grade'] == 'B'


def test_api_top_materials(client):
    """Top materials returns ranked list"""
    res = client.get('/api/top_materials?n=5')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) == 5
    ranks = [d['sustainability_rank'] for d in data]
    assert ranks == sorted(ranks)  # Must be ascending


def test_api_packaging_usage(client):
    """Packaging usage returns 10 entries"""
    res = client.get('/api/packaging_usage')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) == 10
    assert 'Packaging_Used' in data[0]
    assert 'order_count' in data[0]


def test_api_co2_trend(client):
    """CO₂ trend returns monthly time series"""
    res = client.get('/api/co2_trend')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) > 0
    assert 'month_year' in data[0]
    assert 'total_co2' in data[0]


def test_api_category_stats(client):
    """Category stats returns 5 categories"""
    res = client.get('/api/category_stats')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) == 5
    categories = [d['Category'] for d in data]
    assert 'Electronics' in categories
    assert 'Furniture' in categories


def test_api_shipping_stats(client):
    """Shipping stats returns Air and Road"""
    res = client.get('/api/shipping_stats')
    assert res.status_code == 200
    data = json.loads(res.data)
    modes = [d['Shipping_Mode'] for d in data]
    assert 'Air' in modes
    assert 'Road' in modes


# ── POST recommend endpoint ───────────────────────────────

VALID_PAYLOAD = {
    "category": "Electronics",
    "shipping_mode": "Air",
    "weight_kg": 1.5,
    "distance_km": 1200,
    "length_cm": 30,
    "width_cm": 20,
    "height_cm": 15,
    "fragility": 8,
    "moisture_sensitive": 1
}


def test_api_recommend_success(client):
    """Recommend returns valid prediction structure"""
    res = client.post('/api/recommend',
                      data=json.dumps(VALID_PAYLOAD),
                      content_type='application/json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True
    assert 'predicted_cost_usd' in data
    assert 'predicted_co2_kg' in data
    assert 'recommendations' in data
    assert len(data['recommendations']) == 5


def test_api_recommend_recommendation_structure(client):
    """Each recommendation has required fields"""
    res = client.post('/api/recommend',
                      data=json.dumps(VALID_PAYLOAD),
                      content_type='application/json')
    data = json.loads(res.data)
    for rec in data['recommendations']:
        assert 'rank' in rec
        assert 'packaging' in rec
        assert 'confidence' in rec
        assert 'eco_grade' in rec
        assert rec['eco_grade'] in ['A', 'B', 'C', 'D']


def test_api_recommend_ranks_ordered(client):
    """Recommendations are ordered by rank"""
    res = client.post('/api/recommend',
                      data=json.dumps(VALID_PAYLOAD),
                      content_type='application/json')
    data = json.loads(res.data)
    ranks = [r['rank'] for r in data['recommendations']]
    assert ranks == [1, 2, 3, 4, 5]


def test_api_recommend_road_shipping(client):
    """Works with Road shipping mode"""
    payload = {**VALID_PAYLOAD, "shipping_mode": "Road", "category": "Furniture"}
    res = client.post('/api/recommend',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True


def test_api_recommend_missing_field(client):
    """Returns error when required field missing"""
    payload = {"category": "Electronics"}  # Missing most fields
    res = client.post('/api/recommend',
                      data=json.dumps(payload),
                      content_type='application/json')
    data = json.loads(res.data)
    assert data['success'] is False
    assert 'error' in data


def test_api_recommend_invalid_category(client):
    """Returns error for unknown category"""
    payload = {**VALID_PAYLOAD, "category": "UnknownCategory"}
    res = client.post('/api/recommend',
                      data=json.dumps(payload),
                      content_type='application/json')
    data = json.loads(res.data)
    assert data['success'] is False


def test_api_recommend_predictions_in_range(client):
    """Predicted values are positive"""
    res = client.post('/api/recommend',
                      data=json.dumps(VALID_PAYLOAD),
                      content_type='application/json')
    data = json.loads(res.data)
    assert data['predicted_cost_usd'] > 0
    assert data['predicted_co2_kg'] >= 0
    assert 0 <= data['co2_saving_pct'] <= 100


def test_api_recommend_model_metrics(client):
    """Response includes model quality metrics"""
    res = client.post('/api/recommend',
                      data=json.dumps(VALID_PAYLOAD),
                      content_type='application/json')
    data = json.loads(res.data)
    assert 'model_metrics' in data
    assert data['model_metrics']['cost_r2'] > 0.99
    assert data['model_metrics']['co2_r2'] > 0.99
    assert data['model_metrics']['pkg_accuracy'] > 0.90
