"""
This module defines the FastAPI application and configures necessary components,
such as the lifespan of the application and session middleware.

It also initializes the database on startup and includes the API routes from
the 'routes.py' module.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from database import init_db
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Manages the lifespan of the FastAPI application, initializing resources
        on startup and cleaning up on shutdown.

        During the lifespan, the database is initialized (tables are created if
        they do not exist). When the app shuts down, it logs a shutdown message.

        Args:
            app (FastAPI): The FastAPI application instance.
    """
    print("Initializing database...")
    init_db()  # Call the function to create tables if not exist
    yield
    print("Shutting down...")

# Create FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Add session middleware to manage sessions in the app
app.add_middleware(SessionMiddleware, secret_key="school")

# Include routes from routes.py
app.include_router(router)
