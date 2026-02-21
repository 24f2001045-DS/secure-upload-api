from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import csv
import io
import os

# -------------------------------------------------
# Create FastAPI app FIRST (must be before routes)
# -------------------------------------------------
app = FastAPI()

# -------------------------------------------------
# CORS Configuration (Required for evaluator)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow any origin
    allow_credentials=True,      # Must be False when using "*"
    allow_methods=["*"],          # Allow all methods (POST, OPTIONS, etc.)
    allow_headers=["*"],          # Allow all headers
)

# -------------------------------------------------
# Constants
# -------------------------------------------------
MAX_FILE_SIZE = 50 * 1024  # 50 KB
ALLOWED_EXTENSIONS = {".csv", ".json", ".txt"}
UPLOAD_TOKEN = "jps5cpm0v38wkqe0"
EXPECTED_EMAIL = "24f2001045@ds.study.iitm.ac.in"

# -------------------------------------------------
# Health Check (Render requirement)
# -------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "ok"}

# -------------------------------------------------
# Secure Upload Endpoint
# -------------------------------------------------
@app.post("/upload")
async def secure_upload(
    file: UploadFile = File(...),
    x_upload_token_5067: str = Header(None, alias="X-Upload-Token-5067")
):
    # 1️⃣ Authentication
    if x_upload_token_5067 != UPLOAD_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2️⃣ File Extension Validation
    filename = file.filename
    _, ext = os.path.splitext(filename)

    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # 3️⃣ File Size Validation
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Only CSV supported for analysis
    if ext.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Only CSV supported for analysis")

    # 4️⃣ CSV Processing
    try:
        decoded = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded))
        rows = list(csv_reader)

        if not rows:
            raise HTTPException(status_code=400, detail="Empty CSV file")

        required_columns = {"id", "name", "value", "category"}
        if not required_columns.issubset(set(csv_reader.fieldnames)):
            raise HTTPException(status_code=400, detail="Missing required columns")

        total_value = 0.0
        category_counts = {}

        for row in rows:
            total_value += float(row["value"])
            category = row["category"]
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "email": EXPECTED_EMAIL,
            "filename": filename,
            "rows": len(rows),
            "columns": csv_reader.fieldnames,
            "totalValue": round(total_value, 2),
            "categoryCounts": category_counts
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid numeric value in CSV")

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV format")