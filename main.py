"""
This module defines the FastAPI application and configures necessary components,
such as the lifespan of the application and session middleware.

It also initializes the database on startup and includes the API routes from
the 'routes.py' module.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from starlette.requests import Request
from config import templates
from database.database import init_db
from routers import kids, ingredients, symptoms, authorisation, remedies
from fastapi.staticfiles import StaticFiles

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

# Mount the static directory (for CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")



# Add session middleware to manage sessions in the app
app.add_middleware(SessionMiddleware, secret_key="school")

# Include routes from routes.py
#app.include_router(router)

# Register Routers
app.include_router(authorisation.router)
app.include_router(kids.router)
app.include_router(ingredients.router)
app.include_router(symptoms.router)
app.include_router(remedies.router)
@app.get("/")
async def home(request: Request):
    """
        Home endpoint that returns a welcome message.

        Returns:
            dict: A simple welcome message.
        """
    return templates.TemplateResponse("auth.html", {"request": request})
