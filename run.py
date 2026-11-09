#!/usr/bin/env python3
"""
Screenly - Autonomous Role-Adaptive Technical Screening System
Application Launcher
"""

import sys
import os
import webbrowser
import uvicorn
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.database import init_db

def print_banner():
    banner = f"""
========================================================================
   ____                                   __         
  / __/___________ ___ ___  ___  / /_ __  
 _\\ \\/ __/ __/ -_) -_) _ \\/ / / / / // /  
/___/\\__/_/  \\__/\\__/_//_/_/_/ /_/\\_, /   
                                 /___/    
========================================================================
 :: System :: Screenly - AI Technical Candidate Screening & RAG Engine
 :: Role Support :: AI/ML Engineer | Backend Engineer | Data Scientist
 :: Grounding :: Tom Mitchell ML, Burkov 100-Page ML, System Design
 :: URL :: http://localhost:{settings.PORT}
 :: Mode :: LLM_PROVIDER={settings.LLM_PROVIDER}
========================================================================
"""
    print(banner)


def main():
    print_banner()
    print("[1/2] Initializing database schema...")
    init_db()

    print(f"[2/2] Starting Screenly server on http://localhost:{settings.PORT} ...")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
