DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'truecost_api') THEN
    CREATE ROLE truecost_api LOGIN PASSWORD 'api-local-only';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'truecost_broker') THEN
    CREATE ROLE truecost_broker LOGIN PASSWORD 'broker-local-only';
  END IF;
END $$;
GRANT CONNECT ON DATABASE truecost TO truecost_broker;
GRANT USAGE ON SCHEMA public TO truecost_broker;
GRANT CONNECT ON DATABASE truecost TO truecost_api;
