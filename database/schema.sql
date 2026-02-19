-- ============================================================
-- EcoPackAI – PostgreSQL Database Schema
-- Based on real datasets:
--   • materials_database_600.xlsx  (600 materials)
--   • real_packaging_history.xlsx  (15,000 orders)
-- ============================================================

DROP TABLE IF EXISTS material_recommendations CASCADE;
DROP TABLE IF EXISTS engineered_features CASCADE;
DROP TABLE IF EXISTS packaging_history CASCADE;
DROP TABLE IF EXISTS materials CASCADE;

-- ============================================================
-- TABLE 1: materials  (600 rows)
-- ============================================================
CREATE TABLE materials (
    material_id           INTEGER PRIMARY KEY,
    material_name         VARCHAR(150) NOT NULL,
    category              VARCHAR(30) NOT NULL
                          CHECK (category IN ('Eco','Paper','Plastic','Wood','Metal','Glass')),
    density_kg_m3         NUMERIC(10,3) NOT NULL,
    tensile_strength_mpa  NUMERIC(10,3) NOT NULL,
    co2_emission_kg       NUMERIC(10,4) NOT NULL,    -- CO₂ per kg produced
    cost_per_kg           NUMERIC(8,4) NOT NULL,     -- USD per kg
    biodegradable         VARCHAR(3) CHECK (biodegradable IN ('Yes','No')),
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: packaging_history  (15,000 rows)
-- ============================================================
CREATE TABLE packaging_history (
    order_id              INTEGER PRIMARY KEY,
    order_date            DATE NOT NULL,
    item_name             VARCHAR(150),
    category              VARCHAR(50)
                          CHECK (category IN ('Electronics','Clothing','Furniture','Beauty','Home Decor')),
    weight_kg             NUMERIC(8,3) NOT NULL,
    volumetric_weight_kg  NUMERIC(8,3),
    l_cm                  NUMERIC(7,2),
    w_cm                  NUMERIC(7,2),
    h_cm                  NUMERIC(7,2),
    fragility             INTEGER CHECK (fragility BETWEEN 0 AND 10),
    moisture_sens         BOOLEAN DEFAULT FALSE,
    shipping_mode         VARCHAR(10) CHECK (shipping_mode IN ('Air','Road')),
    distance_km           INTEGER NOT NULL,
    packaging_used        VARCHAR(100),
    cost_usd              NUMERIC(8,4),
    co2_emission_kg       NUMERIC(10,4),
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 3: engineered_features  (600 rows – Milestone 1 output)
-- ============================================================
CREATE TABLE engineered_features (
    feature_id                SERIAL PRIMARY KEY,
    material_id               INTEGER REFERENCES materials(material_id),
    co2_impact_index          NUMERIC(8,4),   -- 0=worst, 1=greenest
    cost_efficiency_index     NUMERIC(8,4),   -- 0=poor value, 1=best value
    material_suitability_score NUMERIC(8,4),  -- weighted composite 0–1
    sustainability_rank       INTEGER,         -- 1 = best overall
    eco_grade                 VARCHAR(1) CHECK (eco_grade IN ('A','B','C','D')),
    computed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 4: material_recommendations  (Milestone 2 output)
-- ============================================================
CREATE TABLE material_recommendations (
    recommendation_id   SERIAL PRIMARY KEY,
    order_id            INTEGER REFERENCES packaging_history(order_id),
    material_id         INTEGER REFERENCES materials(material_id),
    rank                INTEGER NOT NULL,
    predicted_cost_usd  NUMERIC(8,4),
    predicted_co2_kg    NUMERIC(8,4),
    confidence_score    NUMERIC(5,4),
    model_version       VARCHAR(20),
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_mat_category         ON materials(category);
CREATE INDEX idx_mat_co2              ON materials(co2_emission_kg ASC);
CREATE INDEX idx_mat_cost             ON materials(cost_per_kg ASC);
CREATE INDEX idx_mat_biodegradable    ON materials(biodegradable);
CREATE INDEX idx_hist_category        ON packaging_history(category);
CREATE INDEX idx_hist_shipping        ON packaging_history(shipping_mode);
CREATE INDEX idx_hist_date            ON packaging_history(order_date);
CREATE INDEX idx_hist_packaging_used  ON packaging_history(packaging_used);
CREATE INDEX idx_feat_material        ON engineered_features(material_id);
CREATE INDEX idx_feat_rank            ON engineered_features(sustainability_rank ASC);
CREATE INDEX idx_rec_order            ON material_recommendations(order_id);

-- ============================================================
-- VIEWS
-- ============================================================

-- Top eco-grade materials with their scores
CREATE VIEW v_top_materials AS
SELECT
    m.material_id,
    m.material_name,
    m.category,
    m.biodegradable,
    m.co2_emission_kg,
    m.cost_per_kg,
    ef.eco_grade,
    ef.material_suitability_score,
    ef.sustainability_rank
FROM materials m
JOIN engineered_features ef ON m.material_id = ef.material_id
ORDER BY ef.sustainability_rank ASC;

-- Average CO₂ and cost per packaging type from real history
CREATE VIEW v_packaging_performance AS
SELECT
    packaging_used,
    COUNT(*)                        AS order_count,
    ROUND(AVG(co2_emission_kg)::numeric, 4) AS avg_co2_kg,
    ROUND(AVG(cost_usd)::numeric, 4)        AS avg_cost_usd,
    ROUND(AVG(weight_kg)::numeric, 3)       AS avg_weight_kg,
    ROUND(AVG(distance_km)::numeric, 0)     AS avg_distance_km
FROM packaging_history
GROUP BY packaging_used
ORDER BY order_count DESC;

-- Category-wise sustainability summary
CREATE VIEW v_category_sustainability AS
SELECT
    h.category,
    COUNT(*)                        AS total_orders,
    ROUND(AVG(h.co2_emission_kg)::numeric, 4) AS avg_co2_per_order,
    ROUND(AVG(h.cost_usd)::numeric, 4)        AS avg_cost_usd,
    ROUND(SUM(h.co2_emission_kg)::numeric, 2) AS total_co2_kg
FROM packaging_history h
GROUP BY h.category
ORDER BY total_co2_kg DESC;

-- Grade distribution
CREATE VIEW v_eco_grade_summary AS
SELECT
    ef.eco_grade,
    COUNT(*)                                           AS material_count,
    ROUND(AVG(ef.material_suitability_score)::numeric, 4) AS avg_score,
    ROUND(AVG(m.co2_emission_kg)::numeric, 4)         AS avg_co2_kg,
    ROUND(AVG(m.cost_per_kg)::numeric, 4)             AS avg_cost_per_kg
FROM engineered_features ef
JOIN materials m ON m.material_id = ef.material_id
GROUP BY ef.eco_grade
ORDER BY ef.eco_grade;

-- ============================================================
-- COMMENTS
-- ============================================================
COMMENT ON TABLE materials IS
  '600 packaging materials with physical, environmental, and cost attributes';
COMMENT ON TABLE packaging_history IS
  '15,000 real shipping orders with actual packaging chosen, cost, and CO₂ impact';
COMMENT ON TABLE engineered_features IS
  'ML-ready engineered features computed from materials table in Module 2';
COMMENT ON TABLE material_recommendations IS
  'AI-generated packaging recommendations per order (populated in Milestone 2)';

COMMENT ON COLUMN materials.co2_emission_kg IS
  'CO₂ emitted during production of 1 kg of this material';
COMMENT ON COLUMN engineered_features.co2_impact_index IS
  '0=highest emitter, 1=greenest. Formula: 0.65×(1−CO₂_norm) + 0.35×biodegradable_flag';
COMMENT ON COLUMN engineered_features.cost_efficiency_index IS
  '0=poor value, 1=best value. Formula: performance/(cost_norm+ε), re-normalised to 0–1';
COMMENT ON COLUMN engineered_features.material_suitability_score IS
  'Weighted composite: 35% CO₂ + 25% cost efficiency + 20% strength + 10% density + 10% biodegradable';
