from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from parser import process_resume_file  # Import the wrapper function
import os, json, shutil, tempfile
from typing import Optional

app = FastAPI(title="Resume Parser API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_JSON = "parsed_resumes_structured.json"

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...), target_job: Optional[str] = "Data Scientist"):
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Use temporary file for better security
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        # Use the wrapper function for simpler processing
        result = process_resume_file(temp_path, target_job)

        # Clean up temporary file
        os.unlink(temp_path)

        # Persist data (optional)
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", OUTPUT_JSON)
        with open(output_path, "w") as f:
            json.dump(result["data"], f, indent=2)

        return JSONResponse(content={
            "success": True,
            "message": f"Processed {result['pages_processed']} pages and found {result['resumes_found']} resumes",
            "data": result["data"]
        })
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/candidates")
def get_candidates():
    """Get all parsed candidates"""
    output_path = os.path.join("data", OUTPUT_JSON)
    if not os.path.exists(output_path):
        return JSONResponse(content={"candidates": {}, "count": 0})
    
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
        return JSONResponse(content={"candidates": data, "count": len(data)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading candidates: {str(e)}")

@app.get("/")
def root():
    """API health check"""
    return {"message": "Resume Parser API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api": "Resume Parser API",
        "version": "1.0.0"
    }