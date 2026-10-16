from fastapi import FastAPI
from app.database.connection import Base, engine
from app.database import models  
from app.routes import auth , images


app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(images.router)
@app.get("/")
def welcome_message():
    return {"massege" : "Welcome to the image processing application"}

