from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api_router import router as api_router
from app.utils.exception_handlers import register_exception_handlers
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Crypto News API with Gemini AI")

# Configure CORS
# Get allowed origins from environment variable, with defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,https://console.bloktrading.io").split(",")

# Add any additional origins you want to allow
origins = [
    origin.strip() for origin in ALLOWED_ORIGINS
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the browser
)

# Register exception handlers
register_exception_handlers(app)

app.include_router(api_router)