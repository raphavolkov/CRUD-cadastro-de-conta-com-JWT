from fastapi import FastAPI

from .database import Base, engine
from .routers import auth
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Api no ar"}
