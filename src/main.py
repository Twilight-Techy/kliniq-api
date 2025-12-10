# src/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from src.common.database.database import connect_to_db, close_db_connection
from src.common.config import settings
from src.router.routers import include_routers

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await close_db_connection()

# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="Kliniq API",
    description="AI-Powered Clinical Communication API for African Healthcare",
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
    <title>Kliniq API</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            background: #0a0a0f;
            color: #e5e5e5;
            min-height: 100vh;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Animated background */
        .bg-gradient {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }
        
        .content {
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 4rem 0 3rem;
        }
        
        .logo {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 2rem;
        }
        
        .logo-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 24px;
            color: white;
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
        }
        
        .logo-text {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #a5a5a5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #fff 0%, #6366f1 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            color: #9ca3af;
            font-size: 1.125rem;
        }
        
        /* Stats */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(99, 102, 241, 0.3);
            transform: translateY(-2px);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #6366f1;
            margin-bottom: 0.25rem;
        }
        
        .stat-label {
            color: #9ca3af;
            font-size: 0.875rem;
        }
        
        /* Cards */
        .card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #fff;
        }
        
        .card p {
            color: #9ca3af;
            margin-bottom: 1.5rem;
        }
        
        /* Endpoints */
        .endpoints {
            display: grid;
            gap: 1rem;
        }
        
        .endpoint {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 1.25rem;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            transition: all 0.2s ease;
        }
        
        .endpoint:hover {
            background: rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.3);
        }
        
        .method {
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .method.post { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
        .method.get { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        
        .endpoint-path {
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 0.9rem;
            color: #e5e5e5;
        }
        
        .endpoint-desc {
            margin-left: auto;
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        /* Features */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .feature {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: rgba(99, 102, 241, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(99, 102, 241, 0.1);
        }
        
        .feature-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6366f1;
        }
        
        .feature span {
            font-size: 0.9rem;
            color: #e5e5e5;
        }
        
        /* CTA */
        .cta {
            text-align: center;
            padding: 2rem 0;
        }
        
        .button {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 0.875rem 2rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
        }
        
        .button svg {
            width: 20px;
            height: 20px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem 0;
            color: #6b7280;
            font-size: 0.875rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 2rem;
        }
        
        .footer a {
            color: #6366f1;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="bg-gradient"></div>
    
    <div class="container content">
        <header class="header">
            <div class="logo">
                <div class="logo-icon">K</div>
                <span class="logo-text">Kliniq API</span>
            </div>
            <h1>Healthcare Communication API</h1>
            <p>AI-powered multilingual support for African healthcare</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">20+</div>
                <div class="stat-label">African Languages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">&lt;1s</div>
                <div class="stat-label">Response Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">99.9%</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔐 Authentication Endpoints</h2>
            <p>Secure user authentication with JWT tokens and role-based access control.</p>
            
            <div class="endpoints">
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span class="endpoint-path">/auth/signup</span>
                    <span class="endpoint-desc">Create new account</span>
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span class="endpoint-path">/auth/login</span>
                    <span class="endpoint-desc">Authenticate user</span>
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span class="endpoint-path">/auth/verify</span>
                    <span class="endpoint-desc">Verify email</span>
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <span class="endpoint-path">/auth/me</span>
                    <span class="endpoint-desc">Get current user</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>✨ Key Features</h2>
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                        </svg>
                    </div>
                    <span>JWT Authentication</span>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        </svg>
                    </div>
                    <span>Role-based Access</span>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <span>Async PostgreSQL</span>
                </div>
                <div class="feature">
                    <div class="feature-icon">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                        </svg>
                    </div>
                    <span>Email Verification</span>
                </div>
            </div>
        </div>
        
        <div class="cta">
            <a href="/docs" class="button">
                View API Documentation
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                </svg>
            </a>
        </div>
        
        <footer class="footer">
            <p>
                Built with FastAPI • 
                <a href="/docs">Swagger UI</a> • 
                <a href="/redoc">ReDoc</a>
            </p>
            <p style="margin-top: 0.5rem;">© 2025 Kliniq Healthcare. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
"""
    return html_content