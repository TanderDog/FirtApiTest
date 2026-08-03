CREATE TABLE IF NOT EXISTS mos_tikets_daily (
    id SERIAL PRIMARY KEY,
    secid VARCHAR(10) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    tiket_date DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (secid, tiket_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_secid_date
ON mos_tikets_daily (secid, tiket_date DESC);