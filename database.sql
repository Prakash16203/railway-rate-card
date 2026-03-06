CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, password_hash, role, email) VALUES
('user', '1234', 'customer', 'user@example.com'),
('Admin', '1234', 'admin', 'admin@example.com');



CREATE TABLE rates (
    id SERIAL PRIMARY KEY,
    from_station VARCHAR(50) NOT NULL,
    to_station VARCHAR(50) NOT NULL,
    train_number VARCHAR(20),
    rate_card VARCHAR(100) NOT NULL,
    slr VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add the same demo data as your old fake rates
INSERT INTO rates (from_station, to_station, train_number, rate_card, slr) VALUES
('S1', 'S2', NULL, 'R1 - ₹1250', 'SLR1 - Kharadi Substation'),
('S2', 'S1', NULL, 'R1 - ₹1250', 'SLR1 - Kharadi Substation'),
('SRINAGAR', 'JAMMU', '1234', 'Kashmir Express Freight - ₹3850', 'SLR-K - Srinagar Goods Yard'),
('JAMMU', 'SRINAGAR', '1234', 'Kashmir Express Freight - ₹3850', 'SLR-J - Jammu Cantt Yard');


CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    account_group VARCHAR(50),
    email VARCHAR(100),
    mobile VARCHAR(20),
    alt_mobile VARCHAR(20),
    address1 TEXT,
    address2 TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    pin VARCHAR(10),
    gst VARCHAR(50),
    pan VARCHAR(20),
    aadhaar VARCHAR(20),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some dummy vendors (matching your original FAKE_VENDORS style)
INSERT INTO vendors (account_name, mobile, city, state, gst, email) VALUES
('Patel Logistics', '9876543210', 'PUNE', 'MAHARASHTRA', '27AAQFP1234R1Z5', 'patel@logistics.in'),
('Sharma Transports', '9123456789', 'MUMBAI', 'MAHARASHTRA', '27AABCS5678D1Z2', 'sharma@trans.in'),
('Khan Cargo', '9988776655', 'NAGPUR', 'MAHARASHTRA', '27AAAFK9999Q1Z8', 'khan@cargo.com'),
('Express Movers', '9898989898', 'DELHI', 'DELHI', '07AAAFE4567P1Z9', 'express@movers.com');



CREATE TABLE rate_cards (
    id SERIAL PRIMARY KEY,
    train_no VARCHAR(20),
    vehicle_type VARCHAR(50),
    weight_capacity VARCHAR(50),
    parcel_type VARCHAR(50),
    days VARCHAR(100),
    origin_station VARCHAR(50) NOT NULL,
    origin_code VARCHAR(20),
    dest_station VARCHAR(50) NOT NULL,
    dest_code VARCHAR(20),
    rate_type VARCHAR(50),
    rate_card VARCHAR(100) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),          -- connects to vendors table
    origin_person VARCHAR(100),
    origin_mobile VARCHAR(20),
    dest_person VARCHAR(100),
    dest_mobile VARCHAR(20),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert 3 example detailed rate cards (linking to vendor ids 1,2,3,4 from previous insert)
INSERT INTO rate_cards (
    train_no, origin_station, dest_station, rate_card, vendor_id,
    vehicle_type, days, remark, origin_mobile, dest_mobile
) VALUES
('1234', 'SRINAGAR', 'JAMMU', 'Kashmir Express Freight - ₹3850', 1,
 'Parcel Van', 'Daily', 'Priority loading, cold chain option', '9900990099', '8800880088'),
('5678', 'DELHI', 'MUMBAI', 'North-South Parcel - ₹4500', 2,
 'SLR', 'Mon-Wed-Fri', 'Bulk parcels preferred', '9123456789', '9988776655'),
('9999', 'PUNE', 'BANGALORE', 'South Express Freight - ₹5200', 3,
 'Brake Van', 'Tue-Thu-Sat', 'Max 5 tons per trip', '9876543210', '9898989898');


 