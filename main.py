from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def index():
    return {"message": "Hello from blog 4!"}


@app.get("/test")
async def test():
    return {"message": "This works"}
