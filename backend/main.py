from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import odds, alerts, bets, arb, sharp

app = FastAPI(title="OddsIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(odds.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(bets.router, prefix="/api/v1")
app.include_router(arb.router, prefix="/api/v1")
app.include_router(sharp.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
