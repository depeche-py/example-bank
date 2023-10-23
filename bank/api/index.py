from ._base import app


@app.get("/")
def index():
    return {"message": "Hello, world!"}
