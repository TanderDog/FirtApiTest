from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def root():
    return  """ 
    <HTML>
        <head>
            <title>My App</title>
        </head>
        <body>
            <h1>Welcome to My App</h1>
            <p>This is a simple FastAPI app.</p>
            <button onclick="window.location.href='/data'">Показать JSON</button>
        </body>
    </HTML> """

@app.get("/data")
def get_data():
    return {"name": "Даниил", "status": "ok"}