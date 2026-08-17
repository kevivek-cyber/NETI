CREATE TABLE IF NOT EXISTS ceremony_events (
    id BIGSERIAL PRIMARY KEY,
    ceremony_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION prevent_ceremony_events_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'append-only: ceremony_events cannot be updated or deleted';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ceremony_events_append_only ON ceremony_events;

CREATE TRIGGER ceremony_events_append_only
BEFORE UPDATE OR DELETE ON ceremony_events
FOR EACH ROW
EXECUTE FUNCTION prevent_ceremony_events_mutation();