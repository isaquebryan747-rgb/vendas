CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    category VARCHAR(50),
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    partner_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    pix_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_code VARCHAR(30) UNIQUE NOT NULL,
    customer_id BIGINT NOT NULL,
    product_id INTEGER REFERENCES products(id),
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING_PAYMENT',
    partner_code VARCHAR(20),
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS commissions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) UNIQUE NOT NULL,
    partner_id INTEGER REFERENCES partners(id) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);