DROP SCHEMA IF EXISTS extensions;

CREATE SCHEMA extensions;

SET search_path = extensions;

-- USE PGSPHERE

CREATE EXTENSION pg_sphere SCHEMA extensions;
