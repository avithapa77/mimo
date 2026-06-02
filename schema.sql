CREATE DATABASE IF NOT EXISTS mimo_db;
USE mimo_db;

CREATE TABLE IF NOT EXISTS users (
    user_id   VARCHAR(50)  PRIMARY KEY,
    name      VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS gateways (
    gateway_id  VARCHAR(50)   PRIMARY KEY,
    user_id     VARCHAR(50)   NOT NULL,
    label       VARCHAR(100)  NOT NULL,
    lat         DECIMAL(9,6)  NOT NULL,
    lng         DECIMAL(9,6)  NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS devices (
    device_id   VARCHAR(50)  PRIMARY KEY,
    gateway_id  VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    type        VARCHAR(50)  NOT NULL,
    state       VARCHAR(50)  NOT NULL,
    FOREIGN KEY (gateway_id) REFERENCES gateways(gateway_id)
);

-- Seed data
INSERT IGNORE INTO users VALUES ('user_001', 'Hari Prasad');

INSERT IGNORE INTO gateways VALUES
    ('gw_kathmandu_home', 'user_001', 'Kathmandu Home', 27.7172, 85.3240),
    ('gw_pokhara_house',  'user_001', 'Pokhara House',  28.2096, 83.9856);

INSERT IGNORE INTO devices VALUES
    ('dev_01', 'gw_kathmandu_home', 'Living Room Light', 'light',      'on'),
    ('dev_02', 'gw_kathmandu_home', 'Front Door Lock',   'lock',       'locked'),
    ('dev_03', 'gw_kathmandu_home', 'AC Unit',           'thermostat', 'off'),
    ('dev_10', 'gw_pokhara_house',  'Garden Light',      'light',      'off'),
    ('dev_11', 'gw_pokhara_house',  'Main Gate',         'lock',       'locked');
