
import psycopg2


conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="postgres",
    password="1234",
    port=5432
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    age INTEGER
)
""")
conn.commit()

def add_user (name: str, age: int):
    cur.execute(
        "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
        (name, age)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    return new_id

def get_users():
    cur.execute("SELECT id, name, age FROM users")
    rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "age": r[2]} for r in rows]