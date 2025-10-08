import psycopg2
import pytest

conn_params = {
    "host": "localhost",
    "database": "FIDPS",
    "user": "postgres",
    "password": ""
}

def test_tables_exist():
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.well_measurements');")
            assert cur.fetchone()[0] is not None

            cur.execute("SELECT to_regclass('public.damage_types');")
            assert cur.fetchone()[0] is not None

def test_columns_exist():
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='well_measurements';")
            cols = [c[0] for c in cur.fetchall()]
            for expected_col in ["measurement_id", "timestamp", "depth", "mud_pressure", "damage_type_id"]:
                assert expected_col in cols
