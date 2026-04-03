-- Create separate databases for each service
CREATE DATABASE slh_guardian;
CREATE DATABASE slh_botshop;
CREATE DATABASE slh_wallet;
CREATE DATABASE slh_factory;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE slh_main TO postgres;
GRANT ALL PRIVILEGES ON DATABASE slh_guardian TO postgres;
GRANT ALL PRIVILEGES ON DATABASE slh_botshop TO postgres;
GRANT ALL PRIVILEGES ON DATABASE slh_wallet TO postgres;
GRANT ALL PRIVILEGES ON DATABASE slh_factory TO postgres;
