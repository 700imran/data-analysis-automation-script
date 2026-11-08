from __future__ import annotations
import json, os, uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from .engine import analyze_frames
from .registry import MODULES, PROFILES
from .io import read_uploaded_file, slug

load_dotenv()

app = FastAPI(
    title="MarginPulse Intelligence Engine API",
    description="Configurable business intelligence for distributors, retailers and selected service businesses.",
    version="0.1.1",
)
STORAGE_ROOT = Path(os.getenv("MARGINPULSE_STORAGE", "./storage")).resolve()
API_KEY = os.getenv("MARGINPULSE_API_KEY", "local-dev-key-change-before-deployment")


def _auth(x_api_key: str | None) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Valid X-API-Key header required.")

@app.get("/health")
def health():
    return {"status": "ok", "service": "MarginPulse Intelligence Engine", "version": "0.1.1"}

@app.get("/api/v1/modules")
def list_modules(x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    return {"profiles": PROFILES, "modules": MODULES}

@app.post("/api/v1/analyze")
async def analyze(
    files: list[UploadFile] = File(..., description="CSV or XLSX files. An XLSX workbook may contain multiple recognised sheets."),
    config: str = Form(default="{}", description="JSON client config: client_id, profile, currency, as_of_date, dataset_map, column_mappings, thresholds."),
    x_api_key: str | None = Header(default=None),
):
    _auth(x_api_key)
    try:
        if len(files) > 20:
            raise ValueError("Upload no more than 20 files per analysis request")
        cfg = json.loads(config or "{}")
        if not isinstance(cfg, dict):
            raise ValueError("config must be a JSON object")
        client_id = slug(cfg.get("client_id", ""))
        if not client_id or len(client_id) > 64:
            raise ValueError("config.client_id is required and must be 1–64 safe characters")
        frames = []
        total_size = 0
        for upload in files:
            content = await upload.read()
            total_size += len(content)
            if len(content) > 40 * 1024 * 1024:
                raise ValueError(f"{upload.filename} exceeds the 40 MB per-file limit")
            if total_size > 80 * 1024 * 1024:
                raise ValueError("Total upload size exceeds the 80 MB request limit")
            if not upload.filename:
                continue
            frames.append((upload.filename, read_uploaded_file(upload.filename, content)))
        if not frames:
            raise ValueError("No usable file uploads received")
        result = analyze_frames(frames, cfg, STORAGE_ROOT, analysis_id=uuid.uuid4().hex[:12])
        return {
            "summary": result["summary"],
            "module_availability": result["module_availability"],
            "module_results": result["module_results"],
            "insights": result["insights"],
            "data_quality": result["data_quality"],
            "ignored_sheets": result["ignored_sheets"],
            "download_url": f"/api/v1/analyses/{result['summary']['analysis_id']}/download?client_id={client_id}",
        }
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Avoid returning raw file contents or stack traces to callers.
        raise HTTPException(status_code=500, detail=f"Analysis failed safely: {type(exc).__name__}: {exc}") from exc

@app.get("/api/v1/analyses/{analysis_id}")
def get_analysis(analysis_id: str, client_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    safe_client = slug(client_id)
    if not safe_client or not analysis_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid analysis_id or client_id")
    path = STORAGE_ROOT / safe_client / analysis_id / "analysis.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    return json.loads(path.read_text(encoding="utf-8"))

@app.get("/api/v1/analyses/{analysis_id}/download")
def download_analysis(analysis_id: str, client_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    safe_client = slug(client_id)
    if not safe_client or not analysis_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid analysis_id or client_id")
    path = STORAGE_ROOT / safe_client / f"{analysis_id}.zip"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis package not found")
    return FileResponse(path, filename=f"MarginPulse_{safe_client}_{analysis_id}.zip", media_type="application/zip")
