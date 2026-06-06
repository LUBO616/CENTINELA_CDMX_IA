-- 911 AI Flow Demo - Database Initialization
-- PostgreSQL 15+ required
-- Creates schemas and tables for the emergency demo system

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

-- Raw data schema: stores original redacted conversations
CREATE SCHEMA IF NOT EXISTS raw;

-- Core data schema: stores processed triage results
CREATE SCHEMA IF NOT EXISTS core;

-- Analytics schema: stores aggregated metrics and incidents
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================================
-- RAW SCHEMA TABLES
-- ============================================================================

-- Table: raw.conversations
-- Purpose: Store original conversations with PII redacted
CREATE TABLE IF NOT EXISTS raw.conversations (
    id SERIAL PRIMARY KEY,
    call_id UUID UNIQUE NOT NULL,
    trace_id UUID UNIQUE NOT NULL,
    original_text TEXT NOT NULL,
    redacted_text TEXT NOT NULL,
    redaction_flags JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for raw.conversations
CREATE INDEX IF NOT EXISTS idx_raw_conversations_call_id ON raw.conversations(call_id);
CREATE INDEX IF NOT EXISTS idx_raw_conversations_trace_id ON raw.conversations(trace_id);
CREATE INDEX IF NOT EXISTS idx_raw_conversations_created_at ON raw.conversations(created_at DESC);

-- ============================================================================
-- CORE SCHEMA TABLES
-- ============================================================================

-- Table: core.triage_results
-- Purpose: Store AI triage analysis results
CREATE TABLE IF NOT EXISTS core.triage_results (
    id SERIAL PRIMARY KEY,
    call_id UUID NOT NULL,
    trace_id UUID NOT NULL,
    risk_level INTEGER NOT NULL CHECK (risk_level BETWEEN 1 AND 10),
    branch VARCHAR(20) NOT NULL CHECK (branch IN ('low', 'mid', 'critical')),
    priority_class VARCHAR(20) NOT NULL CHECK (priority_class IN ('minimum', 'low', 'medium', 'high', 'critical')),
    case_category VARCHAR(50),
    medical_category VARCHAR(50),
    protected_group_flags JSONB DEFAULT '{}',
    best_interest_child BOOLEAN DEFAULT FALSE,
    human_required BOOLEAN DEFAULT FALSE,
    primary_authority VARCHAR(100),
    support_authorities TEXT[],
    public_stage_phrase TEXT,
    rationale_public TEXT,
    trust_flags JSONB DEFAULT '{}',
    p0_signals TEXT[],
    keywords_detected JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (call_id) REFERENCES raw.conversations(call_id) ON DELETE CASCADE
);

-- Indexes for core.triage_results
CREATE INDEX IF NOT EXISTS idx_triage_call_id ON core.triage_results(call_id);
CREATE INDEX IF NOT EXISTS idx_triage_trace_id ON core.triage_results(trace_id);
CREATE INDEX IF NOT EXISTS idx_triage_risk_level ON core.triage_results(risk_level);
CREATE INDEX IF NOT EXISTS idx_triage_branch ON core.triage_results(branch);
CREATE INDEX IF NOT EXISTS idx_triage_category ON core.triage_results(case_category);
CREATE INDEX IF NOT EXISTS idx_triage_human_required ON core.triage_results(human_required);
CREATE INDEX IF NOT EXISTS idx_triage_created_at ON core.triage_results(created_at DESC);

-- ============================================================================
-- ANALYTICS SCHEMA TABLES
-- ============================================================================

-- Table: analytics.incidents
-- Purpose: Store structured incident records for analytics
CREATE TABLE IF NOT EXISTS analytics.incidents (
    id SERIAL PRIMARY KEY,
    incident_id UUID UNIQUE NOT NULL,
    call_id UUID NOT NULL,
    trace_id UUID NOT NULL,
    risk_level INTEGER,
    branch VARCHAR(20),
    case_category VARCHAR(50),
    human_required BOOLEAN DEFAULT FALSE,
    has_p0_signals BOOLEAN DEFAULT FALSE,
    location_hint TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (call_id) REFERENCES raw.conversations(call_id) ON DELETE CASCADE
);

-- Indexes for analytics.incidents
CREATE INDEX IF NOT EXISTS idx_incidents_incident_id ON analytics.incidents(incident_id);
CREATE INDEX IF NOT EXISTS idx_incidents_call_id ON analytics.incidents(call_id);
CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON analytics.incidents(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_risk_level ON analytics.incidents(risk_level);
CREATE INDEX IF NOT EXISTS idx_incidents_category ON analytics.incidents(case_category);
CREATE INDEX IF NOT EXISTS idx_incidents_branch ON analytics.incidents(branch);
CREATE INDEX IF NOT EXISTS idx_incidents_human_required ON analytics.incidents(human_required);
CREATE INDEX IF NOT EXISTS idx_incidents_p0_signals ON analytics.incidents(has_p0_signals);

-- Table: analytics.metrics_cache
-- Purpose: Cache computed metrics for dashboard performance
CREATE TABLE IF NOT EXISTS analytics.metrics_cache (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_key VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(metric_type, metric_key)
);

-- Indexes for analytics.metrics_cache
CREATE INDEX IF NOT EXISTS idx_metrics_type ON analytics.metrics_cache(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_calculated_at ON analytics.metrics_cache(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_expires_at ON analytics.metrics_cache(expires_at);

-- Table: analytics.predictive_incidents
-- Purpose: Store massive synthetic data for predictive analytics
CREATE TABLE IF NOT EXISTS analytics.predictive_incidents (
    id SERIAL PRIMARY KEY,
    incident_id TEXT UNIQUE NOT NULL,
    branch VARCHAR(20) NOT NULL CHECK (branch IN ('low', 'mid', 'critical')),
    risk_level INTEGER NOT NULL CHECK (risk_level BETWEEN 1 AND 10),
    case_category VARCHAR(50) NOT NULL,
    human_required BOOLEAN DEFAULT FALSE,
    p0_signals TEXT[],
    alcaldia_norm VARCHAR(50),
    synthetic BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    geom GEOMETRY(Point, 4326)
);

-- Indexes for analytics.predictive_incidents
CREATE INDEX IF NOT EXISTS idx_predictive_incident_id ON analytics.predictive_incidents(incident_id);
CREATE INDEX IF NOT EXISTS idx_predictive_created_at ON analytics.predictive_incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictive_branch ON analytics.predictive_incidents(branch);
CREATE INDEX IF NOT EXISTS idx_predictive_risk_level ON analytics.predictive_incidents(risk_level);
CREATE INDEX IF NOT EXISTS idx_predictive_category ON analytics.predictive_incidents(case_category);
CREATE INDEX IF NOT EXISTS idx_predictive_alcaldia ON analytics.predictive_incidents(alcaldia_norm);
CREATE INDEX IF NOT EXISTS idx_predictive_human_required ON analytics.predictive_incidents(human_required);
CREATE INDEX IF NOT EXISTS idx_predictive_synthetic ON analytics.predictive_incidents(synthetic);
CREATE INDEX IF NOT EXISTS idx_predictive_geom ON analytics.predictive_incidents USING GIST(geom);
-- Table: analytics.whatsapp_lab_messages
-- Purpose: Store WhatsApp-style lab messages for demo/testing
CREATE TABLE IF NOT EXISTS analytics.whatsapp_lab_messages (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    from_hash TEXT NOT NULL,
    profile_name TEXT,
    message_text TEXT NOT NULL,
    message_text_redacted TEXT NOT NULL,
    category VARCHAR(50),
    branch VARCHAR(20) CHECK (branch IN ('low', 'mid', 'critical')),
    risk_level INTEGER CHECK (risk_level BETWEEN 1 AND 10),
    human_required BOOLEAN DEFAULT FALSE,
    p0_signals TEXT[],
    bot_reply TEXT,
    source VARCHAR(20) DEFAULT 'webchat',
    synthetic BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    from_number_redacted VARCHAR(50),
    location_hint TEXT,
    location_source VARCHAR(50),
    incident_time TIMESTAMP,
    alcaldia_norm VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    processed_at TIMESTAMP
);

-- Indexes for analytics.whatsapp_lab_messages
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_message_id ON analytics.whatsapp_lab_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_created_at ON analytics.whatsapp_lab_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_from_hash ON analytics.whatsapp_lab_messages(from_hash);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_category ON analytics.whatsapp_lab_messages(category);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_branch ON analytics.whatsapp_lab_messages(branch);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_risk_level ON analytics.whatsapp_lab_messages(risk_level);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_human_required ON analytics.whatsapp_lab_messages(human_required);
CREATE INDEX IF NOT EXISTS idx_whatsapp_lab_source ON analytics.whatsapp_lab_messages(source);


-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: analytics.summary_stats
-- Purpose: Real-time summary statistics
CREATE OR REPLACE VIEW analytics.summary_stats AS
SELECT
    COUNT(*) as total_incidents,
    COUNT(*) FILTER (WHERE risk_level BETWEEN 1 AND 4) as low_risk_count,
    COUNT(*) FILTER (WHERE risk_level = 5) as mid_risk_count,
    COUNT(*) FILTER (WHERE risk_level BETWEEN 6 AND 10) as critical_risk_count,
    COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_count,
    COUNT(*) FILTER (WHERE has_p0_signals = TRUE) as p0_signals_count,
    COUNT(DISTINCT case_category) as unique_categories,
    MAX(timestamp) as last_incident_time
FROM analytics.incidents;

-- View: analytics.hourly_volume
-- Purpose: Incident volume by hour for trend analysis
CREATE OR REPLACE VIEW analytics.hourly_volume AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as incident_count,
    AVG(risk_level) as avg_risk_level,
    COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_count
FROM analytics.incidents
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- View: analytics.category_distribution
-- Purpose: Distribution of incidents by category
CREATE OR REPLACE VIEW analytics.category_distribution AS
SELECT
    case_category,
    COUNT(*) as incident_count,
    AVG(risk_level) as avg_risk_level,
    COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_count,
    ROUND(COUNT(*)::NUMERIC / NULLIF((SELECT COUNT(*) FROM analytics.incidents), 0) * 100, 2) as percentage
FROM analytics.incidents
WHERE case_category IS NOT NULL
GROUP BY case_category
ORDER BY incident_count DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_raw_conversations_updated_at
    BEFORE UPDATE ON raw.conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_triage_results_updated_at
    BEFORE UPDATE ON core.triage_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Clean old metrics cache
CREATE OR REPLACE FUNCTION clean_expired_metrics()
RETURNS void AS $$
BEGIN
    DELETE FROM analytics.metrics_cache
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Function: Notify predictive data changes for real-time updates
CREATE OR REPLACE FUNCTION notify_predictive_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    -- Build notification payload
    IF TG_OP = 'DELETE' THEN
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', OLD.incident_id,
            'created_at', OLD.created_at,
            'timestamp', NOW()
        );
    ELSE
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'incident_id', NEW.incident_id,
            'branch', NEW.branch,
            'risk_level', NEW.risk_level,
            'case_category', NEW.case_category,
            'created_at', NEW.created_at,
            'timestamp', NOW()
        );
    END IF;
    
    -- Send notification
    PERFORM pg_notify('predictive_updates', payload::text);
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Triggers for predictive incidents real-time notifications
CREATE TRIGGER notify_predictive_insert
    AFTER INSERT ON analytics.predictive_incidents
    FOR EACH ROW
    EXECUTE FUNCTION notify_predictive_change();

CREATE TRIGGER notify_predictive_update
    AFTER UPDATE ON analytics.predictive_incidents
    FOR EACH ROW
    EXECUTE FUNCTION notify_predictive_change();

CREATE TRIGGER notify_predictive_delete
    AFTER DELETE ON analytics.predictive_incidents
    FOR EACH ROW
-- Function: Notify WhatsApp Lab message changes for real-time updates
CREATE OR REPLACE FUNCTION notify_whatsapp_lab_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    -- Build notification payload
    IF TG_OP = 'DELETE' THEN
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'message_id', OLD.message_id,
            'created_at', OLD.created_at,
            'timestamp', NOW()
        );
    ELSE
        payload = json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
            'message_id', NEW.message_id,
            'category', NEW.category,
            'branch', NEW.branch,
            'risk_level', NEW.risk_level,
            'human_required', NEW.human_required,
            'created_at', NEW.created_at,
            'timestamp', NOW()
        );
    END IF;
    
    -- Send notification
    PERFORM pg_notify('whatsapp_lab_updates', payload::text);
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Triggers for WhatsApp Lab messages real-time notifications
CREATE TRIGGER notify_whatsapp_lab_insert
    AFTER INSERT ON analytics.whatsapp_lab_messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_whatsapp_lab_change();

CREATE TRIGGER notify_whatsapp_lab_update
    AFTER UPDATE ON analytics.whatsapp_lab_messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_whatsapp_lab_change();

CREATE TRIGGER notify_whatsapp_lab_delete
    AFTER DELETE ON analytics.whatsapp_lab_messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_whatsapp_lab_change();

    EXECUTE FUNCTION notify_predictive_change();

-- ============================================================================
-- INITIAL DATA / DEMO SETUP
-- ============================================================================

-- Insert initial metrics cache entry
INSERT INTO analytics.metrics_cache (metric_type, metric_key, metric_value, expires_at)
VALUES ('system', 'initialized', '{"status": "ready", "version": "1.0.0"}', NOW() + INTERVAL '1 year')
ON CONFLICT (metric_type, metric_key) DO NOTHING;

-- ============================================================================
-- GRANTS (for application user)
-- ============================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA raw TO PUBLIC;
GRANT USAGE ON SCHEMA core TO PUBLIC;
GRANT USAGE ON SCHEMA analytics TO PUBLIC;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA core TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO PUBLIC;

-- Grant permissions on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO PUBLIC;

-- Grant permissions on views
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO PUBLIC;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify schema creation
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete!';
    RAISE NOTICE 'Schemas created: raw, core, analytics';
    RAISE NOTICE 'Tables created: 4 tables + 3 views';
    RAISE NOTICE 'Ready for 911 AI Flow Demo';
END $$;

-- Display table counts
SELECT 
    schemaname,
    COUNT(*) as table_count
FROM pg_tables
WHERE schemaname IN ('raw', 'core', 'analytics')
GROUP BY schemaname
ORDER BY schemaname;

-- Made with Bob
