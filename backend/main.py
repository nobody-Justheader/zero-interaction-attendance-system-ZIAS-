"""
ZIAS FastAPI Application
Main entry point for REST API server
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

from api.routes import auth, devices, attendance, students
from api.database import init_db, close_db
from api.config import settings
from mqtt.client import mqtt_client
import redis.asyncio as redis

security = HTTPBearer()

# Redis connection pool
redis_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global redis_pool
    init_db()
    redis_pool = redis.ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
    
    # Start MQTT client in background
    mqtt_client.start()
    
    print(f"ZIAS API Server started on {settings.API_HOST}:{settings.API_PORT}")
    
    yield
    
    # Shutdown
    close_db()
    mqtt_client.stop()
    await redis_pool.disconnect()
    print("ZIAS API Server shutdown")


app = FastAPI(
    title="ZIAS API",
    description="Zero Interaction Attendance System REST API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "ZIAS API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "mqtt": mqtt_client.is_connected()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
