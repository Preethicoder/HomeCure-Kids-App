from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.sessions import SessionMiddleware

from database import init_db
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    init_db()  # Call the function to create tables if not exist
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="school")
# Include routes from routes.py
app.include_router(router)