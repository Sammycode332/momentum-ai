BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '20s';
SET LOCAL lock_timeout = '2s';
SET LOCAL search_path = pg_catalog, public;

-- Confirm production and neondb in the Neon SQL Editor selectors before running.
-- The database name alone cannot distinguish branches.
-- Only PostgreSQL catalogs are queried. No application or Auth rows are read.
-- Compare schema evidence with available migration history. Object presence
-- alone does not establish that a particular migration script was executed.
WITH inventory AS (
    SELECT c.oid, n.nspname AS schema_name, c.relname AS table_name,
           c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS rls_forced,
           c.relowner
    FROM pg_class AS c
    JOIN pg_namespace AS n ON n.oid = c.relnamespace
    WHERE current_database() = 'neondb'
      AND c.relkind IN ('r', 'p')
      AND (n.nspname = 'public' OR n.nspname = 'neon_auth')
), app_tables AS (
    SELECT * FROM inventory
    WHERE schema_name = 'public' AND table_name LIKE 'momentum\_%' ESCAPE '\'
), roles AS (
    SELECT oid, rolname, rolcanlogin, rolsuper, rolbypassrls,
           rolcreaterole, rolcreatedb, rolinherit, rolreplication,
           has_database_privilege(oid, current_database(), 'CONNECT') AS can_connect,
           has_schema_privilege(oid, 'public', 'USAGE') AS public_usage,
           has_schema_privilege(oid, 'public', 'CREATE') AS public_create
    FROM pg_roles
    WHERE rolname IN ('momentum_app', 'momentum_scheduler', 'momentum_scheduler_worker')
)
SELECT jsonb_build_object(
    'database', current_database(),
    'postgres_version', current_setting('server_version'),
    'transaction_read_only', current_setting('transaction_read_only'),
    'audit_role', current_user,
    'neon_auth_schema_exists', to_regnamespace('neon_auth') IS NOT NULL,
    'inventory', (SELECT jsonb_agg(jsonb_build_object(
        'schema', schema_name, 'table', table_name,
        'owner', pg_get_userbyid(relowner), 'rls_enabled', rls_enabled,
        'rls_forced', rls_forced
    ) ORDER BY schema_name, table_name) FROM inventory),
    'roles', (SELECT jsonb_agg(to_jsonb(roles) - 'oid' ORDER BY rolname) FROM roles),
    'memberships', (SELECT jsonb_agg(jsonb_build_object(
        'member', member.rolname, 'role', parent.rolname, 'admin_option', m.admin_option
    ) ORDER BY member.rolname, parent.rolname)
    FROM pg_auth_members AS m
    JOIN roles AS member ON member.oid = m.member
    JOIN pg_roles AS parent ON parent.oid = m.roleid),
    'effective_table_grants', (SELECT jsonb_agg(jsonb_build_object(
        'table', t.table_name, 'role', r.rolname, 'privilege', p.name
    ) ORDER BY t.table_name, r.rolname, p.name)
    FROM app_tables AS t CROSS JOIN roles AS r
    CROSS JOIN unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                           'REFERENCES', 'TRIGGER']) AS p(name)
    WHERE has_table_privilege(r.oid, t.oid, p.name)),
    'columns', (SELECT jsonb_agg(jsonb_build_object(
        'table', t.table_name, 'name', a.attname, 'type', format_type(a.atttypid, a.atttypmod),
        'not_null', a.attnotnull, 'default', pg_get_expr(d.adbin, d.adrelid),
        'column_acl', a.attacl
    ) ORDER BY t.table_name, a.attnum)
    FROM app_tables AS t
    JOIN pg_attribute AS a ON a.attrelid = t.oid AND a.attnum > 0 AND NOT a.attisdropped
    LEFT JOIN pg_attrdef AS d ON d.adrelid = t.oid AND d.adnum = a.attnum),
    'constraints', (SELECT jsonb_agg(jsonb_build_object(
        'table', t.table_name, 'name', c.conname, 'definition', pg_get_constraintdef(c.oid),
        'validated', c.convalidated
    ) ORDER BY t.table_name, c.conname)
    FROM app_tables AS t JOIN pg_constraint AS c ON c.conrelid = t.oid),
    'indexes', (SELECT jsonb_agg(jsonb_build_object(
        'table', t.table_name, 'definition', pg_get_indexdef(i.indexrelid),
        'valid', i.indisvalid
    ) ORDER BY t.table_name, pg_get_indexdef(i.indexrelid))
    FROM app_tables AS t JOIN pg_index AS i ON i.indrelid = t.oid),
    'policies', (SELECT jsonb_agg(to_jsonb(p) ORDER BY p.tablename, p.policyname)
    FROM pg_policies AS p JOIN app_tables AS t
      ON t.schema_name = p.schemaname AND t.table_name = p.tablename),
    'public_grants', (SELECT jsonb_agg(jsonb_build_object(
        'table', t.table_name, 'privilege', acl.privilege_type
    ) ORDER BY t.table_name, acl.privilege_type)
    FROM app_tables AS t JOIN pg_class AS c ON c.oid = t.oid
    CROSS JOIN LATERAL aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) AS acl
    WHERE acl.grantee = 0)
) AS catalog_report;

ROLLBACK;
