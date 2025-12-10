# src/main.py

# import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from src.common.database.database import connect_to_db, close_db_connection
from src.common.config import settings
from src.router.routers import include_routers
# from src.common.utils.email import test_email

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    # Schedule test_email to run in the background within the existing event loop
    # asyncio.create_task(test_email())
    yield
    await close_db_connection()

# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="Retgrow Learn API",
    description="Retgrow Initiative's platform to aid students' tech learning journey.",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware for CORS using allowed origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from a separate file
include_routers(app)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retgrow Learn API</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }
        .header {
            text-align: center;
            padding: 2rem 0;
            border-bottom: 2px solid #eee;
            margin-bottom: 2rem;
        }
        .header h1 {
            color: #2563eb;
            margin: 0;
        }
        .content {
            background: #f8fafc;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .endpoint {
            background: #fff;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            border: 1px solid #e5e7eb;
        }
        .endpoint code {
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: monospace;
        }
        .cta {
            text-align: center;
            margin-top: 2rem;
        }
        .button {
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            text-decoration: none;
            transition: background 0.2s;
        }
        .button:hover {
            background: #1d4ed8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to Retgrow Learn API</h1>
        <p>A powerful API for learning and growth</p>
    </div>
    
    <div class="content">
        <h2>Getting Started</h2>
        <p>The Retgrow Learn API provides endpoints for managing learning resources and tracking progress. Here's what you need to know to get started:</p>
        
        <div class="endpoint">
            <h3>Base URL</h3>
            <code>https://api.retgrow.com/v1</code>
        </div>
        
        <h3>Key Features</h3>
        <ul>
            <li>RESTful API design</li>
            <li>JSON response format</li>
            <li>Secure authentication</li>
            <li>Comprehensive documentation</li>
        </ul>
        
        <h3>Quick Example</h3>
        <div class="endpoint">
            <p>Make your first API call:</p>
            <code>curl -X GET https://api.retgrow.com/v1/status</code>
        </div>
        
        <div class="cta">
            <a href="/docs" class="button">View Full Documentation</a>
        </div>
    </div>
</body>
</html>
"""
    return html_content