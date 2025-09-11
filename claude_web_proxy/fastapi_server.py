"""
FastAPI Server for Claude Web Proxy
REST API server that bridges between browser automation and clients
"""
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import uvicorn

from .claude_browser import ClaudeBrowser

# Configure logging
logger = structlog.get_logger()

# Global browser instance
claude_browser: Optional[ClaudeBrowser] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="Message to send to Claude")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    new_conversation: bool = Field(False, description="Start a new conversation")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Claude's response")
    status: str = Field(..., description="Response status")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.now)

class StatusResponse(BaseModel):
    browser_running: bool
    logged_in: bool
    last_activity: Optional[datetime]
    uptime_seconds: float

class SetupRequest(BaseModel):
    headless: bool = Field(False, description="Run browser in headless mode")
    timeout: int = Field(300, description="Login timeout in seconds")

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser lifecycle"""
    global claude_browser
    
    logger.info("Starting FastAPI server with Claude Web Proxy")
    
    # Startup
    try:
        claude_browser = ClaudeBrowser(headless=False)  # Start visible for initial setup
        await claude_browser.start_browser()
        logger.info("Claude browser initialized")
    except Exception as e:
        logger.error("Failed to initialize browser", error=str(e))
        claude_browser = None
    
    yield
    
    # Shutdown
    if claude_browser:
        try:
            await claude_browser.close()
            logger.info("Claude browser closed")
        except Exception as e:
            logger.error("Error closing browser", error=str(e))

# Create FastAPI app
app = FastAPI(
    title="Claude Web Proxy",
    description="REST API bridge for Claude Web (claude.ai)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track server start time
SERVER_START_TIME = datetime.now()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Claude Web Proxy API", "status": "running", "version": "1.0.0"}

@app.get("/claude/status", response_model=StatusResponse)
async def get_status():
    """Get current status of Claude browser"""
    global claude_browser
    
    if not claude_browser:
        return StatusResponse(
            browser_running=False,
            logged_in=False,
            last_activity=None,
            uptime_seconds=0
        )
    
    try:
        # Check if browser context is still running (correct method for BrowserContext)
        def check_browser_context_status() -> bool:
            try:
                if not claude_browser.browser:  # browser is actually a BrowserContext
                    return False
                
                # BrowserContext status via pages (correct method)
                pages = claude_browser.browser.pages
                if len(pages) == 0:
                    return False
                
                # Check if first page is not closed
                first_page = pages[0]
                return not first_page.is_closed()
                
            except Exception as e:
                logger.debug("Browser context status check failed", error=str(e))
                return False
        
        browser_running = check_browser_context_status()
        
        # Quick login status check (don't navigate away from current page)
        logged_in = claude_browser.is_logged_in
        
        uptime = (datetime.now() - SERVER_START_TIME).total_seconds()
        
        return StatusResponse(
            browser_running=browser_running,
            logged_in=logged_in,
            last_activity=datetime.now(),
            uptime_seconds=uptime
        )
    
    except Exception as e:
        logger.error("Error checking status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")

@app.post("/claude/setup")
async def setup_claude(request: SetupRequest):
    """Setup Claude browser (interactive login)"""
    global claude_browser
    
    try:
        # Close existing browser if any
        if claude_browser:
            await claude_browser.close()
        
        # Create new browser instance
        claude_browser = ClaudeBrowser(headless=request.headless)
        await claude_browser.start_browser()
        
        # Check login status
        logged_in = await claude_browser.check_login_status()
        
        if not logged_in:
            logger.info("User needs to log in, waiting for interactive login", timeout=request.timeout)
            
            if request.headless:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Cannot perform interactive login in headless mode"}
                )
            
            # Wait for user to log in
            logged_in = await claude_browser.wait_for_login(timeout=request.timeout)
        
        if logged_in:
            return {
                "status": "success",
                "message": "Claude browser setup complete",
                "logged_in": True
            }
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Login timeout or failed", "logged_in": False}
            )
    
    except Exception as e:
        logger.error("Setup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.post("/claude/chat", response_model=ChatResponse)
async def chat_with_claude(request: ChatRequest):
    """Send message to Claude and get response"""
    global claude_browser
    
    if not claude_browser:
        raise HTTPException(status_code=500, detail="Browser not initialized. Call /claude/setup first.")
    
    if not claude_browser.is_logged_in:
        # Try to check login status
        logged_in = await claude_browser.check_login_status()
        if not logged_in:
            raise HTTPException(status_code=401, detail="Not logged in to Claude. Call /claude/setup first.")
    
    try:
        # Start new conversation if requested
        if request.new_conversation:
            await claude_browser.start_new_conversation()
        
        # Send message and get response
        response = await claude_browser.send_message(request.message)
        
        return ChatResponse(
            response=response,
            status="success",
            conversation_id=request.conversation_id,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error("Chat failed", error=str(e), message=request.message)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/claude/new-conversation")
async def new_conversation():
    """Start a new conversation with Claude"""
    global claude_browser
    
    if not claude_browser or not claude_browser.is_logged_in:
        raise HTTPException(status_code=500, detail="Browser not ready. Call /claude/setup first.")
    
    try:
        success = await claude_browser.start_new_conversation()
        if success:
            return {"status": "success", "message": "New conversation started"}
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to start new conversation"}
            )
    
    except Exception as e:
        logger.error("Failed to start new conversation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start new conversation: {str(e)}")

@app.post("/claude/restart")
async def restart_browser():
    """Restart the Claude browser"""
    global claude_browser
    
    try:
        # Close existing browser
        if claude_browser:
            await claude_browser.close()
        
        # Create and start new browser
        claude_browser = ClaudeBrowser(headless=False)
        await claude_browser.start_browser()
        
        return {"status": "success", "message": "Browser restarted"}
    
    except Exception as e:
        logger.error("Failed to restart browser", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to restart browser: {str(e)}")

@app.delete("/claude/shutdown")
async def shutdown_browser():
    """Shutdown the Claude browser"""
    global claude_browser
    
    if claude_browser:
        try:
            await claude_browser.close()
            claude_browser = None
            return {"status": "success", "message": "Browser shutdown"}
        except Exception as e:
            logger.error("Error shutting down browser", error=str(e))
            raise HTTPException(status_code=500, detail=f"Error shutting down browser: {str(e)}")
    else:
        return {"status": "success", "message": "Browser already shutdown"}

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"}
    )

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "fastapi_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server(port=8000, reload=True)