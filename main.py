from fastapi import FastAPI
from app.db.database import engine, Base
from app.api import users as users_router
from app.api import notes as notes_router

app = FastAPI(title="NoteVault API")

# include routers
app.include_router(users_router.router)
app.include_router(notes_router.router)


@app.on_event("startup")
def on_startup():
    # create database tables
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
