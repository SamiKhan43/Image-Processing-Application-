from fastapi import FastAPI
from app.database.connection import Base, engine
from app.database import models  

app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def welcome_massege():
    return {"massege" : "Welcome to the image processing application"}

