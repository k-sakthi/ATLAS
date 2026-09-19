from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
import os

app = FastAPI(
    title="Clinical Study API",
    description="Backend for querying clinical study data with evidence trails",
    version="1.0.0"
)

# Allow CORS for Vercel production and local development
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# In production, allow all origins or specifically the Vercel URL
if os.getenv("VERCEL_URL"):
    origins.append(f"https://{os.getenv('VERCEL_URL')}")
origins.append("*")  # Fallback for dynamic Vercel previews if strict origin is too limiting

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

from stage2.api import router as stage2_router
app.include_router(stage2_router, prefix="/api/v1/stage2")

from stage3.api import router as stage3_router
app.include_router(stage3_router, prefix="/api/v1/stage3")

@app.get("/health")
def health_check():
    return {"status": "ok"}
