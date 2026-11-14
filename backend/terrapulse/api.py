"""FastAPI service.  Run:  uv run uvicorn terrapulse.api:app --reload"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, analysis as an
from .catalog import END_YEAR, REGIONS, SOURCE, START_YEAR, VARIABLES
from .power import load_provenance

app = FastAPI(
    title="TerraPulse API",
    version=__version__,
    description="Trend slope, uncertainty and significance for NASA MERRA-2 regional series.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _check(region: str, variable: str) -> None:
    if region not in REGIONS:
        raise HTTPException(404, f"unknown region '{region}'")
    if variable not in VARIABLES:
        raise HTTPException(404, f"unknown variable '{variable}'")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/catalog")
def catalog() -> dict:
    return {
        "period": [START_YEAR, END_YEAR],
        "min_window_years": an.MIN_WINDOW_YEARS,
        "regions": [{"id": k, **v} for k, v in REGIONS.items()],
        "variables": [{"id": k, **v} for k, v in VARIABLES.items()],
        "source": SOURCE,
    }


@app.get("/api/analysis/{region}/{variable}")
def get_analysis(region: str, variable: str) -> dict:
    _check(region, variable)
    return an.analysis(region, variable)


@app.get("/api/trend/{region}/{variable}")
def get_trend(region: str, variable: str, start: int = START_YEAR, end: int = END_YEAR) -> dict:
    _check(region, variable)
    try:
        return an.custom_trend(region, variable, start, end)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/overview/{variable}")
def get_overview(variable: str) -> dict:
    if variable not in VARIABLES:
        raise HTTPException(404, f"unknown variable '{variable}'")
    return an.overview(variable)


@app.get("/api/provenance")
def provenance() -> dict:
    return load_provenance()
