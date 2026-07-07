from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database import add_user, get_users

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class User(BaseModel):
    name: str
    age: int


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/user")
def create_user(user: User):
    new_id = add_user(user.name, user.age)
    return {"message": f"Сохранён {user.name}, id={new_id}"}


@app.get("/users")
def read_users():
    return get_users()
