from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2

app = FastAPI()

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

class User(BaseModel):
    name: str
    age: int

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <body>
            <h1>Мои пользователи</h1>
            <button onclick="addUser()">Добавить</button>
            <button onclick="window.location.href='/users'">Показать всех</button>

            <script>
            async function addUser() {
                const name = prompt("Введите имя:");
                const age = prompt("Введите возраст:");

                const response = await fetch('/user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name, age: parseInt(age)})
                });
                const data = await response.json();
                alert(data.message);
            }
            </script>
        </body>
    </html>
    """

@app.post("/user")
def create_user(user: User):
    cur.execute(
        "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
        (user.name, user.age)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    return {"message": f"Сохранён {user.name}, id={new_id}"}

@app.get("/users")
def get_users():
    cur.execute("SELECT id, name, age FROM users")
    rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "age": r[2]} for r in rows]