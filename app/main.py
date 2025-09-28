from fastapi import FastAPI

from .api.v1.endpoints import healthcheck

app = FastAPI(title="mindful web service")
app.include_router(healthcheck.router, prefix="/api/v1")
