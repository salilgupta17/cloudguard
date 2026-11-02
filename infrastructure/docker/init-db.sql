-- CloudGuard PostgreSQL Multi-Database Initialization Script
-- Initializes separate logical databases for monitored application, isolated restore testing, and CloudGuard metadata.

CREATE DATABASE cloudguard_primary;
CREATE DATABASE cloudguard_isolated_test;
CREATE DATABASE cloudguard_db;

GRANT ALL PRIVILEGES ON DATABASE cloudguard_primary TO cloudguard_admin;
GRANT ALL PRIVILEGES ON DATABASE cloudguard_isolated_test TO cloudguard_admin;
GRANT ALL PRIVILEGES ON DATABASE cloudguard_db TO cloudguard_admin;
