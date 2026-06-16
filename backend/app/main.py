from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.kpi_report.router import router as kpi_router
from app.modules.monthly_kpi.router import router as monthly_kpi_router

app = FastAPI(
    title="Prodoscore Custom Report Engine Center",
    description="Refactored modular REST data API running analytical services.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.111.22:3000",  # Allows your local network IP from your logs
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers
)

# Register Module Router Components
app.include_router(kpi_router)
app.include_router(monthly_kpi_router)


@app.get("/health")
def health_check():
    return {"status": "operational", "engine": "FastAPI + UV Project Container Setup"}
