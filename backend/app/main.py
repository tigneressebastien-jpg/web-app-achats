from __future__ import annotations

from fastapi import FastAPI

from app.api import routes_calculations, routes_exports, routes_health, routes_imports
from app.api import routes_lunes
from app.api import routes_platforms
from app.database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Achats Fruits et Legumes V1", version="0.1.0")

app.include_router(routes_health.router)
app.include_router(routes_platforms.router)
app.include_router(routes_calculations.router)
app.include_router(routes_lunes.router)
app.include_router(routes_imports.router)
app.include_router(routes_exports.router)
