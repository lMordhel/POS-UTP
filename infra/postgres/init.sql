-- POS-UTP Postgres init (ADR-004): dos bases lógicas, una por servicio.
-- Cada servicio es propietario de sus datos; sin objetos compartidos.
SELECT 'CREATE DATABASE ventas_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ventas_db')\gexec
SELECT 'CREATE DATABASE stock_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stock_db')\gexec
