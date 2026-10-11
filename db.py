"""
Database Connection & Management Module (db.py)
Hospital Pharmacy Management System (HPMS)
VIT Chennai DBMS PAT 4 Project

Handles Oracle Database XE 21c (XEPDB1) connectivity via python-oracledb,
connection context management, dictionary row factories, and explicit transactions.
"""

import os
import logging
from contextlib import contextmanager
import oracledb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER", "pharmacy_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 1521))
DB_SERVICE_NAME = os.getenv("DB_SERVICE_NAME", "xepdb1")


def get_connection():
    """
    Establish a standalone connection to Oracle XE 21c via thin mode oracledb.
    """
    try:
        dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE_NAME)
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=dsn
        )
        return connection
    except oracledb.Error as err:
        logger.error(f"Oracle Connection Error: {err}")
        raise err


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database cursor with automatic cleanup and transaction handling.
    Yields (connection, cursor).
    Rolls back automatically on unhandled exceptions.
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
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
    Convert raw cursor tuples into lowercased dictionaries for ergonomic template rendering.
    """
    if not rows or not cursor.description:
        return []
    columns = [col[0].lower() for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def row_to_dict(cursor, row):
    """
    Convert a single cursor tuple into a lowercased dictionary.
    """
    if not row or not cursor.description:
        return None
    columns = [col[0].lower() for col in cursor.description]
    return dict(zip(columns, row))


def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Execute a parameterized SQL query safely.
    Returns:
        - List of dicts if fetchall=True
        - Single dict if fetchone=True
        - None/rowcount if executing DML
    """
    params = params or {}
    with get_db_cursor(commit=commit) as (conn, cursor):
        cursor.execute(sql, params)
        if fetchone:
            row = cursor.fetchone()
            return row_to_dict(cursor, row)
        if fetchall:
            rows = cursor.fetchall()
            return rows_to_dicts(cursor, rows)
        return cursor.rowcount
