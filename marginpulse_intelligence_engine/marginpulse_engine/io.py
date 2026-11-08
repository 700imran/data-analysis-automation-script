from __future__ import annotations
import io, re, zipfile, json
from pathlib import Path
from typing import Any
import pandas as pd
from .registry import DATASET_ALIASES

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}

def slug(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value

def detect_dataset(name: str) -> str | None:
    key = slug(Path(name).stem)
    # Exact aliases first. For compound names, match whole underscore-delimited
    # tokens only; short aliases such as AR/AP must never match arbitrary words.
    pairs = []
    tokens = key.split("_") if key else []
    for dataset, aliases in DATASET_ALIASES.items():
        for alias in aliases:
            a = slug(alias)
            if key == a:
                return dataset
            if not a or len(a) < 4:
                continue
            at = a.split("_")
            for i in range(0, max(0, len(tokens) - len(at) + 1)):
                if tokens[i:i + len(at)] == at:
                    pairs.append((len(a), dataset))
                    break
    return max(pairs)[1] if pairs else None

def read_uploaded_file(filename: str, content: bytes) -> list[tuple[str, pd.DataFrame]]:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type for {filename}. Use CSV or XLSX.")
    if ext == ".csv":
        try:
            df = pd.read_csv(io.BytesIO(content))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
        return [(Path(filename).stem, df)]
    workbook = pd.ExcelFile(io.BytesIO(content))
    frames = []
    for sheet in workbook.sheet_names:
        df = pd.read_excel(workbook, sheet_name=sheet)
        if not df.empty and not df.dropna(how="all").empty:
            frames.append((sheet, df))
    return frames

def load_local_file(path: str | Path) -> list[tuple[str, pd.DataFrame]]:
    p = Path(path)
    return read_uploaded_file(p.name, p.read_bytes())

def build_output_zip(output_dir: Path, zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in output_dir.rglob("*"):
            if p.is_file() and p != zip_path:
                zf.write(p, p.relative_to(output_dir))
    return zip_path

def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
