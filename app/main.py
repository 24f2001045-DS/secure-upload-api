from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import csv
import io
import os

app = FastAPI()

# Proper CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FORCE header on every response (including errors)
@app.middleware("http")
async def force_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

MAX_FILE_SIZE = 50 * 1024
ALLOWED_EXTENSIONS = {".csv", ".json", ".txt"}
UPLOAD_TOKEN = "jps5cpm0v38wkqe0"
EXPECTED_EMAIL = "24f2001045@ds.study.iitm.ac.in"

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def secure_upload(
    file: UploadFile = File(...),
    x_upload_token_5067: str = Header(None, alias="X-Upload-Token-5067")
):
    if x_upload_token_5067 != UPLOAD_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    filename = file.filename
    _, ext = os.path.splitext(filename)

    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    if ext.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Only CSV supported for analysis")

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