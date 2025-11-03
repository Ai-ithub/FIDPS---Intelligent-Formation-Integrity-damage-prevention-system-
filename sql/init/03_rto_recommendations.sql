-- RTO Recommendations Table
-- Stores RTO recommendations persistently instead of in-memory

CREATE TABLE IF NOT EXISTS rto_recommendations (
    id VARCHAR(255) PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    well_id VARCHAR(50) NOT NULL,
    damage_type VARCHAR(20) NOT NULL,
    damage_probability DECIMAL(5,4) CHECK (damage_probability >= 0 AND damage_probability <= 1),
    
    -- Current parameters (JSON)
    current_values JSONB NOT NULL,
    
    -- Recommended parameters (JSON)
    recommended_values JSONB NOT NULL,
    
    -- Optimization results
    expected_improvement DECIMAL(8,2),
    risk_reduction DECIMAL(8,2),
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Constraints
    constraints_satisfied BOOLEAN DEFAULT true,
    constraint_violations TEXT[],
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'applied')),
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    
    -- Metadata
    optimization_method VARCHAR(50),
    computation_time_ms DECIMAL(10,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_rto_timestamp ON rto_recommendations (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rto_well_id ON rto_recommendations (well_id);
CREATE INDEX IF NOT EXISTS idx_rto_status ON rto_recommendations (status);
CREATE INDEX IF NOT EXISTS idx_rto_damage_type ON rto_recommendations (damage_type);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON rto_recommendations TO fidps_user;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_rto_recommendations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_rto_recommendations_updated_at
    BEFORE UPDATE ON rto_recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_rto_recommendations_updated_at();

COMMIT;

