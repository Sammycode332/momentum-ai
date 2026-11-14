"""Read-only connectivity/catalog probe; never prints connection strings or user rows."""
import json
import psycopg
from psycopg.conninfo import conninfo_to_dict
from app.database import _database_url, DatabaseConfigurationError


def main():
    try:
        url = _database_url()
        parameters = conninfo_to_dict(url)
        print(json.dumps({'configuration_present': True, 'runtime_role_is_momentum_app': parameters.get('user') == 'momentum_app'}))
        with psycopg.connect(url, sslmode='require', channel_binding='require', gssencmode='disable', connect_timeout=5) as connection:
            connection.execute('SET TRANSACTION READ ONLY')
            present = connection.execute("SELECT to_regclass('public.momentum_onboarding') IS NOT NULL").fetchone()[0]
            report = {'connected': True, 'onboarding_present': present}
            if present:
                report['onboarding_rls_active'] = connection.execute("SELECT row_security_active('public.momentum_onboarding'::regclass)").fetchone()[0]
                report['select_allowed'] = connection.execute("SELECT has_table_privilege(current_user,'public.momentum_onboarding','SELECT')").fetchone()[0]
            print(json.dumps(report))
            return 0
    except DatabaseConfigurationError:
        print(json.dumps({'connected': False, 'category': 'INVALID_CONFIGURATION'}))
    except psycopg.Error as error:
        # Inspect internally, but never print the exception: it may contain private configuration.
        message = str(error).lower()
        rules = [
            (('resolve', 'translate host', 'name or service', 'nodename'), 'DNS_RESOLUTION'),
            (('timeout', 'timed out'), 'TIMEOUT'),
            (('password authentication', 'authentication failed'), 'DB_CREDENTIALS'),
            (('channel binding',), 'CHANNEL_BINDING'), (('ssl', 'tls'), 'TLS'),
            (('does not exist',), 'MISSING_OBJECT'), (('permission denied',), 'PERMISSIONS'),
            (('refused',), 'CONNECTION_REFUSED'),
        ]
        print(json.dumps({'connected': False, 'type': type(error).__name__, 'sqlstate': error.sqlstate,
                          'categories': [label for words, label in rules if any(word in message for word in words)]}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
