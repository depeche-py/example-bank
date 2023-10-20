import fastapi as _fastapi

app = _fastapi.FastAPI()


@app.get("/")
def index():
    return {"message": "Hello, world!"}
