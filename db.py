"""
Database Connection & Management Module (db.py)
Hospital Pharmacy Management System (HPMS)
PostgreSQL / Neon / Render Implementation

Handles PostgreSQL connectivity via psycopg2, connection pooling/context management,
dictionary row factories (RealDictCursor), and unified parameter handling.
Supports cloud-hosted PostgreSQL instances via DATABASE_URL or individual env variables.
"""

import os
import re
import logging
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from psycopg2 import DatabaseError, IntegrityError, OperationalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", os.getenv("DB_DATABASE", "pharmacy_db"))
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")


def get_connection():
    """
    Establish a connection to PostgreSQL.
    Prioritizes DATABASE_URL if available (common for Neon, Render, Supabase).
    Falls back to individual DB_* parameters.
    """
    try:
        if DATABASE_URL:
            # Normalize URL if using legacy postgres:// scheme
            conn_url = DATABASE_URL
            if conn_url.startswith("postgres://"):
                conn_url = "postgresql://" + conn_url[len("postgres://"):]

            # Ensure SSL mode is enabled for remote cloud databases
            if "neon.tech" in conn_url or "render.com" in conn_url or "supabase" in conn_url:
                if "sslmode=" not in conn_url:
                    sep = "&" if "?" in conn_url else "?"
                    conn_url += f"{sep}sslmode=require"

            return psycopg2.connect(conn_url)
        else:
            conn_params = {
                "user": DB_USER,
                "password": DB_PASSWORD,
                "host": DB_HOST,
                "port": DB_PORT,
                "dbname": DB_NAME,
                "sslmode": DB_SSLMODE
            }
            # Remove password if None to allow peer/trust auth locally
            if not DB_PASSWORD:
                conn_params.pop("password", None)
            return psycopg2.connect(**conn_params)
    except OperationalError as err:
        logger.error(f"PostgreSQL Operational Error: {err}")
        raise err
    except DatabaseError as err:
        logger.error(f"PostgreSQL Connection Error: {err}")
        raise err


@contextmanager
def get_db_cursor(commit=False, cursor_factory=psycopg2.extras.RealDictCursor):
    """
    Context manager for database cursor with automatic cleanup and transaction handling.
    Yields (connection, cursor).
    Rolls back automatically on unhandled exceptions.
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=cursor_factory)
        yield connection, cursor
        if commit:
            connection.commit()
    except Exception as e:
        if connection:
            try:
                connection.rollback()
                logger.warning("Database transaction rolled back due to error.")
            except Exception as rb_err:
                logger.error(f"Rollback failed: {rb_err}")
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


def rows_to_dicts(cursor, rows):
    """
    Convert raw or RealDictRow tuples/dicts into lowercased standard Python dictionaries.
    """
    if not rows:
        return []
    result = []
    for row in rows:
        if hasattr(row, "items"):
            result.append({k.lower(): v for k, v in row.items()})
        elif cursor and cursor.description:
            columns = [col[0].lower() for col in cursor.description]
            result.append(dict(zip(columns, row)))
        else:
            result.append(dict(row))
    return result


def row_to_dict(cursor, row):
    """
    Convert a single raw or RealDictRow tuple/dict into a lowercased standard Python dictionary.
    """
    if not row:
        return None
    if hasattr(row, "items"):
        return {k.lower(): v for k, v in row.items()}
    if cursor and cursor.description:
        columns = [col[0].lower() for col in cursor.description]
        return dict(zip(columns, row))
    return dict(row)


def prepare_sql(sql):
    """
    Preprocess SQL string to ensure 100% PostgreSQL compatibility:
    1. Converts Oracle-style :param_name bindings to psycopg2 %(param_name)s
       (while preserving PostgreSQL type casts like ::text or ::date via negative lookbehind).
    2. Translates common Oracle function names to standard SQL equivalents.
    """
    if not sql:
        return sql

    # Convert :param to %(param)s (ignoring ::type casts)
    converted_sql = re.sub(r'(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)', r'%(\1)s', sql)

    # Convert NVL( to COALESCE(
    converted_sql = re.sub(r'\bNVL\s*\(', 'COALESCE(', converted_sql, flags=re.IGNORECASE)

    # Convert TRUNC(CURRENT_DATE) to CURRENT_DATE
    converted_sql = re.sub(r'\bTRUNC\s*\(\s*CURRENT_DATE\s*\)', 'CURRENT_DATE', converted_sql, flags=re.IGNORECASE)

    # Convert TRUNC(SYSDATE) to CURRENT_DATE
    converted_sql = re.sub(r'\bTRUNC\s*\(\s*SYSDATE\s*\)', 'CURRENT_DATE', converted_sql, flags=re.IGNORECASE)

    # Convert SYSDATE to CURRENT_TIMESTAMP
    converted_sql = re.sub(r'\bSYSDATE\b', 'CURRENT_TIMESTAMP', converted_sql, flags=re.IGNORECASE)

    # Convert TRUNC(col) to DATE(col) (when not already followed by CURRENT_DATE/SYSDATE)
    converted_sql = re.sub(r'\bTRUNC\s*\(', 'DATE(', converted_sql, flags=re.IGNORECASE)

    # Convert FETCH FIRST N ROWS ONLY to LIMIT N
    converted_sql = re.sub(r'\bFETCH\s+FIRST\s+(\d+)\s+ROWS?\s+ONLY\b', r'LIMIT \1', converted_sql, flags=re.IGNORECASE)

    return converted_sql


def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Execute a parameterized SQL query safely against PostgreSQL.
    Returns:
        - List of dicts if fetchall=True
        - Single dict if fetchone=True
        - None / rowcount if executing DML
    """
    params = params or {}
    pg_sql = prepare_sql(sql)
    with get_db_cursor(commit=commit) as (conn, cursor):
        cursor.execute(pg_sql, params)
        if fetchone:
            row = cursor.fetchone()
            return row_to_dict(cursor, row)
        if fetchall:
            rows = cursor.fetchall()
            return rows_to_dicts(cursor, rows)
        return cursor.rowcount
