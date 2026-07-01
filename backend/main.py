# FleetMind API — main application entry point
# Registers all routers, middleware, and loads ML models at startup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    description="FleetMind — AI-Powered Predictive Maintenance Platform API"
)


# CORS Middleware
# Allows the React frontend to call this API from a different origin
# In development: Vite runs on port 5173
# In production: your Vercel domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://fleet-mind-predictive-maintenance-a.vercel.app",  #real URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#ML Model Loading at Startup
# Models are loaded ONCE when the server starts
# Stored in app.state — accessible from any service
# This is critical for performance: loading from disk per request = 100x slower

@app.on_event("startup")
async def load_ml_models():
    """
    Runs automatically when FastAPI starts.
    Loads all ML models into memory once.
    """
    print("\n" + "="*50)
    print("FLEETMIND API STARTING UP")
    print("="*50)

    try:
        from ml.preprocessor import AI4IPreprocessor
        from ml.predictor import FleetMindPredictor
        from ml.explainer import FleetMindExplainer

        app.state.preprocessor = AI4IPreprocessor()
        app.state.predictor    = FleetMindPredictor()
        app.state.explainer    = FleetMindExplainer()

        print("\nAll ML models loaded and ready")

    except Exception as e:
        print(f"\nFailed to load ML models: {e}")
        print("   Prediction endpoints will not work.")
        print("   Ensure training notebooks have been run first.")
        # Don't crash the server — other endpoints still work
        app.state.preprocessor = None
        app.state.predictor    = None
        app.state.explainer    = None

    print("="*50 + "\n")


#Router Registration
# Each router handles a group of related endpoints
# prefix = the URL prefix for all routes in that router
# tags   = groups them in the Swagger UI docs

from app.routers import sensors, predictions, machines, alerts

app.include_router(
    sensors.router,
    prefix="/api/sensors",
    tags=["Sensors"]
)
app.include_router(
    predictions.router,
    prefix="/api/predictions",
    tags=["Predictions"]
)
app.include_router(
    machines.router,
    prefix="/api/machines",
    tags=["Machines"]
)
app.include_router(
    alerts.router,
    prefix="/api/alerts",
    tags=["Alerts"]
)


#System Endpoints

@app.get("/health", tags=["System"])
async def health_check():
    """
    Public endpoint — no auth required.
    Used by deployment platforms (Render, Railway) to verify service is alive.
    Also checks if ML models loaded successfully.
    """
    ml_status = "loaded" if app.state.predictor is not None else "not loaded"

    return {
        "status"    : "healthy",
        "app"       : settings.APP_NAME,
        "version"   : settings.VERSION,
        "ml_models" : ml_status
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message" : "FleetMind API is running",
        "docs"    : "/docs",
        "health"  : "/health"
    }