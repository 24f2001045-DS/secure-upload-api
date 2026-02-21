from fastapi import Request

@app.post("/upload")
async def secure_upload(
    request: Request,
    file: UploadFile = File(...),
    x_upload_token_5067: str = Header(None, alias="X-Upload-Token-5067")
):
    # Allow preflight OPTIONS automatically
    if request.method == "OPTIONS":
        return {}

    # Authentication check
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