CREATE TABLE IF NOT EXISTS mos_tikets_raw (
    id SERIAL PRIMARY KEY,
    secid VARCHAR(10) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_secid_fetched
ON mos_tikets_raw (secid, fetched_at DESC);