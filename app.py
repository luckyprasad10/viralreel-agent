import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import (
    BASE_DIR, DATA_DIR, DOWNLOADS_DIR, PROCESSED_DIR,
    WEB_HOST, WEB_PORT, AUTONOMOUS_MODE, MAX_DAILY_POSTS,
    TARGET_REGIONS, SESSION_MAX_AGE_SECONDS
)
from database import db
from modules.scheduler import pipeline
from modules.trend_hunter import TrendHunter
from modules.downloader import downloader
from modules.video_processor import processor
from modules.ai_captioner import captioner
from modules.instagram_poster import poster
from modules.analytics_tracker import tracker
from modules.auth import (
    create_session_token, verify_session_token,
    verify_credentials, COOKIE_NAME
)

app = FastAPI(title="ViralReel AI - Autonomous TikTok to Instagram Reels Agent")

# Mount static and templates
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount processed and downloads for direct video preview in dashboard
app.mount("/media/processed", StaticFiles(directory=str(PROCESSED_DIR)), name="processed_media")
app.mount("/media/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="downloads_media")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Security Authentication Middleware ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Public whitelist: Static assets, login/logout, health check
    if (
        path.startswith("/static")
        or path in ("/login", "/logout", "/health", "/favicon.ico")
    ):
        return await call_next(request)

    # Check for valid session cookie
    token = request.cookies.get(COOKIE_NAME)
    if not verify_session_token(token):
        if path.startswith("/api/"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized. Please login to access ViralReel AI."}
            )
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)

# Startup event to launch background scheduler
@app.on_event("startup")
def on_startup():
    pipeline.start()
    db.add_log("INFO", "Server", "Web Control Dashboard initialized with Protected Auth.")

@app.on_event("shutdown")
def on_shutdown():
    pipeline.stop()

# --- Health Check (For Cloud Uptime Monitoring & Render) ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ViralReel AI", "security": "authenticated"}

# --- Auth Routes ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in, redirect straight to dashboard
    token = request.cookies.get(COOKIE_NAME)
    if verify_session_token(token):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None, "username": ""})

@app.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: Optional[str] = Form(None)
):
    if verify_credentials(username, password):
        token = create_session_token(username)
        response = RedirectResponse(url="/", status_code=303)
        max_age = SESSION_MAX_AGE_SECONDS if remember else None
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=max_age,
            httponly=True,
            samesite="lax",
            secure=False  # Set False so it works on both HTTP localhost and HTTPS cloud
        )
        db.add_log("SUCCESS", "Auth", f"User '{username}' authenticated successfully.")
        return response
    else:
        db.add_log("WARN", "Auth", f"Failed authentication attempt for username: '{username}'")
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or security password. Access denied.", "username": username},
            status_code=401
        )

@app.get("/logout")
async def handle_logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=COOKIE_NAME)
    return response

# --- Protected Page Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    stats = db.get_dashboard_stats()
    posts_today = pipeline.count_posts_today()
    max_daily = int(db.get_setting("max_daily_posts", MAX_DAILY_POSTS))
    is_autonomous = pipeline.is_autonomous_active()
    
    context = {
        "stats": stats,
        "posts_today": posts_today,
        "max_daily": max_daily,
        "is_autonomous": is_autonomous,
        "insta_connected": poster.is_authenticated or poster.load_session()
    }
    return templates.TemplateResponse(request, "index.html", context)

# --- API Endpoints ---

@app.get("/api/stats")
async def get_stats():
    stats = db.get_dashboard_stats()
    stats["posts_today"] = pipeline.count_posts_today()
    stats["max_daily"] = int(db.get_setting("max_daily_posts", MAX_DAILY_POSTS))
    stats["is_autonomous"] = pipeline.is_autonomous_active()
    stats["insta_connected"] = poster.is_authenticated or poster.load_session()
    return stats

@app.get("/api/queue")
async def get_queue(status: Optional[str] = None, limit: int = 40):
    videos = db.get_queue(status=status, limit=limit)
    return {"videos": videos}

@app.get("/api/logs")
async def get_logs(limit: int = 50):
    logs = db.get_logs(limit=limit)
    return {"logs": logs}

# --- Actions ---

@app.post("/api/actions/discover")
async def trigger_discovery(background_tasks: BackgroundTasks):
    """Trigger background trend hunting."""
    background_tasks.add_task(pipeline.run_discovery_and_preparation)
    return {"status": "started", "message": "Global trend hunter launched in background."}

@app.post("/api/actions/post-next")
async def trigger_post_next(background_tasks: BackgroundTasks):
    """Manually post the next ready video."""
    background_tasks.add_task(pipeline.post_next_ready_video)
    return {"status": "started", "message": "Publishing highest-scoring ready Reel."}

@app.post("/api/actions/approve-post/{video_id}")
async def approve_and_post(video_id: int, background_tasks: BackgroundTasks):
    """One-click post a specific video."""
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    def run_post():
        if video.get("status") != "ready":
            pipeline.prepare_video_pipeline(video_id)
        poster.post_reel(video_id)

    background_tasks.add_task(run_post)
    return {"status": "started", "message": f"Video {video_id} queued for immediate posting."}

@app.post("/api/actions/prepare/{video_id}")
async def prepare_video(video_id: int, background_tasks: BackgroundTasks):
    """Download and process video without posting."""
    background_tasks.add_task(pipeline.prepare_video_pipeline, video_id)
    return {"status": "started", "message": f"Processing video {video_id}..."}

@app.post("/api/actions/toggle-autonomous")
async def toggle_autonomous():
    current = pipeline.is_autonomous_active()
    new_state = not current
    db.set_setting("autonomous_mode", new_state)
    db.add_log("INFO", "Settings", f"Autonomous mode set to {'ON' if new_state else 'OFF'}")
    return {"autonomous_mode": new_state}

@app.post("/api/actions/sync-analytics")
async def sync_analytics(background_tasks: BackgroundTasks):
    background_tasks.add_task(tracker.sync_post_analytics)
    return {"status": "started", "message": "Instagram metrics sync initiated."}

# --- Instagram Account Connection & Profile ---

from modules.instagram_manager import insta_manager
from modules.ai_agent import ai_agent

class InstaLoginRequest(BaseModel):
    username: str
    password: str
    verification_code: Optional[str] = None

@app.post("/api/instagram/login")
async def insta_login(req: InstaLoginRequest):
    result = poster.login(
        username=req.username,
        password=req.password,
        verification_code=req.verification_code
    )
    return result

@app.get("/api/instagram/status")
async def insta_status():
    is_active = poster.is_authenticated or poster.load_session()
    return {
        "connected": is_active,
        "username": os.getenv("INSTA_USERNAME", "")
    }

@app.get("/api/instagram/profile")
async def get_insta_profile():
    return insta_manager.get_profile_details()

@app.post("/api/instagram/engage")
async def trigger_insta_engagement(background_tasks: BackgroundTasks):
    """Trigger AI comment engagement & auto-replies."""
    background_tasks.add_task(insta_manager.engage_audience_and_reply_comments)
    return {"status": "started", "message": "Audience comment auto-reply engine running in background."}

# --- AI Agent Endpoints ---

class AgentChatRequest(BaseModel):
    message: str

@app.post("/api/agent/chat")
async def agent_chat(req: AgentChatRequest):
    reply = ai_agent.process_chat(req.message)
    return {"reply": reply}

@app.get("/api/agent/chat/history")
async def agent_chat_history(limit: int = 30):
    history = db.get_chat_history(limit=limit)
    return {"history": history}

@app.get("/api/agent/decisions")
async def agent_decisions(limit: int = 20):
    decisions = db.get_agent_decisions(limit=limit)
    return {"decisions": decisions}

@app.post("/api/agent/cycle")
async def trigger_agent_cycle(background_tasks: BackgroundTasks):
    background_tasks.add_task(ai_agent.run_autonomous_cycle)
    return {"status": "started", "message": "AI Director autonomous cycle launched."}

# --- Settings ---

class SettingsRequest(BaseModel):
    max_daily_posts: int
    target_regions: List[str]

@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    db.set_setting("max_daily_posts", req.max_daily_posts)
    db.set_setting("target_regions", req.target_regions)
    db.add_log("INFO", "Settings", "Settings updated successfully.")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=WEB_HOST, port=WEB_PORT, reload=False)
