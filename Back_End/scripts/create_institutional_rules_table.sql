-- Manual SQL script to create institutional_rules table
-- Run this if Alembic migration fails

-- Create enum
DO $$ BEGIN
    CREATE TYPE ruletype AS ENUM (
        'TIME_WINDOW', 'SLOT_BLACKOUT', 'MAX_CONSECUTIVE', 'ELECTIVE_SYNC',
        'FACULTY_WORKLOAD', 'ROOM_PREFERENCE', 'DAY_BLACKOUT', 'CUSTOM'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create table
CREATE TABLE IF NOT EXISTS institutional_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    rule_type ruletype NOT NULL,
    configuration JSONB NOT NULL,
    is_hard_constraint BOOLEAN NOT NULL DEFAULT true,
    weight FLOAT NOT NULL DEFAULT 1.0,
    applies_to_departments INTEGER[] DEFAULT '{}',
    applies_to_years INTEGER[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_institutional_rules_id ON institutional_rules(id);
CREATE INDEX IF NOT EXISTS ix_institutional_rules_rule_type ON institutional_rules(rule_type);
CREATE INDEX IF NOT EXISTS ix_institutional_rules_is_active ON institutional_rules(is_active);

-- Mark migration as applied (update alembic_version)
-- UPDATE alembic_version SET version_num = 'bb162e2c2f0d';
