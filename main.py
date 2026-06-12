from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from workflow import Workflow
import json
import os 
import time
import asyncio  # for async sleep


workflow = Workflow()

app = FastAPI(title="Minhaj – AI Curriculum Builder")

@app.middleware("http")
async def log_latency(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    latency = time.perf_counter() - start_time
    
    # ONLY log for /generate POST requests
    if request.url.path == "/generate" and request.method == "POST":
        print(f"[LATENCY] POST /generate | {latency:.4f}s")
        response.headers["X-Process-Time"] = f"{latency:.4f}"  # Optional: expose to clients
    
    return response

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Home page
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Receive JSON from form and generate course
@app.post("/generate")
async def generate(data: dict):
    start_time = time.perf_counter()
    try:
        # Log received data
        print("Received JSON data:")
        print(json.dumps(data, indent=2))
        
        
        # Call the course generation function
        result = workflow.run(data)
        
        
        latency = time.time() - start_time  # Total time in seconds

        zip_path = "course/course.zip"

        if not os.path.exists(zip_path):
            return JSONResponse(
                {"message": "Zip file not found"},
                status_code=500
            )

        return FileResponse(
            path=zip_path,
            filename="course.zip",
            media_type="application/zip"
        )
        
    except Exception as e:
        # Handle any errors
        print("Error during course generation:", str(e))
        return JSONResponse({"message": "Failed to generate course", "error": str(e)}, status_code=500)
    finally:
        latency = time.perf_counter() - start_time
        print(f"[LATENCY] POST /generate (workflow only) | {latency:.4f}s")
