-- ============================================================
-- Crab Monitoring System — PostgreSQL Schema
-- ERD: species_database ─< crabs >─ health_records
--                                  >─ detection_logs
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ── Enums ─────────────────────────────────────────────────────────────────────

CREATE TYPE species_enum AS ENUM (
    'Kepiting Bakau',
    'Kepiting Rajungan',
    'Kepiting Lumpur',
    'Kepiting Batu',
    'Unknown'
);

CREATE TYPE gender_enum AS ENUM (
    'Jantan',
    'Betina',
    'Unknown'
);

CREATE TYPE health_status_enum AS ENUM (
    'Sehat',
    'Kurang Sehat',
    'Sakit',
    'Mati',
    'Unknown'
);

-- ── Species Database ──────────────────────────────────────────────────────────

CREATE TABLE species_database (
    id                      SERIAL PRIMARY KEY,
    species_name            VARCHAR(100) UNIQUE NOT NULL,
    scientific_name         VARCHAR(150),
    family                  VARCHAR(100),
    habitat                 TEXT,
    characteristics         TEXT,
    morphology              TEXT,
    growth_pattern          TEXT,
    common_diseases         TEXT,
    average_weight_min_g    FLOAT,
    average_weight_max_g    FLOAT,
    average_length_min_cm   FLOAT,
    average_length_max_cm   FLOAT,
    distribution            TEXT,
    source_url              VARCHAR(500),
    reference_images        JSONB,
    additional_data         JSONB,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ
);

COMMENT ON TABLE species_database IS 'Database referensi spesies kepiting dari web scraping';
COMMENT ON COLUMN species_database.additional_data IS 'Data tambahan dari berbagai sumber (GBIF, FAO, WoRMS)';

-- Trigger untuk update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_species_updated_at
    BEFORE UPDATE ON species_database
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Crabs (Main Table) ────────────────────────────────────────────────────────

CREATE TABLE crabs (
    id                      SERIAL PRIMARY KEY,
    timestamp               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Species Classification
    species                 species_enum NOT NULL DEFAULT 'Unknown',
    species_confidence      FLOAT NOT NULL DEFAULT 0.0 CHECK (species_confidence BETWEEN 0 AND 100),
    species_database_id     INTEGER REFERENCES species_database(id) ON DELETE SET NULL,
    
    -- Gender
    gender                  gender_enum NOT NULL DEFAULT 'Unknown',
    gender_confidence       FLOAT NOT NULL DEFAULT 0.0 CHECK (gender_confidence BETWEEN 0 AND 100),
    
    -- Health
    health_status           health_status_enum NOT NULL DEFAULT 'Unknown',
    health_confidence       FLOAT NOT NULL DEFAULT 0.0 CHECK (health_confidence BETWEEN 0 AND 100),
    
    -- Physical Measurements
    weight_g                FLOAT CHECK (weight_g > 0),
    length_cm               FLOAT CHECK (length_cm > 0),
    width_cm                FLOAT CHECK (width_cm > 0),
    
    -- Body Parts Completeness
    left_claw               BOOLEAN NOT NULL DEFAULT TRUE,
    right_claw              BOOLEAN NOT NULL DEFAULT TRUE,
    legs_complete           BOOLEAN NOT NULL DEFAULT TRUE,
    shell_damage            BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Detection
    detection_confidence    FLOAT NOT NULL DEFAULT 0.0 CHECK (detection_confidence BETWEEN 0 AND 1),
    
    -- Images
    image_cam1              VARCHAR(500),
    image_cam2              VARCHAR(500),
    
    -- Bounding Box
    bbox_x1                 FLOAT,
    bbox_y1                 FLOAT,
    bbox_x2                 FLOAT,
    bbox_y2                 FLOAT,
    
    -- Tracking
    track_id                INTEGER,
    session_id              VARCHAR(50),
    
    -- Additional
    raw_analysis            JSONB,
    notes                   TEXT
);

COMMENT ON TABLE crabs IS 'Data utama kepiting hasil deteksi AI';
COMMENT ON COLUMN crabs.raw_analysis IS 'Output lengkap AI pipeline dalam JSON';

-- Indexes
CREATE INDEX idx_crabs_timestamp ON crabs(timestamp DESC);
CREATE INDEX idx_crabs_species ON crabs(species);
CREATE INDEX idx_crabs_gender ON crabs(gender);
CREATE INDEX idx_crabs_health ON crabs(health_status);
CREATE INDEX idx_crabs_session ON crabs(session_id);
CREATE INDEX idx_crabs_track ON crabs(track_id);
CREATE INDEX idx_crabs_timestamp_species ON crabs(timestamp, species);
CREATE INDEX idx_crabs_timestamp_health ON crabs(timestamp, health_status);

-- ── Health Records ────────────────────────────────────────────────────────────

CREATE TABLE health_records (
    id                  SERIAL PRIMARY KEY,
    crab_id             INTEGER NOT NULL REFERENCES crabs(id) ON DELETE CASCADE,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    health_status       health_status_enum NOT NULL,
    health_confidence   FLOAT DEFAULT 0.0,
    
    -- Observations
    shell_color         VARCHAR(50),
    shell_condition     VARCHAR(100),
    body_condition      VARCHAR(100),
    
    -- Measurements
    weight_g            FLOAT,
    length_cm           FLOAT,
    width_cm            FLOAT,
    
    -- Diagnosis
    diagnosis           TEXT,
    treatment_notes     TEXT,
    
    -- Image
    image_path          VARCHAR(500),
    
    -- Analysis
    analysis_data       JSONB
);

COMMENT ON TABLE health_records IS 'Riwayat pemantauan kesehatan kepiting';

CREATE INDEX idx_health_records_crab_id ON health_records(crab_id);
CREATE INDEX idx_health_records_timestamp ON health_records(timestamp DESC);

-- ── Detection Logs ────────────────────────────────────────────────────────────

CREATE TABLE detection_logs (
    id                          SERIAL PRIMARY KEY,
    crab_id                     INTEGER REFERENCES crabs(id) ON DELETE SET NULL,
    timestamp                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    camera_id                   SMALLINT NOT NULL CHECK (camera_id IN (1, 2)),
    frame_number                INTEGER,
    session_id                  VARCHAR(50),
    
    detection_confidence        FLOAT,
    bbox_raw                    JSONB,
    
    inference_time_ms           FLOAT,
    total_processing_time_ms    FLOAT,
    
    status                      VARCHAR(50) DEFAULT 'success',
    error_message               TEXT,
    frame_image_path            VARCHAR(500)
);

COMMENT ON TABLE detection_logs IS 'Log setiap frame deteksi untuk audit dan performa monitoring';

CREATE INDEX idx_detection_logs_crab_id ON detection_logs(crab_id);
CREATE INDEX idx_detection_logs_session ON detection_logs(session_id);
CREATE INDEX idx_detection_logs_timestamp ON detection_logs(timestamp DESC);
CREATE INDEX idx_detection_logs_camera_session ON detection_logs(camera_id, session_id);

-- ── Scraping Logs ─────────────────────────────────────────────────────────────

CREATE TABLE scraping_logs (
    id                  SERIAL PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source              VARCHAR(200),
    url                 VARCHAR(500),
    status              VARCHAR(50),
    records_scraped     INTEGER DEFAULT 0,
    error_message       TEXT,
    duration_seconds    FLOAT
);

-- ── Useful Views ──────────────────────────────────────────────────────────────

-- Dashboard summary view
CREATE VIEW v_dashboard_stats AS
SELECT
    COUNT(*)                                                    AS total_crabs,
    COUNT(*) FILTER (WHERE gender = 'Jantan')                   AS male_count,
    COUNT(*) FILTER (WHERE gender = 'Betina')                   AS female_count,
    COUNT(*) FILTER (WHERE health_status = 'Sehat')             AS healthy_count,
    COUNT(*) FILTER (WHERE health_status IN ('Sakit', 'Mati'))  AS sick_count,
    COUNT(*) FILTER (WHERE DATE(timestamp) = CURRENT_DATE)      AS today_count,
    ROUND(AVG(weight_g)::numeric, 1)                            AS avg_weight_g,
    ROUND(AVG(length_cm)::numeric, 1)                           AS avg_length_cm,
    ROUND(AVG(width_cm)::numeric, 1)                            AS avg_width_cm
FROM crabs;

COMMENT ON VIEW v_dashboard_stats IS 'Ringkasan statistik untuk dashboard utama';

-- Species distribution view
CREATE VIEW v_species_distribution AS
SELECT
    species,
    COUNT(*) AS count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 1) AS percentage
FROM crabs
GROUP BY species
ORDER BY count DESC;

-- Daily detection trend view
CREATE VIEW v_daily_trend AS
SELECT
    DATE(timestamp)         AS date,
    COUNT(*)                AS total,
    ROUND(AVG(weight_g)::numeric, 1)    AS avg_weight,
    ROUND(AVG(length_cm)::numeric, 1)   AS avg_length
FROM crabs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date;

-- ── Seed Data — Species Reference ─────────────────────────────────────────────

INSERT INTO species_database (
    species_name, scientific_name, family, habitat, characteristics,
    average_weight_min_g, average_weight_max_g,
    average_length_min_cm, average_length_max_cm, distribution
) VALUES
(
    'Kepiting Bakau', 'Scylla serrata', 'Portunidae',
    'Hutan mangrove, estuari, dan perairan payau di sepanjang pesisir tropis dan subtropis.',
    'Cangkang keras berwarna hijau kecoklatan hingga coklat tua. Capit besar dan kuat. Dua duri tajam di setiap sisi cangkang. Abdomen betina lebih lebar dan bulat.',
    100, 1200, 8, 20,
    'Indo-Pasifik Barat: Asia Tenggara, India, Afrika Timur, Australia Utara'
),
(
    'Kepiting Rajungan', 'Portunus pelagicus', 'Portunidae',
    'Perairan laut dangkal berpasir, padang lamun, dan terumbu karang.',
    'Cangkang biru kehijauan dengan bintik-bintik putih. Kaki belakang berbentuk dayung untuk berenang. Jantan berwarna biru cerah, betina lebih kehijauan.',
    50, 400, 6, 18,
    'Indo-Pasifik: Jepang, Australia, India, Afrika Timur, Laut Merah'
),
(
    'Kepiting Lumpur', 'Scylla olivacea', 'Portunidae',
    'Lumpur estuari, tambak, dan kawasan mangrove bersubstrat lunak.',
    'Cangkang lebih kecil dari S. serrata, warna coklat kemerahan hingga zaitun. Habitat di substrat berlumpur. Toleran terhadap salinitas rendah.',
    80, 600, 6, 15,
    'Asia Tenggara: Indonesia, Malaysia, Filipina, Thailand, Vietnam'
),
(
    'Kepiting Batu', 'Charybdis feriata', 'Portunidae',
    'Dasar berbatu dan berkarang di perairan laut dangkal hingga sedang.',
    'Cangkang keras dengan pola garis-garis khas. Warna coklat atau merah bata dengan bintik-bintik. Capit kuat untuk memecah moluska. Hidup di substrat keras.',
    100, 800, 7, 17,
    'Indo-Pasifik: Asia Tenggara, India, Laut Merah, Afrika Timur, Jepang'
)
ON CONFLICT (species_name) DO NOTHING;
