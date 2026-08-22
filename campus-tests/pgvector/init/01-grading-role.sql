-- Runs once, automatically, on first container startup (standard behavior of
-- files mounted into /docker-entrypoint-initdb.d/ on the postgres image).
-- Creates the low-privilege role every candidate submission runs as: no
-- CREATEDB/CREATEROLE/superuser, so even if the transaction-rollback +
-- statement_timeout wrapper around each submission were ever bypassed, this
-- role alone cannot persist changes or affect other schemas' data.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE ROLE grader WITH LOGIN PASSWORD 'grader_local_only' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION CONNECTION LIMIT 5;
GRANT CONNECT ON DATABASE campus_sql_grading TO grader;
