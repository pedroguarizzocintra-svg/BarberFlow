CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
 email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('client','barber','admin')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS barbers (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
 commission_bps INTEGER NOT NULL DEFAULT 4000 CHECK(commission_bps BETWEEN 0 AND 10000)
);
CREATE TABLE IF NOT EXISTS working_hours (
 id INTEGER PRIMARY KEY, barber_id INTEGER NOT NULL REFERENCES barbers(id),
 weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
 start_time TEXT NOT NULL, end_time TEXT NOT NULL, CHECK(start_time < end_time),
 UNIQUE(barber_id,weekday,start_time)
);
CREATE TABLE IF NOT EXISTS services (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 image_path TEXT, price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
 duration_min INTEGER NOT NULL CHECK(duration_min > 0),
 loyalty_eligible INTEGER NOT NULL DEFAULT 0 CHECK(loyalty_eligible IN (0,1)),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS appointments (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES users(id),
 barber_id INTEGER NOT NULL REFERENCES barbers(id), service_id INTEGER NOT NULL REFERENCES services(id),
 start_at TEXT NOT NULL, end_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('CONFIRMADO','EM_ATENDIMENTO','CONCLUIDO','CANCELADO','AUSENTE')),
 price_cents_snapshot INTEGER NOT NULL CHECK(price_cents_snapshot >= 0),
 commission_bps_snapshot INTEGER NOT NULL CHECK(commission_bps_snapshot BETWEEN 0 AND 10000),
 paid_cents INTEGER CHECK(paid_cents >= 0), completed_at TEXT,
 CHECK(start_at < end_at)
);
CREATE TABLE IF NOT EXISTS supplies (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity >= 0),
 min_quantity INTEGER NOT NULL CHECK(min_quantity >= 0),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS service_supplies (
 service_id INTEGER NOT NULL REFERENCES services(id), supply_id INTEGER NOT NULL REFERENCES supplies(id),
 quantity INTEGER NOT NULL CHECK(quantity > 0), PRIMARY KEY(service_id,supply_id)
);
CREATE TABLE IF NOT EXISTS stock_movements (
 id INTEGER PRIMARY KEY, supply_id INTEGER NOT NULL REFERENCES supplies(id),
 appointment_id INTEGER REFERENCES appointments(id), delta INTEGER NOT NULL CHECK(delta != 0),
 reason TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(appointment_id,supply_id)
);
CREATE TABLE IF NOT EXISTS revenues (
 id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents > 0), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commissions (
 id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS expenses (
 id INTEGER PRIMARY KEY, admin_id INTEGER NOT NULL REFERENCES users(id),
 description TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents > 0), occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rewards (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES users(id),
 status TEXT NOT NULL CHECK(status IN ('DISPONIVEL','RESERVADA','UTILIZADA')),
 appointment_id INTEGER UNIQUE REFERENCES appointments(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS loyalty_credits (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES users(id),
 appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 reward_id INTEGER REFERENCES rewards(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS waitlist (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES users(id),
 service_id INTEGER NOT NULL REFERENCES services(id), barber_id INTEGER NOT NULL REFERENCES barbers(id),
 window_start TEXT NOT NULL, window_end TEXT NOT NULL,
 created_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ATIVA','RETIRADA','ATENDIDA')),
 CHECK(window_start < window_end)
);
CREATE TABLE IF NOT EXISTS offers (
 id INTEGER PRIMARY KEY, waitlist_id INTEGER NOT NULL REFERENCES waitlist(id),
 start_at TEXT NOT NULL, end_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PENDENTE','ACEITA','RECUSADA','EXPIRADA')),
 appointment_id INTEGER UNIQUE REFERENCES appointments(id), CHECK(start_at < end_at)
);
CREATE TABLE IF NOT EXISTS reviews (
 id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comment TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 message TEXT NOT NULL, created_at TEXT NOT NULL, read_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_appointments_barber ON appointments(barber_id,start_at,end_at,status);
CREATE INDEX IF NOT EXISTS idx_appointments_client ON appointments(client_id,start_at);
CREATE INDEX IF NOT EXISTS idx_waitlist ON waitlist(barber_id,service_id,status,created_at,id);
CREATE INDEX IF NOT EXISTS idx_offers_expiry ON offers(status,expires_at);
CREATE INDEX IF NOT EXISTS idx_stock_movements ON stock_movements(supply_id,created_at);
CREATE INDEX IF NOT EXISTS idx_revenues ON revenues(created_at);
CREATE INDEX IF NOT EXISTS idx_commissions ON commissions(created_at);
CREATE INDEX IF NOT EXISTS idx_expenses ON expenses(occurred_at);
