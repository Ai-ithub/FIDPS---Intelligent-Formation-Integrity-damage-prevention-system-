import psycopg2


conn_params = {
    "host": "localhost",
    "database": "FIDPS",
    "user": "postgres",
    "password": ""
}


with psycopg2.connect(**conn_params) as conn:
    with conn.cursor() as cur:
        with open("../migrations/create_tables.sql", "r") as f:
            sql = f.read()
            cur.execute(sql)
    conn.commit()
    print("Tables created successfully!")
