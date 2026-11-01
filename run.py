import os
import sys
import uvicorn
from config import WEB_HOST, WEB_PORT

if __name__ == "__main__":
    # Ensure UTF-8 output on Windows
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("🚀 ViralReel AI - Autonomous TikTok to Instagram Reels Agent")
    print("=" * 60)
    # Use PORT from environment if deploying to cloud (Render, Koyeb, Railway, etc.)
    port = int(os.getenv("PORT", WEB_PORT))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🌐 Server listening on: http://{host}:{port}")
    print(f"📂 Workspace: {os.getcwd()}")
    print("⚡ Starting Server and Scheduler...")
    print("=" * 60)

    uvicorn.run("app:app", host=host, port=port, reload=False)
